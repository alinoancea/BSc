#!/usr/bin/env python3

import os
import time
import zipfile
import subprocess
import sys
import argparse

from registrytool import RegistryWatcher
from processtool import ProcessCreator, ProcessWatcher
from windows_components import CREATE_SUSPENDED
from folderstool import FolderWatcher



class LogFile:


    def __init__(self, filename):
        self.filename = filename
        open(self.filename, 'w')
        self.handle = open(self.filename)


    def write(self, s):
        open(self.filename, 'a').write(s)


    def flush(self):
        pass


    def close(self):
        self.handle.close()



def execute_experiment(argp):
    MALWARE_PATH = os.path.join(argp.deploy_dir, argp.sample_name)
    ZIP_FN = os.path.join(argp.deploy_dir, argp.zip_file)
    EXTRACTION_DIR = os.path.join(argp.deploy_dir, 'dumps')
    CLIENT_LOG_FN = os.path.join(EXTRACTION_DIR, argp.log_file)
    WAIT_CMD = 'choice /N /T %s /D Y >nul' % (argp.wait_time,)

    os.makedirs(EXTRACTION_DIR)
    logger = LogFile(CLIENT_LOG_FN)

    sys.stdout = sys.stderr = logger


    # start monitoring apps
    try:
        dll_lock = open('%s\\tools\\pe-sieve.dll' % (argp.deploy_dir,))
        hollows_hunter_path = '%s\\tools\\hollows_hunter.exe' % (argp.deploy_dir,)

        hollows_proc = ProcessCreator()
        response = hollows_proc.create(hollows_hunter_path, creation_flags=CREATE_SUSPENDED, working_dir=EXTRACTION_DIR)

        if response[0]:
            raise ValueError('[!] ERROR: Hollows hunter process creation. Code: %d' % (response[1],))

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
            hollows_proc.terminate()
            raise ValueError('[!] ERROR: Malware process creation. Code: %s' % (response[1],))

        print('[#] Malware process successfully created. PID: %d' % (malware_proc.pid,))

        subprocess.run(WAIT_CMD, shell=True)
        hollows_proc.resume()

        process_watcher.suspend_differences()
        watch_folder.close()
        registry_watcher.show_diff()

        malware_proc.terminate()
    except ValueError as e:
        print(str(e))
        if hollows_proc:
            hollows_proc.terminate()
        if malware_proc:
            malware_proc.terminate()
        if watch_folder:
            watch_folder.close()
    except:
        if hollows_proc:
            hollows_proc.terminate()
        if malware_proc:
            malware_proc.terminate()
        if watch_folder:
            watch_folder.close()
        raise
        

    logger.close()
    dll_lock.close()

    with zipfile.ZipFile(ZIP_FN, 'a') as zip_file:
        for root, _, files in os.walk(EXTRACTION_DIR):
            for f in files:
                if f.endswith('log') or f.endswith('txt'):
                    zip_file.write(os.path.join(root, f), 'logs\\' + f)
                else:
                    zip_file.write(os.path.join(root, f), 'dumps\\' + f)


if __name__ == '__main__':
    args = argparse.ArgumentParser()

    args.add_argument('-dd', '--deploy_dir', default=os.path.join('C:\\', 'maltest'))
    args.add_argument('-sn', '--sample_name', default='a.exe')
    args.add_argument('-wt', '--wait_time', default='30', type=int)
    args.add_argument('-lf', '--log_file', default='clientapp.log')
    args.add_argument('-zf', '--zip_file', default='extraction.zip')

    argp = args.parse_args()

    execute_experiment(argp)

