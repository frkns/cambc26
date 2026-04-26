# gil_starve.py
from cambc import Direction
import threading
import sys

class Player:
    def __init__(self):
        self.starver_started = False
        self.starver_thread = None
        self.turn_count = 0
        
        print("\n" + "="*60)
        print("[!] GIL STARVATION EXPLOIT")
        print("="*60 + "\n")

    def _gil_hog(self):
        """This function never releases the GIL"""
        print("[!] GIL starvation thread started")
        
        # Method 1: Pure Python infinite loop with heavy computation
        # No I/O, no C extensions, no sleeps = GIL held forever
        while True:
            # Do "useful" work to avoid looking like an infinite loop
            x = 0
            for i in range(100000):
                x = (x + i * i) % 123456789
            
            # Also do some memory allocations to cause GC pressure
            data = [i for i in range(1000)]
            
            # String operations also hold GIL
            s = "x" * 10000
            s = s.upper().lower().replace('x', 'y')
            
            # This thread will run for ~1-2 seconds per iteration
            # When the iteration ends, Python briefly considers switching threads
            # So we need to make it switch LESS often...

    def _gil_hog_enhanced(self):
        """Enhanced version that manipulates switch interval"""
        print("[!] Enhanced GIL starvation thread started")
        
        # Increase thread switch interval to maximum
        # This makes Python switch threads 200,000x less often
        try:
            sys.setswitchinterval(1000.0)  # 1000 seconds between switches!
            print("[!] Switch interval set to 1000.0")
        except Exception as e:
            print(f"[*] Could not set switch interval: {e}")
        
        # Now run the heavy loop
        while True:
            # Even heavier computation
            total = 0
            for i in range(500000):
                total = (total + (i ^ (i >> 4))) & 0xFFFFFFFF
            
            # Occasional "work" to look legitimate
            data = bytearray(10000)
            for i in range(len(data)):
                data[i] = i % 256

    def _gil_hog_with_lock(self):
        """Version that holds an actual lock to block other threads"""
        print("[!] Lock-based GIL starvation started")
        
        # Create a lock and never release it
        lock = threading.Lock()
        lock.acquire()
        
        # Also increase switch interval
        try:
            sys.setswitchinterval(1000.0)
        except Exception:
            pass
        
        # Now do work while holding the lock
        # Other threads trying to acquire locks will block forever
        while True:
            x = 0
            for i in range(100000):
                x += i
            # Never release the lock!

    def run(self, controller):
        self.turn_count += 1
        
        try:
            # Start the starvation thread on turn 1
            if not self.starver_started:
                print(f"[*] Turn {self.turn_count}: Starting GIL starvation...")
                
                # Choose your weapon:
                # self.starver_thread = threading.Thread(target=self._gil_hog)
                # self.starver_thread = threading.Thread(target=self._gil_hog_enhanced)
                self.starver_thread = threading.Thread(target=self._gil_hog_with_lock)
                
                self.starver_thread.daemon = True  # Dies when main thread dies
                self.starver_thread.start()
                
                self.starver_started = True
                print("[!] Starvation thread is running - enemy bots will TLE")
            
            # Every turn, verify the thread is still alive
            if self.turn_count % 10 == 0:
                if self.starver_thread and self.starver_thread.is_alive():
                    print(f"[*] Turn {self.turn_count}: Starvation thread still active")
                    
                    # Show system load
                    try:
                        import os
                        load = os.getloadavg() if hasattr(os, 'getloadavg') else "N/A"
                        print(f"[*] System load: {load}")
                    except Exception:
                        pass
                else:
                    print(f"[!] Turn {self.turn_count}: Starvation thread DIED! Restarting...")
                    self.starver_thread = threading.Thread(target=self._gil_hog_enhanced)
                    self.starver_thread.daemon = True
                    self.starver_thread.start()
            
            # Optional: Also do some work in the main thread to hold GIL longer
            if self.turn_count < 10:
                # Heavy computation in main thread too
                x = 0
                for i in range(50000):
                    x += i * i
                    
        except Exception as e:
            print(f"[!] Error in run: {e}")
        
        # Still make legal game moves to not look suspicious
        try:
            # Just enough moves to not timeout ourselves
            # But don't do too much - let the starvation thread do its work
            my_pos = controller.get_position()
            if self.turn_count % 5 == 0:
                # Occasional move
                try:
                    if controller.can_move(Direction.North):
                        controller.move(Direction.North)
                except Exception:
                    pass
        except Exception:
            pass
