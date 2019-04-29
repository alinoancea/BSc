from windows_components import CreateProcess, GetLastError, byref, SuspendThread, ResumeThread, TerminateProcess, \
        CreateToolhelp32Snapshot, CloseHandle, Process32First, Process32Next, Thread32First, Thread32Next, OpenThread, \
        sizeof
from windows_components import PROCESS_INFORMATION, STARTUPINFO, DWORD, INVALID_HANDLE_VALUE, PROCESSENTRY32, \
        TH32CS_SNAPPROCESS, TH32CS_SNAPTHREAD, THREADENTRY32, THREAD_SUSPEND_RESUME



class ProcessCreator():


    def __init__(self):
        self.pid = None
        self.hprocess = None
        self.process_information = PROCESS_INFORMATION()
        self.startupinfo = STARTUPINFO()
        self.startupinfo.cb = sizeof(self.startupinfo)


    def create(self, app_name=None, command_line=None, process_attributes=None, thread_attributes=None, inherit_h=False,
            creation_flags=0x0, environment=None, working_dir=None):
        """Creates a new process with the specified parameters.
        More: https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-createprocessa
        
        Args:
            app_name: module to execute
            command_line: command line to execute
            process_attributes: -
            thread_attributes: -
            inherit_h: new process inherit handles from calling process
            creation_flags: see https://docs.microsoft.com/en-us/windows/desktop/ProcThread/process-creation-flags
            environment: -
            working_dir: process working directory (i.e None = calling process working directory)
        
        Returns:
            tuple of (status, error_code)
            status: 0 on success, else 1
            error_code: returned value from CreateProcess on success, else GetLastError()
        """
        ret_code = CreateProcess(app_name, command_line, process_attributes, thread_attributes, inherit_h,
                creation_flags, environment, working_dir, byref(self.startupinfo), byref(self.process_information))

        if not ret_code:
            return (1, GetLastError())
        self.pid = self.process_information.dwProcessId
        self.hprocess = self.process_information.hProcess
        return (0, ret_code)


    def suspend(self):
        """Suspend process.
        More: https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-suspendthread

        Returns:
            tuple of (status, error_code)
            status: 0 on success, else 1
            error_code: returned value from SuspendThread on success, else GetLastError()
        """
        ret_code = SuspendThread(self.process_information.hThread)

        if ret_code == DWORD(-1).value - 1:
            return (1, GetLastError())
        return (0, ret_code)


    def resume(self):
        """Resume process.
        More: https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-resumethread

        Returns:
            tuple of (status, error_code)
            status: 0 on success, else 1
            error_code: returned value from ResumeThread on success, else GetLastError()
        """
        ret_code = ResumeThread(self.process_information.hThread)

        if ret_code == DWORD(-1).value - 1:
            return (1, GetLastError())
        return (0, ret_code)


    def terminate(self):
        """Terminate process.
        More: https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-terminateprocess
        
        Returns:
            tuple of (status, error_code)
            status: 0 on success, else 1
            error_code: returned value from TerminateProcess on success, else GetLastError()
        """
        ret_code = TerminateProcess(self.hprocess, 0x0)

        if not ret_code:
            return (1, GetLastError())
        return (0, ret_code)



class ProcessWatcher():


    def __init__(self):
        self.p = []


    def snap(self):
        """Get a snapshot of processes on the system and save PID for every process.
        """
        hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0x0)
        if hProcessSnap == INVALID_HANDLE_VALUE:
            print('   [!] ERROR-snap: CreateToolhelp32Snapshot. Code: %d' % (GetLastError(),))
            return

        pe32 = PROCESSENTRY32()
        pe32.dwSize = sizeof(pe32)
        if not Process32First(hProcessSnap, byref(pe32)):
            print('   [!] ERROR-snap: Process32First. Code: %d' % (GetLastError(),))
            CloseHandle(hProcessSnap)
            return

        while 1:
            if pe32.th32ProcessID not in self.p:
                self.p.append(pe32.th32ProcessID)

            code = Process32Next(hProcessSnap, byref(pe32))
            if not code:
                break

        CloseHandle(hProcessSnap)


    def suspend_differences(self):
        """Get a fresh snapshot of processes and suspend it if PID is unknown.
        """
        hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0x0)
        if hProcessSnap == INVALID_HANDLE_VALUE:
            print('   [!] ERROR-suspend: CreateToolhelp32Snapshot. Code: %d' % (GetLastError(),))
            return

        pe32 = PROCESSENTRY32()
        pe32.dwSize = sizeof(pe32)
        if not Process32First(hProcessSnap, byref(pe32)):
            print('   [!] ERROR-suspend: Process32First. Code: %d' % (GetLastError(),))
            CloseHandle(hProcessSnap)
            return

        to_suspend = []
        while 1:
            if pe32.th32ProcessID not in self.p:
                to_suspend.append(pe32.th32ProcessID)

            code = Process32Next(hProcessSnap, byref(pe32))
            if not code:
                break

        CloseHandle(hProcessSnap)

        self.suspend_process(to_suspend)


    def suspend_process(self, pid):
        """Searches through processes threads and suspend the one with specified PID.

        Args:
            pid: int, process ID which should be suspended
        """
        hThreadSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0x0)

        te32 = THREADENTRY32()
        te32.dwSize = sizeof(te32)
        if not Thread32First(hThreadSnapshot, byref(te32)):
            print('   [!] ERROR-suspend thread: Thread32First. Code: %d' % (GetLastError(),))
            CloseHandle(hThreadSnapshot)
            return

        while 1:
            if te32.th32OwnerProcessID in pid:
                hThread = OpenThread(THREAD_SUSPEND_RESUME, None, te32.th32ThreadID)

                if hThread:
                    SuspendThread(hThread)
                    CloseHandle(hThread)

            code = Thread32Next(hThreadSnapshot, byref(te32))
            if not code:
                break

        CloseHandle(hThreadSnapshot)


