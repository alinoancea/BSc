#!/usr/bin/env python3

import os
import sys
import time

import virtualbox

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')

from exception import VBoxLibException

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__)) + '/..'



class VBoxMachine:


    def __init__(self, name, snapshot, username, password, sample, launch_type='headless',
            sample_name='a.exe', wait_time=30):
        self.virtualbox = virtualbox.VirtualBox()
        self.session = virtualbox.Session()

        self.name = name
        self.username = username
        self.password = password
        self.sample_path = os.path.join(PROJECT_DIR, sample) if not os.path.isabs(sample) else sample
        self.sample_name = sample_name
        self.launch_type = launch_type
        self.deploy_location = 'C:\\maltest'
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


    def wait_for_operation(self, message, status, show_progress=True):
        print(message, end='' if show_progress else '\n', flush=True)
        while status.percent < 100:
            if show_progress:
                print('%s%%..' % (status.percent,), end='', flush=True)
            time.sleep(1)
        if show_progress:
            print('100%')


    def launch(self):
        self.wait_for_operation('[#] Launching machine [%s]..' % (self.name,),
                self.vm.launch_vm_process(self.session, self.launch_type))

        self.console_session = self.session.console
        self.guest_session = self.console_session.guest.create_session(self.username, self.password)

        _, stdout, _ = self.execute_command('set|findstr /ic:PROCESSOR_ARCHITECTURE')

        self.vm_architecture = '64' if 'AMD64' in stdout.decode().upper() else '86'


    def restore_snapshot(self):
        self.vm.lock_machine(self.session, virtualbox.library.LockType(2))
        self.wait_for_operation('[#] Restoring snapshot on [%s]..' % (self.name,),
                self.session.machine.restore_snapshot(self.snapshot))
        self.session.unlock_machine()


    def power_off(self):
        self.wait_for_operation('[#] Powering off [%s]..' % (self.name,), self.console_session.power_down())


    def execute_command(self, cmd, args=[]):
        """Executes a command on the VM.

        Args:
            cmd (str): command to be executed on the VM
            args (list|tuple): arguments to be given to the command

        Returns:
            process: information about the created process
            stdout: output of the executed command
            stderr: error messages of the executed command 
        """
        if not cmd or not isinstance(cmd, str):
            raise VBoxLibException('There is no command specified or typeof(cmd) is not "str"')
        if not isinstance(args, (list, tuple)):
            raise VBoxLibException('args argument should be of type "list" or "tuple"')
        args = ['/c', cmd] + args
        return self.guest_session.execute('cmd.exe', args)
        

    def create_directory(self, path, mode=700, flags=[]):
        self.guest_session.directory_create(path, mode, flags)


    def file_copy(self, source, destination, flags=[]):
        return self.guest_session.file_copy_to_guest(source, destination, flags)


    def check_existing_directory(self, directory_path):
        try:
            return self.guest_session.directory_exists(directory_path)
        except Exception as e:
            if 'No such file or directory on guest' in str(e):
                return False
            raise

    def copy_on_vm(self, source, destination, indent=True):
        source = os.path.normpath(source)
        if os.path.isdir(source):
            if not self.check_existing_directory(self.deploy_location + '\\' + destination):
                self.create_directory(self.deploy_location + '\\' + destination)
            for root, _, files in os.walk(source):
                for f in files:
                    source_file = os.path.join(root, f)
                    destination_file = self.deploy_location + '\\' + destination + '\\' + f

                    self.wait_for_operation('%s[-] Copy [%s] -> [%s]...' % ('\t' if indent else '',
                            source_file, destination_file), self.file_copy(os.path.join(source, f), 
                            destination_file), show_progress=False)
        else:
            destination_file = self.deploy_location + '\\' + destination

            self.wait_for_operation('%s[-] Copy [%s] -> [%s]...' % ('\t' if indent else '', source,
                    destination_file), self.file_copy(source, destination_file), show_progress=False)


    def deploy_necessary_files(self):
        print('[#] Copying necessary files on [%s]...' % (self.name,))
        # create deploy directory
        self.create_directory(self.deploy_location)
        # copy sample
        self.copy_on_vm(self.sample_path, self.sample_name)
        # copy tools directory
        self.copy_on_vm(os.path.join(PROJECT_DIR, 'tools', 'x%s' % (self.vm_architecture,)), 'tools')
        # copy common tools files
        self.copy_on_vm(os.path.join(PROJECT_DIR, 'tools', 'common'), 'tools')


