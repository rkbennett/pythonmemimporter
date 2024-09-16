import os
import sys
import time
import ctypes

if os.name == 'nt':
    import pythonmemorymodule
elif os.name == 'posix':
    MEMFD_CREATE_NO = 319

threedottwelve = (sys.version_info.major == 3 and sys.version_info.minor >= 12)

PyModule_New = ctypes.pythonapi.PyModule_New
PyModule_New.restype = ctypes.py_object
PyModule_ExecDef = ctypes.pythonapi.PyModule_ExecDef
Py_IncRef = ctypes.pythonapi.Py_IncRef

class _FuncPtr(ctypes._CFuncPtr):
    """
    Description:
        This class wraps the ctypes._CFuncPtr class, which allows us to force replication of the behavior from ctypes.PyDLL
    """
    _flags_ = ctypes._FUNCFLAG_CDECL | ctypes._FUNCFLAG_PYTHONAPI
    _restype_ = ctypes.py_object

class _memimporter(object):

    def __init__(self):
        self.module = ctypes.c_void_p()
                            
    def import_module(self, modname, pathname, initfuncname, findproc, spec):
        """
        Description:
            This function returns an init function from a python C extensions, which can be used to load python pyd files directly from memory
        Args:
            modname: module/package name to load
            pathname: file path of target module
            initfuncname: name of the init function for the module (PyInit_<modulename> typically)
            findproc: python function pointer for function which can be used to retrieve raw bytes of pyd
            spec: valid spec for the pyd
        Returns:
            result of an module's init function"""
        if os.name == 'nt':
            hmem = pythonmemorymodule.MemoryModule(data=findproc(modname))
            initf = hmem.get_proc_addr(initfuncname)
        elif os.name == 'posix':
            fd = ctypes.CDLL(None).syscall(MEMFD_CREATE_NO, "/tmp/none", 1)
            os.write(fd, findproc(modname))
            funcPtr = ctypes.CDLL(f"/proc/self/fd/{ fd }")
            initf = funcPtr.__getitem__(initfuncname)
        self.module = ctypes.cast(initf, _FuncPtr)
        if threedottwelve:
            time.sleep(.01)
        while not isinstance(self.module, _FuncPtr):
            pass
        mod = self.module()
        if 'moduledef' in f"{mod}":
            mod_def = mod
            tmp = Py_IncRef(ctypes.py_object(mod_def))
            mod = PyModule_New(spec.name.encode('utf-8'))
            result = PyModule_ExecDef(ctypes.py_object(mod), ctypes.c_void_p(id(mod_def)))
            if result > 0:
                raise ImportError(f"ExecDef failed for module {spec.name} during multi-phase initialization")
        return mod

    def dlopen(self, data, mode):
        """
        Description:
            This function returns the address of pythonmemorymodule object once it is loaded
        Args:
            data: raw bytes of module to load
            mode: currently unused
        Returns:
            Handle to pythonmemorymodule object"""
        if os.name == 'nt':
            self.module = pythonmemorymodule.MemoryModule(data=data)
        else:
            fd = ctypes.CDLL(None).syscall(319, "/tmp/none", 1)
            os.write(fd, data)
            self.module = ctypes.CDLL(f"/proc/self/fd/{ fd }")
            self.module.__dict__['get_proc_addr'] = self.module.__getattr__
        return self.module
