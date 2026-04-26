class Player:
    def __init__(self):
        self.pool = []
        self.i = 0

    def run(self, controller):
        target = 1_500_000_000  # ~1GB (roughly)
        chunk = 100_000_000
        while self.i < target:
            b = bytearray(chunk)
            b[0] = 1
            self.pool.append(b)
            self.i += chunk
        
