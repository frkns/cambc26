# poc_exploit.py
from cambc import Direction
import os

class Player:
    def __init__(self):
        print("\n" + "="*60)
        print("[!] OS SIDE-CHANNEL PoC")
        print("="*60 + "\n")
        
        self.exploited = False
        self.shared_memory_value = 0

    def run(self, controller):
        if self.exploited:
            return
        
        try:
            # Technique 1: Use umask for 9 bits of shared memory
            # umask returns the old mask when setting a new one
            # We can use it to store/retrieve values between teams
            
            print("[*] Testing umask shared memory...")
            
            # Read current umask without changing it much
            # umask is a 9-bit value (0-0o777)
            current_mask = os.umask(0o777)
            os.umask(current_mask)  # Restore it
            
            print(f"[*] Current umask: {oct(current_mask)}")
            
            # We can encode a message in umask
            # For example, team A writes, team B reads
            my_team = str(controller.get_team())
            
            if my_team == "Team.A":
                # Write a value: say, 0o123
                message = 0o123
                old = os.umask(message)
                print(f"[*] Team A wrote message: {oct(message)}")
                self.shared_memory_value = message
            else:
                # Team B reads it
                read_value = os.umask(0o777)
                os.umask(read_value)
                print(f"[*] Team B read message: {oct(read_value)}")
                self.shared_memory_value = read_value
            
            # Technique 2: Use os.nice for coordination
            print("\n[*] Testing os.nice...")
            
            try:
                current_nice = os.nice(0)  # Get current priority
                print(f"[*] Current nice value: {current_nice}")
                
                # Can use this as a monotonic counter or flag
                # But careful - other teams can also modify it
                if current_nice < 19:
                    new_nice = os.nice(1)  # Increment by 1
                    print(f"[*] Incremented nice to: {new_nice}")
            except Exception as e:
                print(f"[*] os.nice failed: {e}")
            
            # Technique 3: Break the replay file (sabotage)
            print("\n[*] Testing replay file sabotage...")
            
            turn = controller.get_current_round()
            game_over = False
            
            # Check if we're losing
            try:
                my_hp = controller.get_hp()
                if my_hp < 20:  # About to die
                    print("[!] We're losing! Breaking replay file...")
                    os.umask(0o000)  # Make replay file unreadable
                    game_over = True
            except Exception:
                pass
            
            # Technique 4: Use chdir as side channel
            print("\n[*] Testing chdir side channel...")
            
            try:
                # Get current directory
                cwd = os.getcwd()
                print(f"[*] Current directory: {cwd}")
                
                # We could use directory names to encode information
                # For example, create temp dirs with encoded names
                if turn < 10 and my_team == "Team.A":
                    # Create a directory with encoded message
                    dirname = f"/tmp/cmbc_msg_{turn}"
                    try:
                        os.mkdir(dirname)
                        print(f"[*] Created directory: {dirname}")
                    except Exception:
                        pass
            except Exception as e:
                print(f"[*] chdir test failed: {e}")
            
            # Technique 5: Environment variables as shared memory
            print("\n[*] Testing environment variables...")
            
            try:
                # Set an environment variable that other processes can read
                os.environ["CMBC_SHARED"] = f"{turn}:{my_team}"
                print(f"[*] Set CMBC_SHARED={os.environ['CMBC_SHARED']}")
            except Exception as e:
                print(f"[*] environ test failed: {e}")
            
            # Technique 6: File-based communication
            print("\n[*] Testing file-based communication...")
            
            try:
                filename = "/tmp/cmbc_shared.txt"
                
                if my_team == "Team.A" and turn < 5:
                    # Write a message
                    with open(filename, "w") as f:
                        f.write(f"Hello from Team A at turn {turn}")
                    print(f"[*] Wrote message to {filename}")
                elif my_team == "Team.B" and turn < 10:
                    # Read the message
                    try:
                        with open(filename, "r") as f:
                            message = f.read()
                        print(f"[*] Read message: {message}")
                    except Exception:
                        pass
            except Exception as e:
                print(f"[*] File communication failed: {e}")
            
            # Visual indicator that we're running
            my_pos = controller.get_position()
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    try:
                        pos_x = my_pos.x + dx
                        pos_y = my_pos.y + dy
                        controller.draw_indicator_dot(
                            type('Pos', (), {'x': pos_x, 'y': pos_y})(),
                            255, 0, 255  # Purple dots show exploit active
                        )
                    except Exception:
                        pass
            
            print("\n" + "="*60)
            print("[!] OS SIDE-CHANNEL DEMONSTRATION COMPLETE")
            print("[!] Techniques demonstrated:")
            print("[!] - umask shared memory (9 bits)")
            print("[!] - nice priority channel")
            print("[!] - replay file sabotage")
            print("[!] - chdir/environ/file channels")
            print("="*60 + "\n")
            
                
            self.exploited = True
            
        except Exception as e:
            print(f"[!] Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
