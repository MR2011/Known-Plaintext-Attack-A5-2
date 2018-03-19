from BitVector import BitVector
from lfsr import LFSR
from a5_2 import A5_2
from matrix import Matrix
import numpy as np
import copy
import itertools
from gww_registers import GwwRegisters
import math
from constant import *
from multiprocessing import Event, Pool


def retrieve_session_key(r1, r2, r3):
    """
        Creates and solves system of linear equations for retrieving the
        session key
        :return solutions for the system of linear equations
    """
    A = Matrix(KEY_SIZE, KEY_SIZE)
    A.build_session_key_matrix()
    b = r1.register + r2.register + r3.register
    solutions = A.gauss(b)
    return solutions


def reverse_clock(f, r, reverse_taps):
    """
        Revert the clocking step
        :param f: frame counter
        :param r: register
        :param reverse_taps: array with the tapping bits to calculate the
                             previous output bit
                             (without the majority function)
    """
    last_element = f
    for tap in reverse_taps:
        last_element = last_element ^ r.register[r.length - tap - 1]
    r.register >> 1
    r.register[0] = last_element


def reverse_frame_counter(r1, r2, r3, f):
    """
        Revert the step where the frame counter f is clocked into the registers
        :param r1, r2, r3: register 1,2 and 3 as LFSR object
        :param f: frame counter
    """
    for i in range(FRAME_COUNTER_SIZE):
        reverse_clock(f[i], r1, R1_REVERSE_TAPS)
        reverse_clock(f[i], r2, R2_REVERSE_TAPS)
        reverse_clock(f[i], r3, R3_REVERSE_TAPS)


def check_session_key(session_key, frame_counter, keystream):
    """
        Runs A5/2 with the session_key and frame_counter argument and
        compares the result with keystream
        :param session_key: 64 bit session key
        :param frame_counter: 22 bit frame counter
        :param keystream: expected keystream
        :return True if the calculated keystream is equal to keystream
    """
    a52 = A5_2(session_key, frame_counter)
    (send_key, receive_key) = a52.get_key_stream(generate_only_send_key=True)
    return keystream == send_key


def convert_solution_to_lfsrs(solution):
    """
        Converts the values from the Gauss algorithm to LFSR objects.
        :param solution: array with the values from the gauss algorithm
        :return register 1, 2 and 3 as LFSR object
    """
    r1_value = solution[R1_START_IN_SOLUTION:R1_END_IN_SOLUTION]
    r2_value = solution[R2_START_IN_SOLUTION:R2_END_IN_SOLUTION]
    r3_value = solution[R3_START_IN_SOLUTION:R3_END_IN_SOLUTION]
    r1 = LFSR(R1_SIZE, [], R1_TAPS, R1_MAJORITY_BITS, R1_NEGATED_BIT)
    r2 = LFSR(R2_SIZE, [], R2_TAPS, R2_MAJORITY_BITS, R2_NEGATED_BIT)
    r3 = LFSR(R3_SIZE, [], R3_TAPS, R3_MAJORITY_BITS, R3_NEGATED_BIT)
    r1.register = BitVector(bitlist=r1_value)
    r2.register = BitVector(bitlist=r2_value)
    r3.register = BitVector(bitlist=r3_value)
    return r1, r2, r3


def check_gauss_solution(solutions, r4, k, f):
    """
        Checks for each solution if it's valid.
        An A5/2 object is created and the registers are initialized with the
        values from the gauss solution. The generated key stream will be then
        compared to the key stream k. If it is the same, the solution
        is correct. Otherwise, the solution is not correct.
        :param solutions: List with solutions from the gauss algorithm
        :param r4: register 4 as LFSR object
        :param k: key stream to verify the solution
        :return the session key or None
    """
    a52 = A5_2(0x0, 0x0)
    for solution in solutions:
        # r1_value, r2_value, r3_value = convert_solution_to_lfsrs(solution)
        # R1[15], R2[16] and R3[18] are always set to 1 in  the A5/2 init
        # process.In order to restore the correct values, all combinations
        # must be checked
        for register_values in list(itertools.product([0, 1], repeat=3)):
            r1, r2, r3 = convert_solution_to_lfsrs(solution)
            (send_key, receive_key) = a52.get_key_stream_with_predefined_registers(str(r1.register), 
                                                                                   str(r2.register), 
                                                                                   str(r3.register), 
                                                                                   str(r4.register), 
                                                                                   generate_only_send_key=True)
            if send_key == k:
                r1.set_bit(FORCE_R1_BIT_TO_1, register_values[0])
                r2.set_bit(FORCE_R2_BIT_TO_1, register_values[1])
                r3.set_bit(FORCE_R3_BIT_TO_1, register_values[2])
                reverse_frame_counter(r1, r2, r3, f)
                session_keys = retrieve_session_key(r1, r2, r3)
                for session_key in session_keys:
                    session_key = BitVector(bitlist=session_key)
                    if check_session_key(session_key.int_val(), f.int_val(), k):
                        return session_key
    return None


def perform_attack(r4, k1, k2, f1, f2, r4_given=False):
    """
        Tries to find the session key K
        :param r4: register 4 as LFSR object
        :param k1: first keystream
        :param k2: second keystream
        :param f1: frame counter for k1
    """
    key_difference = k1 ^ k2
    k = list(key_difference)
    r4_init = copy.deepcopy(r4)
    registers = GwwRegisters(f1, f2)
    for i in range(MAJORITY_CYCLES_A52):
        registers.clock_with_r4(r4)
    A = Matrix(MATRIX_ROWS, MATRIX_COLUMNS)
    A.build_init_register_matrix(registers, r4, k)
    if A.is_solvable(k):
        solutions = A.gauss(k)
        if solutions:
            session_key = check_gauss_solution(solutions, r4_init, k1, f1)
            if session_key:
                print(hex(session_key.int_val()))
                if not r4_given:
                    solution_found.set()


def find_r4(start_value, steps, k1, k2, f1, f2):
    """
        Iterates through all posible values for r4 and
        performs the attack
        :param start_value: start value for r4
        :param steps: number of iterations for r4
        :param k1, k2: keystream 1 and 2
        :param f: frame counter for k1
    """
    for i in range(start_value, start_value + steps, 1):
        if solution_found.is_set():
            break
        r4 = LFSR(R4_SIZE, R4_CLOCK_BITS, R4_TAPS, [], None, None, i)
        if r4.get_bit(10) == 1:
            perform_attack(r4, k1, k2, f1, f2)


def init_pool(event):
    """
        Break condition for all processes as soon as a valid
        solution has been found
        :param event: Multiprocessing Event
    """
    global solution_found
    solution_found = event


def check_range(value, min, max, name):
    if not (value >= min and value < math.pow(2, max)):
        raise ValueError(name + ' must be between ' + str(min) + ' and 2^' + str(max) + '!')


def check_arguments(k1, k2, f1, f2):
    check_range(k1, 0, KEY_STREAM_SIZE, 'Keystream 1')
    check_range(k2, 0, KEY_STREAM_SIZE, 'Keystream 2')
    check_range(f1, 0, FRAME_COUNTER_SIZE, 'Frame Counter 1')
    check_range(f2, 0, FRAME_COUNTER_SIZE, 'Frame Counter 2')
    if (f1 ^ f2) != FRAME_COUNTER_DIFFERENCE:
        raise ValueError('Frame Counter XOR must be 2048!')


def init_attack(k1_value, k2_value, f1, f2, number_of_processes):
    """
        Initializes the attack and creates multiple processes
        :param k1_value, k2_value: keystream values
        :param f1: frame counter for keystream 1
    """
    check_arguments(k1_value, k2_value, f1, f2)
    k1 = BitVector(size=STREAM_KEY_SIZE, intVal=k1_value)
    k2 = BitVector(size=STREAM_KEY_SIZE, intVal=k2_value)
    f1 = BitVector(size=FRAME_COUNTER_SIZE, intVal=f1)
    f2 = BitVector(size=FRAME_COUNTER_SIZE, intVal=(f2))
    solution_found = Event()
    pool = Pool(processes=number_of_processes, initializer=init_pool,
                initargs=(solution_found,))
    procs = []
    for i in range(number_of_processes):
        steps = int(math.pow(2, 17) / number_of_processes)
        start_value = steps * i
        procs.append(pool.apply_async(find_r4, args=(start_value, steps, k1,
                     k2, f1, f2)))
    for p in procs:
        p.get()


def main():
    f = BitVector(bitstring='0001111100000010000100')
    f[22-1-11] = 0
    f_init = copy.deepcopy(f)
    key = 0xfaf3df3fa6698c0c
    frame_counter = f.int_val()
    a52 = A5_2(key, frame_counter)
    #print(a52.key)
    (send_key, receive_key) = a52.get_key_stream(True)
    f[22-1-11] = 1
    f2_init = copy.deepcopy(f)
    frame_counter = f.int_val()
    a522 = A5_2(key, frame_counter)
    (send_key2, receive_key2) = a522.get_key_stream(True)

    r4 = copy.deepcopy(a52.initial_sates['r4'])

    solution_found = Event()
    perform_attack(r4, send_key, send_key2, f_init, f2_init, r4_given=True)

if __name__ == '__main__':
    main()
