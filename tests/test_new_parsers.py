import unittest
from parsing import parse_datetime, parse_references, parse_tags
from datetime import datetime

class TestNewParsingFunctions(unittest.TestCase):

    def test_parse_datetime(self):
        content = "07-10-2025\n19:22\n\nReference:\n\nTags:"
        self.assertEqual(parse_datetime(content), datetime(2025, 7, 10, 19, 22))

    def test_parse_references_single(self):
        content = "Reference: http://example.com\nTags:"
        self.assertEqual(parse_references(content), ["http://example.com"])

    def test_parse_references_multiple_comma(self):
        content = "Reference: http://example.com, http://example2.com\nTags:"
        self.assertEqual(parse_references(content), ["http://example.com", "http://example2.com"])

    def test_parse_references_multiple_newline(self):
        content = "Reference: http://example.com\nhttp://example2.com\nTags:"
        self.assertEqual(parse_references(content), ["http://example.com", "http://example2.com"])

    def test_parse_tags_single(self):
        content = "Tags: tag1"
        self.assertEqual(parse_tags(content), ["tag1"])

    def test_parse_tags_multiple(self):
        content = "Tags: tag1, tag2, tag3"
        self.assertEqual(parse_tags(content), ["tag1", "tag2", "tag3"])

if __name__ == '__main__':
    unittest.main()

