import sys
import time
import ctypes
import pythonmemorymodule

sys.mod_refs = {}
threedottwelve = (sys.version_info.major == 3 and sys.version_info.minor >= 12)
pyversion = f"{sys.version_info.major}.{sys.version_info.minor}"

api_version_table = {
    "3.6": 1060,
    "3.7": 1070,
    "3.8": 1080,
    "3.9": 1090,
    "3.10": 1013,
    "3.11": 1013,
    "3.12": 1013
}

PyModule_FromDefAndSpec2 = ctypes.pythonapi.PyModule_FromDefAndSpec2
PyModule_FromDefAndSpec2.restype = ctypes.py_object
PyModule_New = ctypes.pythonapi.PyModule_New
PyModule_New.restype = ctypes.py_object
PyModule_ExecDef = ctypes.pythonapi.PyModule_ExecDef

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
        mod = self.module()
        if 'moduledef' in f"{mod}":
            if spec.name not in sys.mod_refs:
                sys.mod_refs[spec.name] = {}
                sys.mod_refs[spec.name]['moduledef'] = mod
                sys.mod_refs[spec.name]['mod_from_def'] = PyModule_FromDefAndSpec2(ctypes.c_void_p(id(mod)), ctypes.c_void_p(id(spec)), api_version_table[pyversion])
                sys.mod_refs[spec.name]['module'] = PyModule_New(spec.name.encode('utf-8'))
                result = PyModule_ExecDef(ctypes.py_object(sys.mod_refs[spec.name]['module']), ctypes.c_void_p(id(sys.mod_refs[spec.name]['moduledef'])))
                if result > 0:
                    raise ImportError(f"ExecDef failed for module {spec.name} during multi-phase initialization")
                mod = sys.mod_refs[spec.name]['module']
            else:
                raise ImportError(f"{ spec.name } module already loaded, module available at sys.mod_refs['{spec.name}']['module']")
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
        self.module = pythonmemorymodule.MemoryModule(data=data)
        return self.module
