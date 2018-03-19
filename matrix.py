import numpy as np
import itertools
import copy
from constant import * 
from numpy.linalg import matrix_rank


class Matrix(object):
    def __init__(self, rows, columns):
        """
            Creates an empty matrix
            :param rows: number of rows
            :param columns: number of columns
        """
        self.matrix = np.zeros((rows, columns)).astype(int)
        self.rows = rows
        self.columns = columns

    def build_init_register_matrix(self, registers, r4, k):
        """
            Creates a system of linear equations for the key difference k1 ^ k2
            :param registers: r1, r2, r3 as GwwRegisters object
            :param r4: register 4 as LFSR object
            :param k: key difference k1 ^ k2
        """
        for i in range(self.rows):
            registers.clock_with_r4(r4)
            x = registers.r1.g_delta(i)
            y = registers.r2.g_delta(i)
            z = registers.r3.g_delta(i)

            self.add_row_for_init_registers(x, y, z, i, k)

    def build_session_key_matrix(self):
        self.add_row_for_session_key(R1_SK_POSITIONS_AFTER_CLOCKING, R1_SK_START_ROW)
        self.add_row_for_session_key(R2_SK_POSITIONS_AFTER_CLOCKING, R2_SK_START_ROW)
        self.add_row_for_session_key(R3_SK_POSITIONS_AFTER_CLOCKING, R3_SK_START_ROW)

    def add_row_for_session_key(self, reg_sk_positions, start_row):
        for index, sk_positions in enumerate(reg_sk_positions):
            for sk_position in sk_positions:
                self.matrix[start_row + index][KEY_SIZE - 1 - sk_position] = 1   

    def add_row_for_init_registers(self, x, y, z, row, k):
        """
            Insert a new equation (row) into the matrix: x + y + z = k
            :param x: The x variables (register 1)
            :param y: The y variables (register 2)
            :param z: The z variables (register 3)
            :param row: The row number
            :param k: The key stream bit
        """
        self.insert_gdelta(x, R1_SIZE, row, R1_START_IN_SOLUTION, k)
        self.insert_gdelta(y, R2_SIZE, row, R2_START_IN_SOLUTION, k)
        self.insert_gdelta(z, R3_SIZE, row, R3_START_IN_SOLUTION, k)

    def insert_gdelta(self, variables, size, row, column, k):
        """
            Inserts the variables to the correct positions. 
            Note: The constant term from the equation is added to the key stream bit k.
            :param variables: The variables
            :param size: The number of variables (19 for r1, 22 for r2 and 23 for r3)
            :param row: The row number
            :param column: The column start position
            :param k: The key stream bit k
        """
        for i in range(size):
            self.matrix[row, column] = variables[i]
            column = column + 1
        k[row] = (k[row] - variables[-1]) % 2

    def gauss(self, b):
        """
            Gauss algorithm to solve a system of binary linear equations
            :param b: Vector with the equation solutions, in this case the
                      key difference
            :return list with all possible solutions to this system of
                    equations
        """
        n = self.matrix.shape[0]
        m = self.matrix.shape[1]
        not_unique = []
        for i in range(0, m):
            maxi = i
            # find non-zero element in column i, starting in row i
            for k in range(i, n):  # k index for rows
                if self.matrix[k, i] == 1:
                    maxi = k
            if self.matrix[maxi, i] == 1:
                # swap rows i and maxi in matrix
                # k is column index, start with i because columns < i are zero
                for k in range(i, m):
                    tmp = self.matrix[maxi, k]
                    self.matrix[maxi, k] = self.matrix[i, k]
                    self.matrix[i, k] = tmp
                # swap rows i and maxi in vector b
                tmp = b[maxi]
                b[maxi] = b[i]
                b[i] = tmp
            else:
                not_unique.append(i)

            # iterate all rows and add maxi row to current row such that the
            #  leading element is 0
            for u in range(i+1, n):
                if self.matrix[u, i] == 1:
                    for v in range(i, m):
                        self.matrix[u, v] = (self.matrix[u, v] + self.matrix[i, v]) % 2
                    b[u] = (b[u] + b[i]) % 2
        # iterate all rows backwards and solve the linear equation
        # If several solutions are possible to solve  the equation system, 
        # list all solutions in an array
        solutions = []
        not_unique_combinations = list(itertools.product([0, 1], repeat=len(not_unique)))
        for combination in not_unique_combinations:
            x = [0] * m
            for i in reversed(range(0, n)):
                if self.matrix[i, i % m] == 1:
                    x[i] = b[i]
                    if i < m-1:
                        for k in range(i+1, m):
                            x[i] = (x[i] - self.matrix[i, k] * x[k]) % 2
                else:
                    if i in not_unique:
                        position = not_unique.index(i)
                        x[i] = combination[position]
            solutions.append(x)   
        return solutions

    def is_solvable(self, k):
        k_vector = np.array(k).reshape(KEY_STREAM_SIZE, 1)
        extended_matrix = np.concatenate((self.matrix, k_vector ), axis=1)
        return matrix_rank(self.matrix) <= matrix_rank(extended_matrix)