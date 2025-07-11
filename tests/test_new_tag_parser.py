import unittest
from parsing import parse_tags

class TestParseTags(unittest.TestCase):

    def test_single_line_wikilinks(self):
        content = "Tags: [[Tag1]], [[Tag2]]"
        self.assertEqual(parse_tags(content), ['[[Tag1]]', '[[Tag2]]'])

    def test_multiline_wikilinks(self):
        content = "Tags: [[Tag1]]\n[[Tag2]]"
        self.assertEqual(parse_tags(content), ['[[Tag1]]\n[[Tag2]]'])

    def test_termination_by_heading(self):
        content = "Tags: [[Tag1]]\n# Heading"
        self.assertEqual(parse_tags(content), ['[[Tag1]]'])

    def test_termination_by_non_wikilink(self):
        content = "Tags: [[Tag1]]\nSome other text"
        self.assertEqual(parse_tags(content), ['[[Tag1]]'])

    def test_no_tags(self):
        content = "Tags: "
        self.assertEqual(parse_tags(content), [])

    def test_no_tags_line(self):
        content = "Just some text without a tags line."
        self.assertEqual(parse_tags(content), [])

    def test_tags_with_aliases(self):
        content = "Tags: [[RealTag|Alias]]"
        self.assertEqual(parse_tags(content), ['[[RealTag|Alias]]'])

    def test_duplicate_tags(self):
        content = "Tags: [[Tag1]], [[Tag1]]"
        self.assertEqual(parse_tags(content), ['[[Tag1]]', '[[Tag1]]'])

if __name__ == '__main__':
    unittest.main()
