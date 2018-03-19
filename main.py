# coding=utf-8
import os
import sys
from a5_1 import A5_1
from a5_2 import A5_2
import gww_attack as a52_attack
menu_actions = {}


# =========================
#     MENU FUNCTIONS
# =========================
def main_menu():
    print('\n')
    print(25 * '-', 'MENU', 25 * '-')
    print('Please choose: ')
    print('1. Generate session key with A5/1')
    print('2. Generate session key with A5/2')
    print('3. A5/2 attack')
    print('\n0. Exit')
    choice = input(' >> ')
    exec_menu(choice)
    return


# execute menu
def exec_menu(choice, clear=True):
    if clear:
        os.system('clear')
    ch = choice.lower()

    if ch == '':
        menu_actions['main_menu']()
    else:
        try:
            menu_actions[ch]()
        except KeyError:
            print('Invalid input, please try again.\n')
            menu_actions['main_menu']()
    return


# Back to main menu
def back():
    menu_actions['main_menu']()


# exit programm
def exit():
    print('Program exit')
    sys.exit()


def mini_menu(current_entry):
    print('\nPlease choose: \n')
    print('1. Run again')
    print('2. Back')
    print('\n0. Exit')
    choice = input(' >> ')
    if choice == '1':
        choice = current_entry
    elif choice == '2':
        choice = '9'
    exec_menu(choice)


def a51():
    print(25 * '-', 'A5/1', 25 * '-')
    print('Insert 64 bit session key as hexadecimal value:\n')
    session_key = read_input()
    print(session_key)
    print('Insert 22 bit frame counter as hexadecimal value:\n')
    frame_counter = read_input()
    try:
        a51 = A5_1(session_key, frame_counter)
    except ValueError as error:
        print('\nError: ' + str(error) + '\n')
        menu_actions['1']()
    (send_key, receive_key) = a51.get_key_stream()
    print('k1: ' + str(hex(send_key.int_val())) + '\n')
    print('k2: ' + str(hex(receive_key.int_val())) + '\n')
    mini_menu('1')


def a52():
    print(25 * '-', 'A5/2', 25 * '-')
    print('Insert 64 bit session key as hexadecimal value:\n')
    session_key = read_input()
    print('Insert 22 bit frame counter as hexadecimal value:\n')
    frame_counter = read_input()
    try:
        a52 = A5_2(session_key, frame_counter)
    except ValueError as error:
        print('\nError: ' + str(error) + '\n')
        menu_actions['2']()
    (send_key, receive_key) = a52.get_key_stream()
    print('k1: ' + str(hex(send_key.int_val())) + '\n')
    print('k2: ' + str(hex(receive_key.int_val())) + '\n')
    mini_menu('2')


def attack():
    print(25 * '-', 'A5/2 Attack', 25 * '-')
    print('Insert first 114 bit keystream as hexadecimal value:\n')
    k1 = read_input()
    print('Insert first 22 bit frame counter as hexadecimal value:\n')
    f1 = read_input()
    print('Insert second 114 bit keystream as hexadecimal value:\n')
    k2 = read_input()
    print('Insert second 22 bit frame counter as hexadecimal value:\n')
    f2 = read_input()
    print('Number of processes:\n')
    processes = read_input(10)
    try:
        a52_attack.init_attack(k1, k2, f1, f2, processes)
    except ValueError as error:
        print('Error: ' + str(error))
        menu_actions['3']()
    mini_menu('2')

# =======================
#    MENUS DEFINITIONS
# =======================

# Menu definition
menu_actions = {
    'main_menu': main_menu,
    '1': a51,
    '2': a52,
    '3': attack,
    '9': back,
    '0': exit,
}


def read_input(base=16):
    try:
        value = int(input(' >> '), base)
    except ValueError as error:
        print('Error: invalid value!')
        return read_input()
    return value

# ===============
#      MAIN
# ===============
if __name__ == '__main__':
    try:
        os.system('clear')
        main_menu()
    except KeyboardInterrupt:
        print('Program exit')
