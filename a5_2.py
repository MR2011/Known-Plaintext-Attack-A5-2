from lfsr import LFSR
from BitVector import BitVector
import copy
from constant import *
import math


class A5_2(object):
    """
        Represents the A5/2 stream cipher.
        A key stream for a given session key and the corresponding frame
        counter can be generated
    """
    def __init__(self, key, frame_counter):
        """
            Creates an A5/2 Object
            :param key: 64 bit Session Key
            :param frame_counter: 22 bit frame counter
        """
        if not (key >= 0 and key < math.pow(2, KEY_SIZE)):
            raise ValueError('Key value must be between 0 and 2^64!')
        if not (frame_counter >= 0 and frame_counter < math.pow(2, FRAME_COUNTER_SIZE)):
            raise ValueError('Frame counter value must be between 0 and 2^22!')
        self.r1 = LFSR(R1_SIZE, [], R1_TAPS, R1_MAJORITY_BITS, R1_NEGATED_BIT)
        self.r2 = LFSR(R2_SIZE, [], R2_TAPS, R2_MAJORITY_BITS, R2_NEGATED_BIT)
        self.r3 = LFSR(R3_SIZE, [], R3_TAPS, R3_MAJORITY_BITS, R3_NEGATED_BIT)
        self.r4 = LFSR(R4_SIZE, R4_CLOCK_BITS, R4_TAPS, [], None)
        self.key = BitVector(size=KEY_SIZE, intVal=key)
        self.frame_counter = BitVector(size=FRAME_COUNTER_SIZE,
                                       intVal=frame_counter)
        self.key_stream = BitVector(size=KEY_STREAM_SIZE)
        self.register_states = []

    def get_key_stream_with_predefined_registers(self, r1, r2, r3, r4, generate_only_send_key=False):
        """
            Sets the registers to the specified values (r1, r2, r3 and r4)
            and calculates a key stream
            :param r1: register 1 LFSR
            :param r2: register 2 LFSR
            :param r3: register 3 LFSR
            :param r4: register 4 LFSR
            :param generate_only_send_key: generates only the first 114 bits.
                                           Useful for checking the correct register values in the attack
            :return the generated key stream
        """
        self.r1 = LFSR(R1_SIZE, [], R1_TAPS, R1_MAJORITY_BITS, R1_NEGATED_BIT, bitstring=r1)
        self.r2 = LFSR(R2_SIZE, [], R2_TAPS, R2_MAJORITY_BITS, R2_NEGATED_BIT, bitstring=r2)
        self.r3 = LFSR(R3_SIZE, [], R3_TAPS, R3_MAJORITY_BITS, R3_NEGATED_BIT, bitstring=r3)
        self.r4 = LFSR(R4_SIZE, R4_CLOCK_BITS, R4_TAPS, [], None, bitstring=r4)

        self._clocking_with_majority(MAJORITY_CYCLES_A52)
        self._generate_key_stream(generate_only_send_key=generate_only_send_key)
        return (self.send_key, self.receive_key)

    def _create_register_backup(self):
        """
            Saves the register states r1, r2, r3 and r4 in a dictionary
        """
        self.initial_sates = {'r1': copy.deepcopy(self.r1),
                              'r2': copy.deepcopy(self.r2),
                              'r3': copy.deepcopy(self.r3),
                              'r4': copy.deepcopy(self.r4)}

    def _set_bits(self):
        """
            Sets the bits R1[15] = 1, R2[16] = 1, R3[18] = 1, R4[10] = 1.
        """
        self.r1.set_bit(FORCE_R1_BIT_TO_1, 1)
        self.r2.set_bit(FORCE_R2_BIT_TO_1, 1)
        self.r3.set_bit(FORCE_R3_BIT_TO_1, 1)
        self.r4.set_bit(FORCE_R4_BIT_TO_1, 1)

    def _clocking(self, limit, vector):
        """
            Performs clocking for all registers (r1, r2, r3 and r4)
            :param limit: number of clocking cycles
            :param vector: either the session key or the frame counter.
                           In each cycle a bit is XORed  to the first position.
        """
        for i in reversed(range(limit)):
            self.r1.clock(vector[i])
            self.r2.clock(vector[i])
            self.r3.clock(vector[i])
            self.r4.clock(vector[i])

    def _clocking_with_majority(self, limit, generate_key_stream=False, save_register_states=False):
        """
            Performs clocking for the registers r1, r2 and r3 with the
            majority function of r4
            :param limit: number of clocking cycles
            :param generate_key_stream: Boolean, which determines whether the
                                        output bits should be discarded
            :param save_register_states: Flag, that indicates whether the
                                         register states in each clock cycle
                                         should be saved
        """
        for i in range(limit):
            majority = self._majority()
            if self.r4.get_bit(R4_CLOCKING_BIT_FOR_R1) == majority:
                self.r1.clock()
            if self.r4.get_bit(R4_CLOCKING_BIT_FOR_R2) == majority:
                self.r2.clock()
            if self.r4.get_bit(R4_CLOCKING_BIT_FOR_R3) == majority:
                self.r3.clock()
            self.r4.clock()
            if generate_key_stream:
                if save_register_states:
                    self.register_states.append({'r1': copy.deepcopy(self.r1),
                                                 'r2': copy.deepcopy(self.r2),
                                                 'r3': copy.deepcopy(self.r3)})
                self._add_key_stream_bit(i)

    def _generate_key_stream(self, save_register_states=False, generate_only_send_key=False):
        """
            Generates 114 bits for the send key and 114 bits for the receive
            key.
        """
        self._clocking_with_majority(KEY_STREAM_SIZE, save_register_states=save_register_states, generate_key_stream=True)
        if not generate_only_send_key:
            self.send_key = self.key_stream.deep_copy()
            self._clocking_with_majority(KEY_STREAM_SIZE, save_register_states=save_register_states, generate_key_stream=True)
            self.receive_key = self.key_stream.deep_copy()
        else:
            self.send_key = self.key_stream
            self.receive_key = None

    def get_key_stream(self, save_register_states=False, generate_only_send_key=False):
        """
            Performs the following steps:
            1. Run A5/2 for 64 cycles and XOR the session key into the
               registers
            2. Run A5/2 for 22 cycles and XOR the frame counter into the
               registers
            3. Sets the bits R1[15] = 1, R2[16] = 1, R3[18] = 1, R4[10] = 1.
            4. Run A5/2 for 99 cycles and discard the output
            5. Run A5/2 for 228 cycles and use the output as key stream
            :param save_register_states: Flag, that indicates whether the
                                         register states in each clock cycle
                                         should be saved
            :return key stream as pair (send_key, receive_key) 
        """
        self._clocking(KEY_SIZE, self.key)
        self._clocking(FRAME_COUNTER_SIZE, self.frame_counter)
        self._set_bits()
        self._create_register_backup()
        self._clocking_with_majority(MAJORITY_CYCLES_A52)
        self._generate_key_stream(save_register_states, generate_only_send_key=generate_only_send_key)

        return (self.send_key, self.receive_key)

    def _add_key_stream_bit(self, index):
        """
            Calculates the output bit (key bit)
            :param index: The key stream bit index
        """
        self.key_stream[index] = self.r1.register[0] ^ self.r2.register[0] ^ self.r3.register[0] ^ self.r1.get_majority() ^ self.r2.get_majority() ^ self.r3.get_majority()

    def _majority(self):
        """
            :return most common bit in R4
        """
        clocked_bits = []
        clocked_bits = clocked_bits + self.r4.get_clock_bits()
        a = clocked_bits[0]
        b = clocked_bits[1]
        c = clocked_bits[2]
        return (a*b) ^ (a*c) ^ (b*c) 
