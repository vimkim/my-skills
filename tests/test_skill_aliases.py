from pathlib import Path
import unittest

SKILLS = Path(__file__).resolve().parents[1] / 'skills'


def body(name):
    return (SKILLS / name / 'SKILL.md').read_text().split('\n---\n', 1)[1]


class SkillAliases(unittest.TestCase):
    def test_musk_repeats_decide(self):
        self.assertEqual(body('musk'), body('decide'), 'edit skills/musk/SKILL.md together with skills/decide/SKILL.md')
