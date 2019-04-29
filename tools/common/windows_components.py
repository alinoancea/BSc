from ctypes import c_int, c_bool, c_void_p, c_long, c_short, c_ulong, c_char, c_ushort, c_ubyte, c_long
from ctypes import windll, byref, Structure, sizeof, POINTER


### Windows constants

HANDLE = c_void_p
DWORD = c_ulong
WORD = c_ushort
LPTSTR = POINTER(c_char)
LPBYTE = POINTER(c_ubyte)
LONG = c_long
CHAR = c_char
if sizeof(c_void_p) == 8:
    from ctypes import c_longlong
    ULONG_PTR = c_longlong
else:
    ULONG_PTR = c_long


CREATE_NEW_CONSOLE = 0x00000010
CREATE_SUSPENDED = 0x00000004

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002

MAX_PATH = 0x00000104
INVALID_HANDLE_VALUE = -1
ERROR_NO_MORE_FILES = 0x12



### Windows structures

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



class PROCESSENTRY32(Structure):
    _fields_ = [
        ('dwSize',              DWORD),
        ('cntUsage',            DWORD),
        ('th32ProcessID',       DWORD),
        ('th32DefaultHeapID',   ULONG_PTR),
        ('th32ModuleID',        DWORD),
        ('cntThreads',          DWORD),
        ('th32ParentProcessID', DWORD),
        ('pcPriClassBase',      LONG),
        ('dwFlags',             DWORD),
        ('szExeFile',           CHAR * MAX_PATH)
    ]



class THREADENTRY32(Structure):
    _fields_ = [
        ('dwSize',              DWORD),
        ('cntUsage',            DWORD),
        ('th32ThreadID',        DWORD),
        ('th32OwnerProcessID',  DWORD),
        ('tpBasePri',           LONG),
        ('tpDeltaPri',          LONG),
        ('dwFlags',             DWORD)
    ]



### Windows function headers

CreateProcess = windll.kernel32.CreateProcessW
GetLastError = windll.kernel32.GetLastError
ResumeThread = windll.kernel32.ResumeThread
SuspendThread = windll.kernel32.SuspendThread
CreateToolhelp32Snapshot = windll.kernel32.CreateToolhelp32Snapshot
Process32First = windll.kernel32.Process32First
Process32Next = windll.kernel32.Process32Next
CloseHandle = windll.kernel32.CloseHandle
Thread32First = windll.kernel32.Thread32First
Thread32Next = windll.kernel32.Thread32Next
OpenThread = windll.kernel32.OpenThread
TerminateProcess = windll.kernel32.TerminateProcess