#!/usr/bin/env python3

import os
import sys
import time
import zipfile
import json

from datetime import datetime

import virtualbox

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')

from exception import VBoxLibException  # NOQA

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__)) + '/..'



class VBoxMachine:


    def __init__(self, name, snapshot, username, password, sample, launch_type='headless', wait_time=30,
            extraction_zip='extraction', sample_name='a'):
        self.virtualbox = virtualbox.VirtualBox()
        self.session = virtualbox.Session()

        self.name = name
        self.username = username
        self.password = password
        self.sample_path = os.path.normpath(os.path.join(PROJECT_DIR, sample) if not os.path.isabs(sample) else sample)
        self.sample_name = sample_name + '.exe'
        self.launch_type = launch_type
        self.wait_time = wait_time
        self.extraction_fn = extraction_zip + '.zip'
        self.deploy_location = 'C:\\maltest'
        self.guest_session = None
        self.console_session = None

        try:
            self.vm = self.virtualbox.find_machine(self.name)
        except virtualbox.library.VBoxErrorObjectNotFound:
            raise VBoxLibException('Couldn\'t find [%s] VM in your VirtualBox environment' % (self.name,))

        try:
            self.snapshot = self.vm.find_snapshot(snapshot or '')
        except virtualbox.library.VBoxErrorObjectNotFound as e:
            raise VBoxLibException('VM has no snapshots or snapshot name is invalid!\nERROR: %s' % (str(e),))

        if not os.path.isfile(self.sample_path):
            raise VBoxLibException('Sample [%s] can\'t be found!' % (self.sample_path,))

        self.vm.create_session(session=self.session)
        self.session.unlock_machine()


    def __wait_for_operation(self, op, message, status, show_progress=True):
        print(message, end='' if show_progress else '\n', flush=True)
        last_status = -10
        retries = 5
        while status.percent < 100:
            if status.percent - last_status > 9:
                if show_progress:
                    print('%s%%..' % (status.percent,), end='', flush=True)
                last_status = status.percent
            else:
                if not retries:
                    raise VBoxLibException('ERROR in [%s.__wait_for_operation] - exceeded operation retries' % (op,))
                if status.percent == last_status:
                    retries -= 1
            time.sleep(0.5)
        if show_progress:
            print('100%')


    def launch(self):
        self.__wait_for_operation('launch_vm_process', '[#] Launching machine [%s]..' % (self.name,),
                self.vm.launch_vm_process(self.session, self.launch_type))

        self.console_session = self.session.console
        try:
            self.guest_session = self.console_session.guest.create_session(self.username, self.password)
        except Exception:
            raise VBoxLibException('Username or password are invalid for guest creation!')

        _, stdout, _ = self.__execute_command('proc_architecture', 'set|findstr /ic:PROCESSOR_ARCHITECTURE')

        self.vm_architecture = '64' if 'AMD64' in stdout.decode().upper() else '86'


    def restore_snapshot(self):
        self.vm.lock_machine(self.session, virtualbox.library.LockType(2))
        self.__wait_for_operation('restore_snapshot', '[#] Restoring snapshot on [%s]..' % (self.name,),
                self.session.machine.restore_snapshot(self.snapshot))
        self.session.unlock_machine()


    def power_off(self):
        self.__wait_for_operation('power_off', '[#] Powering off [%s]..' % (self.name,),
                self.console_session.power_down())


    def __execute_command(self, op, cmd, args=[]):
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
        args = ['/c', cmd] + list(args)
        p, o, e = self.guest_session.execute('cmd.exe', args)
        if e and 'Traceback' in e.decode(errors='ignore'):
            raise VBoxLibException('ERROR in [%s.__execute_command]:\n%s' % (op, e.decode(errors='ignore')))

        return (p, o, e)


    def __create_directory(self, path, mode=700, flags=[]):
        self.guest_session.directory_create(path, mode, flags)


    def __file_copy(self, source, destination, flags=[], to_guest=True):
        if to_guest:
            return self.guest_session.file_copy_to_guest(source, destination, flags)
        else:
            return self.guest_session.file_copy_from_guest(source, destination, flags)


    def __check_existing_directory(self, directory_path):
        try:
            return self.guest_session.directory_exists(directory_path)
        except Exception as e:
            if 'No such file or directory on guest' in str(e):
                return False
            raise


    def __copy_on_vm(self, source, destination, indent=True):
        source = os.path.normpath(source)
        indentation = '\t' if indent else ''
        if os.path.isdir(source):
            if not self.__check_existing_directory(self.deploy_location + '\\' + destination):
                self.__create_directory(self.deploy_location + '\\' + destination)
            for root, _, files in os.walk(source):
                for f in files:
                    source_file = os.path.join(root, f)
                    destination_file = self.deploy_location + '\\' + destination + '\\' + f

                    self.__wait_for_operation('__file_copy', '%s[-] Copy [%s] -> [%s]...' % (indentation, source_file,
                            destination_file), self.__file_copy(os.path.join(source, f), destination_file),
                            show_progress=False)
        else:
            destination_file = self.deploy_location + '\\' + destination

            self.__wait_for_operation('__file_copy', '%s[-] Copy [%s] -> [%s]...' % (indentation, source,
                    destination_file), self.__file_copy(source, destination_file), show_progress=False)


    def copy_from_vm(self, source, destination, indent=True):
        destination = os.path.normpath(destination)
        indentation = '\t' if indent else ''
        self.__wait_for_operation('__file_copy', '%s[-] Extracting [%s] -> [%s]...' % (indentation, source,
                destination), self.__file_copy(source, destination, to_guest=False), show_progress=False)


    def deploy_necessary_files(self):
        print('[#] Copying necessary files on [%s]...' % (self.name,))
        # create deploy directory
        self.__create_directory(self.deploy_location)
        # copy sample
        self.__copy_on_vm(self.sample_path, self.sample_name)
        # copy tools directory
        self.__copy_on_vm(os.path.join(PROJECT_DIR, 'tools', 'x%s' % (self.vm_architecture,)), 'tools')
        # copy common tools files
        self.__copy_on_vm(os.path.join(PROJECT_DIR, 'tools', 'common'), 'tools')

        # unziping files
        self.__unzip_tools()


    def __unzip_tools(self):
        print('[#] Unzip python...')
        tools_dir = self.deploy_location + '\\tools\\'
        self.__execute_command('__unzip_tools', '%sunzip.exe' % (tools_dir,), ['%spython.zip' % (tools_dir,),
                '-d', tools_dir])


    def extract_archive(self):
        results_dir = os.path.join(PROJECT_DIR, 'results')
        datetime_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        experiment_result_dir = os.path.join(results_dir, datetime_now)
        os.makedirs(experiment_result_dir)

        zip_location = os.path.join(experiment_result_dir, 'results.zip')

        self.copy_from_vm(self.deploy_location + '\\' + self.extraction_fn, zip_location)

        zipfile.ZipFile(zip_location, 'r').extractall(experiment_result_dir)
        with open(os.path.join(experiment_result_dir, 'info.json'), 'w') as f:
            f.write(json.dumps({
                'malware': self.sample_path,
                'vm': self.name,
                'vm_achitecture': self.vm_architecture,
                'vm_username': self.username,
                'vm_password': self.password
            }))


    def launch_client_app(self):
        print('[#] Launching clientapp.py on guest...')
        python_path = self.deploy_location + '\\tools\\python\\python.exe'
        tools_dir = self.deploy_location + '\\tools\\'
        args = [
            '-dd', self.deploy_location,
            '-sn', self.sample_name,
            '-wt', str(self.wait_time),
            '-zf', self.extraction_fn
        ]
        self.__execute_command('launch_client_app', python_path, ['%sclientapp.py' % (tools_dir,)] + args)

        self.extract_archive()
