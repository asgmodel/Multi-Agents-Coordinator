import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class SkillsShCompatibilityTest(unittest.TestCase):
    def test_public_standard_skill_location_and_frontmatter(self):
        files = list(SKILLS.glob("*/SKILL.md"))
        self.assertEqual([f.parent.name for f in files], ["multi-agent-project-coordinator"])
        for file in files:
            source = file.read_text(encoding="utf-8")
            self.assertTrue(source.startswith("---\n"))
            parts = source.split("---\n", 2)
            self.assertEqual(len(parts), 3)
            header, body = parts[1], parts[2]
            meta = dict(re.findall(r"^([a-z]+):\s*(.+)$", header, flags=re.MULTILINE))
            self.assertEqual(meta.get("name"), file.parent.name)
            self.assertGreater(len(meta.get("description", "")), 40)
            self.assertTrue(body.strip())
            self.assertNotIn("metadata.internal", header)

    def test_no_root_skill_that_shadows_nested_discovery(self):
        self.assertFalse((ROOT / "SKILL.md").exists())
        self.assertFalse((ROOT / ".github/skills").exists())


if __name__ == "__main__":
    unittest.main()
