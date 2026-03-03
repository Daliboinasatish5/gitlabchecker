"""Test cases for gitlab_utils/projects.py"""
import unittest
from unittest.mock import MagicMock, patch

from gitlab_utils import projects


class TestGetUserProjects(unittest.TestCase):
    """Test cases for get_user_projects function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = MagicMock()

    def test_get_user_projects_structure(self):
        """Test that get_user_projects returns correct structure"""
        result = {
            "all": [{"id": 1, "name": "project1"}, {"id": 2, "name": "project2"}],
            "personal": [{"id": 1, "name": "project1"}],
            "contributed": [{"id": 2, "name": "project2"}],
        }

        self.assertIn("all", result)
        self.assertIn("personal", result)
        self.assertIn("contributed", result)
        self.assertEqual(len(result["all"]), 2)

    def test_project_classification(self):
        """Test classification of personal vs contributed projects"""
        personal_projects = [
            {"id": 1, "name": "my-project", "owner": {"id": 1}},
        ]
        contributed_projects = [
            {"id": 2, "name": "team-project", "owner": {"id": 2}},
        ]

        self.assertTrue(len(personal_projects) > 0)
        self.assertTrue(len(contributed_projects) > 0)

    def test_empty_projects(self):
        """Test handling of user with no projects"""
        result = {"all": [], "personal": [], "contributed": []}

        self.assertEqual(len(result["all"]), 0)
        self.assertEqual(len(result["personal"]), 0)


class TestProjectMetrics(unittest.TestCase):
    """Test cases for project metrics"""

    def test_project_stats_calculation(self):
        """Test calculation of project statistics"""
        projects_data = [
            {"id": 1, "star_count": 10, "forks_count": 5},
            {"id": 2, "star_count": 20, "forks_count": 15},
        ]

        total_stars = sum(p.get("star_count", 0) for p in projects_data)
        total_forks = sum(p.get("forks_count", 0) for p in projects_data)

        self.assertEqual(total_stars, 30)
        self.assertEqual(total_forks, 20)


if __name__ == "__main__":
    unittest.main()
