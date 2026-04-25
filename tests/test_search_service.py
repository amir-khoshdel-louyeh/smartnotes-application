import unittest

from services.search_service import SearchService


class TestSearchService(unittest.TestCase):
    def test_replace_all_case_insensitive(self):
        original = "Hello World hello world"
        updated, count = SearchService.replace_all(original, "hello", "hi", case_sensitive=False)

        self.assertEqual(updated, "hi World hi world")
        self.assertEqual(count, 2)

    def test_replace_all_case_sensitive(self):
        original = "Hello World hello world"
        updated, count = SearchService.replace_all(original, "hello", "hi", case_sensitive=True)

        self.assertEqual(updated, "Hello World hi world")
        self.assertEqual(count, 1)

    def test_replace_all_no_query_returns_same_text(self):
        original = "Hello World"
        updated, count = SearchService.replace_all(original, "", "hi")

        self.assertEqual(updated, original)
        self.assertEqual(count, 0)
