# utils/encoding.py
class Encoding:
    @staticmethod
    def encode_triple(a, b, c):
        """
        Encodes three integers into a single 32-bit integer.
        - a: 6 bits (values 0 to 63)
        - b: 6 bits (values 0 to 63)
        - c: 20 bits (values 0 to 1,048,575)
        """
        # Shift 'b' left by 6 bits, and 'c' left by 12 bits (6 + 6)
        # Combine them all using bitwise OR
        encoded_val = (c << 12) | (b << 6) | a
        return encoded_val

    @staticmethod
    def decode_triple(encoded_val):
        """
        Decodes a single 32-bit integer back into three integers.
        """
        # Mask the first 6 bits to get 'a' (0x3F is 63, or 111111 in binary)
        a = encoded_val & 0x3F
        
        # Shift right by 6 bits, then mask the next 6 bits to get 'b'
        b = (encoded_val >> 6) & 0x3F
        
        # Shift right by 12 bits to get 'c'. 
        # We mask it to 20 bits (0xFFFFF) to ensure we don't grab extra bits
        # if the integer happened to be larger than 32 bits.
        c = (encoded_val >> 12) & 0xFFFFF
        
        return a, b, c