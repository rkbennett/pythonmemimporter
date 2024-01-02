import sys
import ctypes
import pythonmemorymodule

threedottwelve = (sys.version_info.major == 3 and sys.version_info.minor >= 12)

class _FuncPtr(ctypes._CFuncPtr):
    _flags_ = ctypes._FUNCFLAG_CDECL | ctypes._FUNCFLAG_PYTHONAPI
    _restype_ = ctypes.py_object

class _memimporter(object):

    def __init__(self):
        self.module = ctypes.c_void_p()
                            
    def import_module(self, modname, pathname, initfuncname, findproc, spec):
        hmem = pythonmemorymodule.MemoryModule(data=findproc(modname))
        initf = hmem.get_proc_addr(initfuncname)
        self.module = ctypes.cast(initf, _FuncPtr)
        if threedottwelve:
            time.sleep(.01)
        while not isinstance(self.module, _FuncPtr):
            pass
        return self.module()

    def dlopen(self, data):
        self.module = pythonmemorymodule.MemoryModule(data=data)
        return ctypes.addressof(self.module.pythonmemorymodule.contents)
