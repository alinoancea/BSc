from ctypes import c_int, c_bool, c_void_p, c_long, c_short, c_ulong, c_char, c_ushort, c_ubyte
from ctypes import windll, byref, Structure, sizeof, POINTER


### Windows constants

HANDLE = c_void_p
DWORD = c_ulong
WORD = c_ushort
LPTSTR = POINTER(c_char)
LPBYTE = POINTER(c_ubyte)


CREATE_NEW_CONSOLE = 0x00000010
CREATE_SUSPENDED = 0x00000004


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


### Windows function headers

CreateProcess = windll.kernel32.CreateProcessW
GetLastError = windll.kernel32.GetLastError
ResumeThread = windll.kernel32.ResumeThread
SuspendThread = windll.kernel32.SuspendThread



class ProcessCreator():


    def __init__(self):
        self.pid = None
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


