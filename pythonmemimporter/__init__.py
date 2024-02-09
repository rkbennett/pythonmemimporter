import sys
import ctypes
import time
import pythonmemorymodule

threedottwelve = (sys.version_info.major == 3 and sys.version_info.minor >= 12)

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
        hmem = pythonmemorymodule.MemoryModule(data=findproc(modname))
        initf = hmem.get_proc_addr(initfuncname)
        self.module = ctypes.cast(initf, _FuncPtr)
        if threedottwelve:
            time.sleep(.01)
        while not isinstance(self.module, _FuncPtr):
            pass
        return self.module()

    def dlopen(self, data, mode):
        """
        Description:
            This function returns the address of pythonmemorymodule object once it is loaded
        Args:
            data: raw bytes of module to load
            mode: currently unused
        Returns:
            Handle to pythonmemorymodule object"""
        self.module = pythonmemorymodule.MemoryModule(data=data)
        return self.module
