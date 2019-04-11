#!/usr/bin/env python3

import os
import time
import zipfile
import subprocess
import sys

from ctypes import c_int, c_bool, c_void_p, c_long, c_short, c_ulong, c_char, c_ushort, c_ubyte
from ctypes import windll, byref, Structure, sizeof, POINTER


DEPLOY_DIR = os.path.join('C:\\', 'maltest')
SAMPLE_NAME = 'a.exe'
MALWARE_PATH = os.path.join(DEPLOY_DIR, SAMPLE_NAME)
WAIT_TIME = 30
ZIP_FN = os.path.join(DEPLOY_DIR, 'extraction.zip')
EXTRACTION_DIR = os.path.join(DEPLOY_DIR, 'dumps')
LOG_FILE = 'clientapp.log'
CLIENT_LOG_FN = os.path.join(EXTRACTION_DIR, LOG_FILE)

os.makedirs(EXTRACTION_DIR)
logger = open(CLIENT_LOG_FN, 'w')

sys.stdout = sys.stderr = logger


### START - Windows constants

HANDLE = c_void_p
DWORD = c_ulong
WORD = c_ushort
LPTSTR = POINTER(c_char)
LPBYTE = POINTER(c_ubyte)

### END - Windows constants


### START - Windows structures

class STARTUPINFO(Structure):
    _fields_ = [
        ('cb',              DWORD),
        ('lpReserved',      LPTSTR),
        ('lpDesktop',       LPTSTR),
        ('pTitle',          LPTSTR),
        ('dwX',             DWORD),
        ('dwY',             DWORD),
        ('dwXSize',         DWORD),
        ('dwYSize',         DWORD),
        ('dwXCountChars',   DWORD),
        ('dwYCountChars',   DWORD),
        ('dwFillAttribute', DWORD),
        ('dwFlags',         DWORD),
        ('wShowWindow',     WORD),
        ('cbReserved2',     WORD),
        ('lpReserved2',     LPBYTE),
        ('hStdInput',       HANDLE),
        ('hStdOutput',      HANDLE),
        ('hStdError',       HANDLE)
    ]



class PROCESS_INFORMATION(Structure):
    _fields_ = [
        ('hProcess',    HANDLE),
        ('hThread',     HANDLE),
        ('dwProcessId', DWORD),
        ('dwThreadId',  DWORD)
    ]

# END - Windows structures


# START - Windows function headers

CreateProcess = windll.kernel32.CreateProcessW
GetLastError = windll.kernel32.GetLastError
ResumeThread = windll.kernel32.ResumeThread

# END - Windows function headers

# start monitoring apps

#start a suspended hollows_hunter.exe and after WAIT_TIME resume it
hh_pi = PROCESS_INFORMATION()
hh_si = STARTUPINFO()
hh_si.cb = sizeof(hh_si)
# protect needed imports for hollows_hunter
#TODO: rewrite this crap
dll_lock = open('%s\\tools\\pe-sieve.dll' % (DEPLOY_DIR,))
hollows_hunter_path = '%s\\tools\\hollows_hunter.exe /kill' % (DEPLOY_DIR,)
ret = CreateProcess(None, hollows_hunter_path, None, None, None, 0x4, None, EXTRACTION_DIR, byref(hh_si),
        byref(hh_pi))

pi = PROCESS_INFORMATION()
si = STARTUPINFO()
si.cb = sizeof(si)

logger.write('[#] Executing [%s]\n' % (MALWARE_PATH,))
ret = CreateProcess(MALWARE_PATH, None, None, None, None, 0x0, None, None, byref(si), byref(pi))

if ret:
    logger.write('CreateProcess success! ID: %d\n' % (pi.dwProcessId,))
else:
    err = GetLastError()
    logger.write('Something went wrong %x!\n' % (err,))
    sys.exit(err)

time.sleep(WAIT_TIME)
ResumeThread(hh_pi.hThread)
time.sleep(WAIT_TIME)

# logger.write('[#] Dumping PID [%d] using procdump.exe\n' % (pi.dwProcessId,))
# subprocess.Popen(['%s\\tools\\procdump.exe' % (DEPLOY_DIR,), '-t', '-ma', str(pi.dwProcessId), '/AcceptEula'],
#         cwd=EXTRACTION_DIR)

# in case hollows_hunter doesn't kill the process
subprocess.run(['taskkill', '/F', '/PID', str(pi.dwProcessId)])

logger.close()
dll_lock.close()

with zipfile.ZipFile(ZIP_FN, 'a') as zip_file:
    for root, _, files in os.walk(EXTRACTION_DIR):
        for f in files:
            zip_file.write(os.path.join(root, f))
