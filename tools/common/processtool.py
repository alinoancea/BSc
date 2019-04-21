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


