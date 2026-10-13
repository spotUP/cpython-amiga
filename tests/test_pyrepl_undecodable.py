"""Y2-TERM(b): PyREPL's event queue kept an undecodable byte (0x9B, the 8-bit CSI a console
may send) in its buffer, so every later key was appended behind it and decoded to nothing:
the REPL took no more input. The byte is dropped and later keys flow; an incomplete UTF-8
sequence still waits for its rest.

Run: build/host/python.exe -m unittest -v tests/test_pyrepl_undecodable.py
"""
import os
import unittest

from _pyrepl.terminfo import TermInfo
from _pyrepl.unix_eventqueue import EventQueue


def queue():
    os.environ.setdefault("TERM", "xterm")
    fd = os.open(os.devnull, os.O_RDONLY)
    try:
        return EventQueue(fd, "utf-8", TermInfo("xterm", fallback=True))
    finally:
        os.close(fd)


def keys(q, data):
    for b in data:
        q.push(b)
    out = []
    while not q.empty():
        out.append(q.get().data)
    return out


class Undecodable(unittest.TestCase):
    def test_a_later_key_arrives_after_an_undecodable_byte(self):
        q = queue()
        self.assertEqual(keys(q, b"\xffA"), ["A"])
        self.assertEqual(keys(q, b"x"), ["x"])

    def test_a_lead_byte_followed_by_ascii_keeps_the_ascii(self):
        self.assertEqual(keys(queue(), b"\xc3("), ["("])

    def test_valid_utf8_still_decodes_and_waits_for_its_rest(self):
        q = queue()
        self.assertEqual(keys(q, b"\xc3"), [])
        self.assertEqual(keys(q, b"\xa9"), ["é"])
        self.assertEqual(keys(q, "€".encode()), ["€"])


if __name__ == "__main__":
    unittest.main()
