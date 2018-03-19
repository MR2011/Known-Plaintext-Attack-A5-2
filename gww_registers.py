from collections import Counter
from constant import *


class GwwRegisters:
    def __init__(self, f1, f2):
        self.r1 = GwwRegister(R1_SIZE, R1_TAPS, R1_X_DELTA_PRODUCTS, R1_DELTA_DELTA_PRODUCTS, 'r1', R1_FC_POSITIONS_AFTER_CLOCKING, f1, f2)
        self.r2 = GwwRegister(R2_SIZE, R2_TAPS, R2_X_DELTA_PRODUCTS, R2_DELTA_DELTA_PRODUCTS, 'r2', R2_FC_POSITIONS_AFTER_CLOCKING, f1, f2)
        self.r3 = GwwRegister(R3_SIZE, R3_TAPS, R3_X_DELTA_PRODUCTS, R3_DELTA_DELTA_PRODUCTS, 'r3', R3_FC_POSITIONS_AFTER_CLOCKING, f1, f2) 

    def clock(self, register):
        """
            :param register: Register number (1,2,3) determining which
                             register will be clocked
        """
        if register == 1:
            self.r1.clock()
        elif register == 2:
            self.r2.clock()
        elif register == 3:
            self.r3.clock()

    def clock_with_r4(self, r4):
        """
            Clocks the registers r1, r2, r3 and r4.
            :param r4: register 4 as LFSR object
        """
        majority = self._majority(r4)
        if r4.get_bit(R4_CLOCKING_BIT_FOR_R1) == majority:
            self.r1.clock()
        if r4.get_bit(R4_CLOCKING_BIT_FOR_R2) == majority:
            self.r2.clock()
        if r4.get_bit(R4_CLOCKING_BIT_FOR_R3) == majority:
            self.r3.clock()
        r4.clock()

    def _majority(self, r4):
        clocked_bits = []
        clocked_bits = clocked_bits + r4.get_clock_bits()
        counter = Counter(clocked_bits)
        return counter.most_common(1)[0][0]


class GwwRegister:
    """
        Represents a Register
        Each cell contains the initial variables (before the 99 clocking
        cycles and after the key setup)to calculate the actual value in
        the current cycle
    """
    def __init__(self, size, taps, x_delta_products, delta_delta_products, register_no, fc_positions, f1, f2):
        """
            :param size: The size of the register
            :param taps: Array, containing the positions for the variables
                         which are XORed in each clocking cycle
            :param x_delta_products: Array with tuples which contain the x * delta positions for the g_delta function
                                     Example for R1: x_12 * delta_14 XOR  x_14 * delta_12 XOR x_14 * delta_15 XOR x_15 * delta_14 XOR x_12 * delta_15 XOR x_15 * delta_12
                                             --> [(12, 14), (14,12), (14, 15), (15, 14), (12, 15), (15,12)]
            :param delta_delta_products: Array with tuples which contain the delta_i * delta_j positions for the g_delta function.
                                         (Note: for single delta positions --> delta_18 = (delta_18, delta_18)
                                         Example for R1: delta_14 * delta_12  XOR delta_14 * delta_15 XOR delta_15 * delta_12 XOR delta_12 XOR delta_15 XOR delta_18
                                                  --> [(14, 12), (14, 15), (15, 12), (12, 12), (15, 15), (18, 18)]
            :param register_no: The register name. Only valid values are r1, r2, r3 or r4 (Must match the delta dictionary!)
            :param fc_positions: Contains the frame counter positions which are XORed with the register values (required for computing deltas)
            :param f1: frame counter for keystream 1
            :param f2: frame counter for keystream 2
        """
        self.size = size
        self.taps = taps
        self.register_no = register_no
        self.x_delta_products = x_delta_products
        self.delta_delta_products = delta_delta_products
        self.register = [None] * size
        self.fc_positions = fc_positions
        self.f1 = f1
        self.f2 = f2
        for i in range(size):
            self.register[i] = [i]

    def clock(self):
        """
            Performs the clocking for a register.
            Calculates the feedback polynom according to the taps and shifts
            the register afterwards
        """
        feedback_polynom = []
        for tap in self.taps:
            feedback_polynom += self.get_bit(tap)
        last = []
        for element in feedback_polynom:
            # even number of element => delete element
            # uneven number of element => keep one element
            if feedback_polynom.count(element) % 2 == 1:
                last.append(element)
            feedback_polynom = list(filter(lambda a: a != element, feedback_polynom))
        for i in range(self.size - 1):
            self.register[i] = self.register[i+1]
        self.register[-1] = last

    def get_bit(self, i):
        return self.register[self.size - 1 - i]

    def calculate_deltas(self):
        """
            Calculates the difference between registers from keystream 1 and keystream 2
        """
        deltas = [0] * self.size
        for i, values in enumerate(self.register):
            delta = 0
            for value in values:
                for pos in self.fc_positions[value]:
                    delta = delta ^ self.f1[pos] ^ self.f2[pos]
            deltas[i] = delta
        return deltas

    def g_delta(self, cycle):
        """
            :param cycle: the current clocking cycle
            :return Array with the initial x variables to calculate the ouput
                    in the current cycle for this register
        """
        g_delta = [0] * (self.size + 1)
        delta = self.calculate_deltas()
        for position in self.x_delta_products:
            x_pos = position[0]
            d_pos = position[1]
            for x in self.get_bit(x_pos):
                g_delta[x] = (g_delta[x] + delta[self.size - 1 - d_pos]) % 2
        result = 0
        for constant in self.delta_delta_products:
            result = result + delta[self.size - 1 - constant[0]] * delta[self.size - 1 - constant[1]]
        result = result % 2
        g_delta[-1] = result
        return g_delta
