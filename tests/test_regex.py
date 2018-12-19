import unittest
from hocr_parser import parser


class RegexTests(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        cls.bbox_pattern = parser.HOCRElement.COORDINATES_PATTERN

    def test_valid_bboxes(self):
        # normal case
        self.bbox_should_match(
            string="bbox 1 2 3 4",
            expected=(1, 2, 3, 4)
        )

        # floats (not in spec)
        self.bbox_should_match(
            string="bbox 1.2 2.4 3.6 4.8",
            expected=(1, 2, 3, 4)
        )

        # negative ints (not in spec)
        self.bbox_should_match(
            string="bbox -1 -2 -3 -4",
            expected=(-1, -2, -3, -4)
        )

        # negative floats (not in spec)
        self.bbox_should_match(
            string="bbox -1.2 -2.4 -3.6 -4.8",
            expected=(-1, -2, -3, -4)
        )

        # too much whitespace (whitespace other than space is against spec)
        self.bbox_should_match(
            string="bbox  1   2 \t 3 \n 4",
            expected=(1, 2, 3, 4)
        )

        # surrounded by semi-colons
        self.bbox_should_match(
            string="foo;bbox 1 2 3 4;bar",
            expected=(1, 2, 3, 4)
        )

        # other stuff around (probably shouldn't match this)
        self.bbox_should_match(
            string="foo bbox 1 2 3 4 bar",
            expected=(1, 2, 3, 4)
        )

    def test_invalid_bboxes(self):
        self.bbox_should_not_match("")
        self.bbox_should_not_match("BBOX 1 2 3 4")
        self.bbox_should_not_match("bbox")
        self.bbox_should_not_match("bbox 1")
        self.bbox_should_not_match("bbox 1 2")
        self.bbox_should_not_match("bbox 1 2 3")
        self.bbox_should_not_match("bbox a 2 3 4")
        self.bbox_should_not_match("box 1 2 3 4")
        self.bbox_should_not_match("bbbox 1 2 3 4")
        self.bbox_should_not_match("bbox 1 2 3 4a")

    def bbox_should_match(self, string, expected):
        match = self.bbox_pattern.search(string)
        self.assertIsNotNone(match)

        result = (
            int(float(match.group(1))),
            int(float(match.group(2))),
            int(float(match.group(3))),
            int(float(match.group(4)))
        )

        self.assertEqual(result, expected)

    def bbox_should_not_match(self, string):
        match = self.bbox_pattern.search(string)
        self.assertIsNone(match)
