"""News portrait ordering must not alter publication authors or caller data."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("site_build", Path(__file__).parents[1] / "tools" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def person(tag, name, current=True):
    return dict(tag=tag, name=name, current=current, url=None, slug=tag,
                photo="group_profile/" + tag + ".jpg")


class NewsFaceOrderTests(unittest.TestCase):
    def setUp(self):
        self.a = person("alpha", "Alpha")
        self.b = person("beta", "Beta")
        self.c = person("gamma", "Gamma")
        self.n = person("namhoonlee", "Namhoon Lee")

    def test_namhoon_last_and_input_unchanged(self):
        people = [self.a, self.n, self.b]
        result = str(build.news_faces(people, 3))
        self.assertIn('aria-label="Alpha, Beta, Namhoon Lee"', result)
        self.assertLess(result.index('title="Beta"'), result.index('title="Namhoon Lee"'))
        self.assertEqual([p["tag"] for p in people], ["alpha", "namhoonlee", "beta"])

    def test_other_people_keep_order(self):
        self.assertIn('aria-label="Beta, Alpha"', str(build.news_faces([self.b, self.a], 3)))

    def test_overflow_keeps_namhoon_visible_last_and_filters_alumni(self):
        old = person("alumnus", "Alumnus", current=False)
        result = str(build.news_faces([self.a, self.n, old, self.b, self.c], 3))
        self.assertIn('aria-label="Alpha, Beta, Gamma, Namhoon Lee"', result)
        self.assertIn('>+2</span>', result)
        self.assertNotIn('Alumnus', result)
        self.assertIn('src="group_profile/namhoonlee.jpg"', result)
        self.assertLess(result.index('>+2</span>'), result.index('title="Namhoon Lee"'))
        self.assertEqual(result.count('class="member-face'), 3)

    def test_single_slot_keeps_namhoon_visible(self):
        result = str(build.news_faces([self.a, self.n, self.b], 1))
        self.assertIn('src="group_profile/namhoonlee.jpg"', result)
        self.assertEqual(result.count('class="member-face'), 1)

    def test_overflow_without_namhoon_unchanged(self):
        result = str(build.news_faces([self.a, self.b, self.c], 2))
        self.assertIn('title="Alpha"', result)
        self.assertIn('>+2</span>', result)

    def test_only_namhoon_or_no_people(self):
        self.assertIn('title="Namhoon Lee"', str(build.news_faces([self.n], 3)))
        self.assertEqual(str(build.news_faces([], 3)), "")


if __name__ == "__main__":
    unittest.main()
