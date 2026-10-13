"""Y4: AmigaOS CON: (ROM CON: and KingCON) sends the cursor-up key as the 8-bit CSI 0x9B and
'A', not ESC [ A. PyREPL dropped the undecodable 0x9B and typed the 'A' (a stray "A" after Up, no
history); with TERM unset its fallback terminfo ("dumb") has no keys at all, and vtcon's terminfo
only knows the application-mode ESC O A. The 8-bit C1 bytes at the start of a key are now their
7-bit pairs, and the normal-mode arrows are always keys.

Run: build/host/python.exe -m unittest -v tests/test_pyrepl_c1.py
"""
import os
import unittest

from _pyrepl.terminfo import TermInfo
from _pyrepl.unix_eventqueue import EventQueue


def queue(term):
    fd = os.open(os.devnull, os.O_RDONLY)
    try:
        return EventQueue(fd, "utf-8", TermInfo(term, fallback=True))
    finally:
        os.close(fd)


def names(q, data):
    for b in data:
        q.push(b)
    out = []
    while not q.empty():
        out.append(q.get().data)
    return out


class EightBitCsi(unittest.TestCase):
    def test_up_as_csi_A_is_the_up_key_with_no_terminfo_keys(self):
        # TERM unset on the Amiga: the fallback is "dumb", which has no keys
        for term in ("dumb", "no-such-terminal"):
            self.assertEqual(names(queue(term), b"\x9bA"), ["up"], term)

    def test_up_as_csi_A_is_the_up_key_when_terminfo_says_ESC_O_A(self):
        # TERM=vtcon: kcuu1=\EOA (application mode), the console ignores smkx
        self.assertEqual(names(queue("xterm"), b"\x9bA"), ["up"])

    def test_all_four_arrows_and_the_ss3_form(self):
        q = queue("dumb")
        self.assertEqual(names(q, b"\x9bA\x9bB\x9bC\x9bD"), ["up", "down", "right", "left"])
        self.assertEqual(names(queue("xterm"), b"\x8fA"), ["up"])

    def test_no_stray_A_and_later_keys_flow(self):
        q = queue("dumb")
        self.assertEqual(names(q, b"\x9bAx"), ["up", "x"])

    def test_a_continuation_byte_0x9b_inside_a_character_is_not_a_csi(self):
        # U+011B is C4 9B in UTF-8
        self.assertEqual(names(queue("dumb"), "ě".encode()), ["ě"])

    def test_seven_bit_escape_arrows_still_work(self):
        self.assertEqual(names(queue("dumb"), b"\x1b[A"), ["up"])


if __name__ == "__main__":
    unittest.main()
