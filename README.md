# pythonmemimporter

## **Compatible with Python 3.6+**

**Requires pythonmemorymodule**

A POC for importing pyd files from memory without the use of _memimporter. Uses raw python and the pythonmemorymodule to import python package pyd files. I have tried to model the usage of this module after _memimporter, but the code is simple enough you could tweak it to pass a bytes object vs a function which returns the bytes object.

## How it works

After spending a decent amount of time looking over the code from _memimporter I determined that porting it wasn't going to be a viable option due to the python object definitions which are used by python's c-api but aren't exposed to ctypes. From there I pivoted to the ctypes code and noticed that all ctypes.PyDLL returned was a function pointer which has a python flag set. So the method I used here, was to define a custom ctypes function pointer object and then cast the function pointer of the init function (found via pythonmemorymodule's get_func_addr) to my custom function pointer object. By doing this it tells python to handle the function like a python init function. Once this is cast it's as simple as calling the function which returns a valid module object. Cheers.

## Basic Usage

### Import a python pyd with pythonmemorymodule

```python
# Import the requirements
import sys
import importlib
from pythonmemimporter import _memimporter
_memimporter = _memimporter()
if (sys.version_info.major == 3 and sys.version_info.minor >= 11):
    import importlib.util

# Create a custom meta hook (required for getting loader assocaited to spec, this example does not work with python 3.12+)

class memory_importer(object):
    def find_module(self, module, path=None):
        if module == "_psutil_windows":
            return self
    def load_module(self, name):
        pass

# Define function which returns bytes of pyd (in this example the file _psutil_windows.pyd exists in my Downloads directory)

def _get_module_content(file):
    return open(f'c:\\users\\user\\Downloads\\{file}.pyd', "rb").read()

# Insert meta hook into meta path

sys.meta_path.insert(0, memory_importer())

# Create module in memory from init function

fullname = "_psutil_windows"
fpath = "/some/fake/path/here"
spec = importlib.util.find_spec(fullname, fpath)
initname = "PyInit__psutil_windows"
mod = _memimporter.import_module(fullname, fpath, initname, _get_module_content, spec)

# Add module to module cache

sys.modules[mod.__name__] = mod

# Make module available by module name

exec(f"{mod.__name__} = sys.modules['{mod.__name__}']")

# Profit

psutil_windows.cpu_stats()
```

### Return a pythonmemorymodule.MemoryModule object

```python
from pythonmemimporter import _memimporter
_memimporter = _memimporter()
data = open(r"..\..\Downloads\_psutil_windows.pyd", "rb").read()
memorymodule = _memimporter.dlopen(data, 0)
```

## Gotchas

* This is a POC and has some ISMs to it, for instance on python3.12 I could only get the code to not crash by adding a sleep of .01 (I personally don't like this tactic) I assume because of some form of race condition
* Currently, after importing some pyds and trying to execute them, the python interpreter will still crash. I've seen this on my pyclrhost package, though I'll also say that my pyclrhost package isn't a normal package.
* This has currently only been tested on windows 10 and 11 with python 3.10-3.12, but in theory should work on any version 3.6+

## Special Thanks

* [naksyn](https://github.com/naksyn) - For pythonmemorymodule (Windows)
* [nullbites](https://github.com/nullbites) - For his fd technique of loading shared objects (Linux)

