from lfsr import LFSR
from BitVector import BitVector
from collections import Counter
from constant import *
import math


class A5_1(object):
    """
        Represents the A5/1 stream cipher.
        A key stream for a given session key and the corresponding frame
        counter can be generated
    """
    def __init__(self, key, frame_counter):
        """
            Creates an A5/1 Object
            :param key: 64 bit Session Key
            :param frame_counter: 22 bit frame counter
        """
        if not (key >= 0 and key < math.pow(2, KEY_SIZE)):
            raise ValueError('Key value must be between 0 and 2^64!')
        if not (frame_counter >= 0 and frame_counter < math.pow(2, FRAME_COUNTER_SIZE)):
            raise ValueError('Frame counter value must be between 0 and 2^22!')
        self.r1 = LFSR(R1_SIZE, [R1_CLOCKING_BIT], R1_TAPS)
        self.r2 = LFSR(R2_SIZE, [R2_CLOCKING_BIT], R2_TAPS)
        self.r3 = LFSR(R3_SIZE, [R3_CLOCKING_BIT], R3_TAPS)
        self.key = BitVector(size=KEY_SIZE, intVal=key)
        self.frame_counter = BitVector(size=FRAME_COUNTER_SIZE, intVal=frame_counter)
        self.key_stream = BitVector(size=KEY_STREAM_SIZE)
        self._clocking(KEY_SIZE, self.key)
        self._clocking(FRAME_COUNTER_SIZE, self.frame_counter)
        self._clocking_with_majority(MAJORITY_CYCLES_A51)
        self._generate_key_stream()

    def _clocking(self, limit, vector):
        """
            Performs clocking for all registers (r1, r2 and r3)
            :param limit: number of clocking cycles
            :param vector: either the session key or the frame counter.
                           In each cycle a bit is XORed to the first position.
        """
        for i in reversed(range(limit)):
            self.r1.clock(vector[i])
            self.r2.clock(vector[i])
            self.r3.clock(vector[i])

    def _clocking_with_majority(self, limit, generate_key_stream=False):
        """
            Performs clocking for the registers r1, r2 and r3
            :param limit: number of clocking cycles
            :param generate_key_stream: Boolean, which determines whether the
                                        output bits should be discarded
        """
        for i in range(limit):
            majority = self._majority()
            if self.r1.get_clock_bits()[0] == majority:
                self.r1.clock()
            if self.r2.get_clock_bits()[0] == majority:
                self.r2.clock()
            if self.r3.get_clock_bits()[0] == majority:
                self.r3.clock()
            if generate_key_stream:
                self._add_key_stream_bit(i)

    def _generate_key_stream(self):
        """
            Generates 114 bits for the send key and 114 bits for the receive
            key.
        """
        self._clocking_with_majority(KEY_STREAM_SIZE, True)
        self.send_key = self.key_stream.deep_copy()
        self._clocking_with_majority(KEY_STREAM_SIZE, True)
        self.receive_key = self.key_stream.deep_copy()

    def get_key_stream(self):
        return (self.send_key, self.receive_key)

    def _add_key_stream_bit(self, index):
        """
            Calculates the output bit (key bit)
            :param index: The key stream bit index
        """
        self.key_stream[index] = self.r1.register[0] ^ self.r2.register[0] ^ self.r3.register[0]

    def _majority(self):
        """
            :return most common bit of the clocking bits from r1, r2 and r3
        """
        clocked_bits = []
        clocked_bits.append(self.r1.get_clock_bits()[0])
        clocked_bits.append(self.r2.get_clock_bits()[0])
        clocked_bits.append(self.r3.get_clock_bits()[0])

        counter = Counter(clocked_bits)
        return counter.most_common(1)[0][0]