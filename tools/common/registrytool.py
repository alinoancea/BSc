#!/usr/bin/env python3

import os
import fnmatch

import winreg


WHITELIST = []
REG_WATCHER = None
REG_WHITELIST = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'registry.whitelist')
RK_MAP = {
    winreg.HKEY_CURRENT_USER: 'HKCU',
    winreg.HKEY_LOCAL_MACHINE: 'HKLM',
}


# load registry whitelist
with open(REG_WHITELIST) as fr:
    for path in fr.readlines():
        WHITELIST.append(path.lower().replace('\\', '/'))



class RegistryWatcher():


    def __init__(self, keys=(winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER), exclude=None):
        self.keys = keys
        self.d = {}
        self.changes = []
        self.exclude = exclude


    def snap(self, path=None, key=None):
        if path is None:
            for k in self.keys:
                self.d[k] = self.snap(RK_MAP[k], k)
            return
        d = {0:{}}
        idx = 0
        while 1:
            try:
                name, val, _ = winreg.EnumValue(key, idx)
            except OSError:
                break
            d[0][name] = val
            idx += 1
        idx = 0
        while 1:
            try:
                name = winreg.EnumKey(key, idx)
            except OSError:
                break
            subpath = '%s/%s' % (path, name)
            if self.exclude and self.exclude(subpath):
                idx += 1
                continue
            try:
                subkey = winreg.OpenKey(key, name)
            except PermissionError:
                idx += 1
                continue
            d[name] = self.snap(subpath, subkey)
            winreg.CloseKey(subkey)
            idx += 1
        return d


    def diff(self, path=None, key=None, d=None):
        if key is None:
            for k in self.d:
                self.diff(RK_MAP[k], k, self.d[k])
            return self.changes
        idx = 0
        newlst = []
        while 1:
            try:
                name, val, _ = winreg.EnumValue(key, idx)
            except OSError:
                break
            if name in d[0]:
                if d[0][name] != val:
                    self.changes.append(('%s/%s' % (path, name), d[0][name], val))
            else:
                self.changes.append(('%s/%s' % (path, name), None, val))
            newlst.append(name)
            idx += 1
        for k in d[0]:
            if type(d[0][k]) != dict and k not in newlst:
                self.changes.append(('%s/%s' % (path, k), d[0][k], None))
        idx = 0
        while 1:
            try:
                name = winreg.EnumKey(key, idx)
            except OSError:
                break
            subpath = '%s/%s' % (path, name)
            if self.exclude and self.exclude(subpath):
                idx += 1
                continue
            try:
                subkey = winreg.OpenKey(key, name)
            except PermissionError:
                idx += 1
                continue
            self.diff(subpath, subkey, d.get(name, {0:{}}))
            winreg.CloseKey(subkey)
            idx += 1



def whitelisted(path):
    pth = path.lower().replace('\\', '/')
    for e in WHITELIST:
        if fnmatch.fnmatch(pth, e):
            return True


def create_snapshot():
    global REG_WATCHER

    REG_WATCHER = RegistryWatcher(exclude=whitelisted)
    print('[#] Snapshotting registry...')
    REG_WATCHER.snap()


def show_diff():
    diff = REG_WATCHER.diff()
    print('[*] Differences:')
    for path, old, new in diff:
        if old is None:
            op = 'created: [%s]' % new
        elif new is None:
            op = 'deleted (was [%s])' % old
        else:
            op = 'changed: [%s] -> [%s]' % (old, new)
        print('[-]   [%s]: %s' % (path, op))
