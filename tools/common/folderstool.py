#!/usr/bin/env python3

import sys
import os
import threading

from windows_components import CreateFile, CloseHandle, ReadDirectoryChangesW, sizeof, create_string_buffer, byref, \
        GetLastError, memset, cast
from windows_components import GENERIC_READ, FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING, DWORD, MAX_PATH, \
        FILE_FLAG_BACKUP_SEMANTICS, INVALID_HANDLE_VALUE, FILE_NOTIFY_INFORMATION, FILE_NOTIFY_CHANGE_ATTRIBUTES, \
        FILE_NOTIFY_CHANGE_CREATION, FILE_NOTIFY_CHANGE_DIR_NAME, FILE_NOTIFY_CHANGE_FILE_NAME, \
        FILE_NOTIFY_CHANGE_LAST_WRITE, FILE_NOTIFY_CHANGE_SECURITY, FILE_NOTIFY_CHANGE_SIZE, PFILE_NOTIFY_INFORMATION


EVENTS = {
    0x00000001: 'created',
    0x00000002: 'deleted',
    0x00000003: 'changed',
    0x00000004: 'change/old_name',
    0x00000005: 'change/new_name'
}


class FolderWatcher(threading.Thread):


    def __init__(self, output=sys.stdout):
        super().__init__()
        self.hfolders = {}
        self.stop = 0
        self.results = []
        self.output = output


    def add_to_watch(self, path='C:\\'):
        handle = CreateFile(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS, None)
        if handle == INVALID_HANDLE_VALUE:
            print('[!] ERROR: Could not get handle for [%s] directory!' % (path,), file=sys.stderr)
            sys.exit(-1)

        self.hfolders[path] = handle


    def close(self):
        self.stop = 1
        for h in self.hfolders.values():
            CloseHandle(h)
        if self.output is not sys.stdout:
            self.output.close()


    def run(self):
        notify_filters = FILE_NOTIFY_CHANGE_FILE_NAME | FILE_NOTIFY_CHANGE_DIR_NAME | FILE_NOTIFY_CHANGE_ATTRIBUTES | \
                FILE_NOTIFY_CHANGE_SIZE | FILE_NOTIFY_CHANGE_LAST_WRITE | FILE_NOTIFY_CHANGE_CREATION | \
                FILE_NOTIFY_CHANGE_SECURITY

        bufsize = (sizeof(FILE_NOTIFY_INFORMATION) + MAX_PATH * 2) * 100
        buffer = create_string_buffer(bufsize)
        returned = DWORD(0)
        while 1:
            if self.stop:
                break
            for p, h in self.hfolders.items():
                memset(buffer, 0, bufsize)
                if not ReadDirectoryChangesW(h, buffer, bufsize, True, notify_filters, byref(returned), None, None):
                    print('ERROR: ReadDirectoryChanges() failed. Code: %x!' % GetLastError())

                offs = 0
                for _ in range(100):
                    fni = cast(buffer[offs:offs + sizeof(FILE_NOTIFY_INFORMATION)], PFILE_NOTIFY_INFORMATION).contents
                    namelen, nextoffs = int(fni.FileNameLength), int(fni.NextEntryOffset)
                    name = buffer.raw[offs + 12:offs + 12 + namelen].decode('utf16')
                    evt = EVENTS.get(fni.Action)
                    if evt is None:
                        continue
                    fn = os.path.join(p, name)
                    if (not os.path.isdir(fn)) and fn not in self.results:
                        try:
                            size = '%s bytes' % os.path.getsize(fn)
                        except Exception:
                            size = 'missing'
                        print('[%s] changed: %s (%s)' % (fn, evt, size), file=self.output)
                        self.results.append(fn)
                    if not nextoffs:
                        break
                    offs += nextoffs
