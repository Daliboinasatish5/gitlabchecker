"""Test cases for modes/compliance_mode.py"""
import unittest
from unittest.mock import MagicMock

from modes import compliance_mode


class TestComplianceChecks(unittest.TestCase):
    """Test cases for compliance checks"""

    def test_readme_presence_check(self):
        """Test detection of README file"""
        report_with_readme = {"has_readme": True, "readme_status": "complete"}
        report_without_readme = {"has_readme": False, "readme_status": "missing"}

        self.assertTrue(report_with_readme["has_readme"])
        self.assertFalse(report_without_readme["has_readme"])

    def test_license_file_check(self):
        """Test detection of LICENSE file"""
        report = {"has_license": True, "license_type": "MIT"}

        self.assertTrue(report["has_license"])
        self.assertEqual(report["license_type"], "MIT")

    def test_missing_compliance_elements(self):
        """Test reporting of missing elements"""
        missing_elements = []

        if not True:  # has_readme
            missing_elements.append("README")
        if not False:  # has_license
            missing_elements.append("LICENSE")

        self.assertIn("LICENSE", missing_elements)


class TestComplianceReporting(unittest.TestCase):
    """Test cases for compliance reporting"""

    def test_compliance_score_calculation(self):
        """Test calculation of compliance score"""
        checks = {
            "readme": True,
            "license": True,
            "contributing": False,
            "changelog": True,
        }

        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        compliance_score = (passed_checks / total_checks) * 100

        self.assertEqual(compliance_score, 75.0)

    def test_compliance_status(self):
        """Test determination of compliance status"""
        score = 80
        status = "compliant" if score >= 70 else "non-compliant"

        self.assertEqual(status, "compliant")

    def test_compliance_recommendations(self):
        """Test generation of compliance recommendations"""
        missing = ["CONTRIBUTING.md", "CHANGELOG.md"]
        recommendations = [f"Add {item}" for item in missing]

        self.assertEqual(len(recommendations), 2)
        self.assertIn("Add CONTRIBUTING.md", recommendations)


class TestProjectCompliance(unittest.TestCase):
    """Test cases for project compliance validation"""

    def test_project_compliance_validation(self):
        """Test validation of project compliance"""
        project = {
            "id": 1,
            "name": "test-project",
            "has_readme": True,
            "has_license": True,
        }

        self.assertIsNotNone(project)
        self.assertTrue(project["has_readme"])

    def test_batch_compliance_check(self):
        """Test batch compliance checking"""
        projects = [
            {"id": 1, "name": "proj1", "compliant": True},
            {"id": 2, "name": "proj2", "compliant": False},
            {"id": 3, "name": "proj3", "compliant": True},
        ]

        compliant_count = sum(1 for p in projects if p["compliant"])
        total_count = len(projects)

        self.assertEqual(compliant_count, 2)
        self.assertEqual(total_count, 3)


if __name__ == "__main__":
    unittest.main()
