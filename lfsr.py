from BitVector import BitVector


class LFSR(object):
    """
        This class represents a linear feedback shift register for
        the A5 stream cipher
    """
    def __init__(self, length, clock_bits, taps, majority_bits=None, negated_bit=None, bitstring=None, int_value=None):
        """
            :param length: size (number of bits) of the lfsr
            :param clock_bits: position of bits which indicate
                               clocking for A5/1
            :param taps: position of bits to calculate the first
                         position in a clocking cycle
            :param majority_bits: Optional parameter, positions of
                                  bits for the majority function A5/2
            :param negated_bit: Optional parameter, position of the
                                bit that is negated in the majority
                                function (for A5/2)
            :param bitstring: register value as bitstring
            :param int_value: register value as integer
        """
        if bitstring:
            self.register = BitVector(bitstring=bitstring)
        elif int_value:
            self.register = BitVector(size=length, intVal=int_value)
        else:
            self.register = BitVector(size=length)
        self.length = length
        self.taps = taps
        self.majority_bits = majority_bits
        self.negated_bit = negated_bit
        self.clock_bits = []
        for clock_bit in clock_bits:
            self.clock_bits.append(length - clock_bit - 1)

    def clock(self, key_bit=False):
        """
            Clocks the lfsr
            :param key_bit: Optional parameter for XORing
                            an additional bit into the first
                            position (relevant if frame counter
                            or session key is clocked into lfsr)
        """
        result = key_bit
        for tap in self.taps:
            result = result ^ self.register[(self.length - tap - 1)]
        self.register << 1
        self.register[-1] = result

    def get_clock_bits(self):
        clock_bit_values = []
        for clock_bit in self.clock_bits:
            clock_bit_values.append(self.register[clock_bit])
        return clock_bit_values

    def set_bit(self, index, value):
        self.register[self.length - index - 1] = value

    def get_bit(self, index):
        return self.register[self.length - index - 1]

    def get_majority(self):
        values = [self.register[self.length - self.negated_bit - 1] ^ 1]
        for bit in self.majority_bits:
            values.append(self.register[self.length - bit - 1])
        a = values[0]
        b = values[1]
        c = values[2]
        return (a*b) ^ (a*c) ^ (b*c) 
