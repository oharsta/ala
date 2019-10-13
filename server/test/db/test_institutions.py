import unittest

from server.db.institutions import metadata


class TestEducations(unittest.TestCase):

    def test_educations(self):
        res = metadata()
        self.assertEqual(2, len(res))
