import unittest
from a5_2 import A5_2


class A5_2Test(unittest.TestCase):

    def test_one(self):
        key = 0xfffffffffffffc00
        frame_counter = 0x21
        a52 = A5_2(key, frame_counter)
        (send_key, receive_key) = a52.get_key_stream()
        send_key.pad_from_right(6)
        receive_key.pad_from_right(6)
        self.assertEqual(send_key.int_val(), 0xf4512cac13593764460b722dadd500)
        self.assertEqual(receive_key.int_val(), 0x4800d4328e16a14dcd7b9722265100)

if __name__ == '__main__':
    unittest.main()