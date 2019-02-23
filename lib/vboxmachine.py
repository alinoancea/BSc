#!/usr/bin/env python3

import os
import sys
import time

import virtualbox

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')

from exception import VBoxLibException



class VBoxMachine:


    def __init__(self, name, snapshot, username, password, sample, launch_type='headless'):
        self.virtualbox = virtualbox.VirtualBox()
        self.session = virtualbox.Session()

        self.name = name
        self.username = username
        self.password = password
        self.launch_type = launch_type
        self.guest_session = None
        self.console_session = None

        self.vm = self.virtualbox.find_machine(self.name)
        if not self.vm:
            raise VBoxLibException('Couldn\'t find [%s] VM in your VirtualBox environment')

        try:
            self.snapshot = self.vm.find_snapshot(snapshot or '')
        except virtualbox.library.VBoxErrorObjectNotFound as e:
            raise VBoxLibException('There is no snapshot on VM or the snapshot couldn\'t be found!\n'
                    'ERROR: %s' % (str(e)))
        
        self.vm.create_session(session=self.session)
        self.session.unlock_machine()


    def wait_for_operation(self, message, status):
        print(message, end='', flush=True)
        while status.percent < 100:
            print('.', end='', flush=True)
            time.sleep(1)
        print('OK')


    def launch(self):
        self.wait_for_operation('[#] Launching machine [%s]' % (self.name,),
                self.vm.launch_vm_process(self.session, self.launch_type))

        self.console_session = self.session.console
        self.guest_session = self.console_session.guest.create_session(self.username, self.password)

        _, stdout, _ = self.guest_session.execute('cmd.exe', ['/c', 'set|findstr /ic:PROCESSOR_ARCHITECTURE'])

        self.vm_architecture = '64' if 'AMD64' in stdout.decode().upper() else '86'


    def restore_snapshot(self):
        self.vm.lock_machine(self.session, virtualbox.library.LockType(2))
        self.wait_for_operation('[#] Restoring snapshot on [%s]..' % (self.name,),
                self.session.machine.restore_snapshot(self.snapshot))
        self.session.unlock_machine()


    def power_off(self):
        self.wait_for_operation('[#] Powering off [%s]..' % (self.name,), self.console_session.power_down())


        