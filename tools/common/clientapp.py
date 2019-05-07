#!/usr/bin/env python3

import os
import time
import zipfile
import subprocess
import sys

from registrytool import RegistryWatcher
from processtool import ProcessCreator, ProcessWatcher
from windows_components import CREATE_SUSPENDED
from folderstool import FolderWatcher


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


# start monitoring apps

#start a suspended hollows_hunter.exe and after WAIT_TIME resume it
# protect needed imports for hollows_hunter
#TODO: rewrite this crap
dll_lock = open('%s\\tools\\pe-sieve.dll' % (DEPLOY_DIR,))
hollows_hunter_path = '%s\\tools\\hollows_hunter.exe' % (DEPLOY_DIR,)

hollows_proc = ProcessCreator()
response = hollows_proc.create(hollows_hunter_path, creation_flags=CREATE_SUSPENDED, working_dir=EXTRACTION_DIR)

if response[0]:
    print('[!] ERROR: Hollows hunter process creation. Code: %d' % (response[1],))
    sys.exit()

registry_watcher = RegistryWatcher(output=open(os.path.join(EXTRACTION_DIR, 'registry_changes.txt'), 'w'))
print('[#] Snapshotting registry...', end='')
t0 = time.time()
registry_watcher.snap()
print('%s sec.' % (time.time() - t0))

process_watcher = ProcessWatcher()
print('[#] Snapshotting processes...', end='')
t0 = time.time()
process_watcher.snap()
print('%s sec.' % (time.time() - t0))

watch_folder = FolderWatcher(output=open(os.path.join(EXTRACTION_DIR, 'folder_changes.txt'), 'w'))
watch_folder.add_to_watch()
watch_folder.start()

print('[#] Executing [%s]...' % (MALWARE_PATH,))
malware_proc = ProcessCreator()
response = malware_proc.create(MALWARE_PATH)

if response[0]:
    print('[!] ERROR: Malware process creation. Code: %s' % (response[1],))
    sys.exit()

print('[#] Malware process successfully created. PID: %d' % (malware_proc.pid,))

time.sleep(WAIT_TIME)
hollows_proc.resume()

process_watcher.suspend_differences()
watch_folder.close()
registry_watcher.show_diff()

malware_proc.terminate()

logger.close()
dll_lock.close()

with zipfile.ZipFile(ZIP_FN, 'a') as zip_file:
    for root, _, files in os.walk(EXTRACTION_DIR):
        for f in files:
            zip_file.write(os.path.join(root, f))
