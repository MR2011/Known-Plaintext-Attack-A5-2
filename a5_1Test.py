import unittest
from a5_1 import A5_1


class A5_1Test(unittest.TestCase):
    def test_one(self):
        key = 0xEFCDAB8967452312
        frame_counter = 0x000134
        a51 = A5_1(key, frame_counter)
        (send_key, receive_key) = a51.get_key_stream()
        self.assertEqual(send_key.int_val(), 0x14D3AA960BFA0546ADB861569CA30)
        self.assertEqual(receive_key.int_val(), 0x093F4D68D757ED949B4CBE41B7C6B)

if __name__ == '__main__':
    unittest.main()
