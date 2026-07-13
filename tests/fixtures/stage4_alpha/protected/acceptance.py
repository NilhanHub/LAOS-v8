import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calculator import add


class AdditionAcceptance(unittest.TestCase):
    def test_positive(self) -> None:
        self.assertEqual(add(7, 5), 12)

    def test_negative(self) -> None:
        self.assertEqual(add(-4, 9), 5)

    def test_zero(self) -> None:
        self.assertEqual(add(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
