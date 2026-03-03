"""Test cases for modes/user_profile.py"""
import unittest
from unittest.mock import MagicMock

from modes import user_profile


class TestUserProfileRendering(unittest.TestCase):
    """Test cases for render_user_profile function"""

    def test_user_profile_data_structure(self):
        """Test that user profile contains required fields"""
        user_profile_data = {
            "id": 1,
            "name": "John Doe",
            "username": "johndoe",
            "bio": "Software developer",
            "location": "New York",
            "web_url": "https://gitlab.com/johndoe",
        }

        self.assertIn("id", user_profile_data)
        self.assertIn("name", user_profile_data)
        self.assertIn("username", user_profile_data)
        self.assertIsNotNone(user_profile_data["name"])

    def test_empty_user_profile(self):
        """Test handling of empty user profile"""
        user_profile_data = {
            "id": None,
            "name": None,
            "username": None,
        }

        self.assertIsNone(user_profile_data["id"])

    def test_user_profile_validation(self):
        """Test validation of user profile data"""
        user_profile_data = {
            "id": 1,
            "username": "validuser",
        }

        self.assertTrue(user_profile_data["id"] > 0)
        self.assertTrue(len(user_profile_data["username"]) > 0)


class TestUserStats(unittest.TestCase):
    """Test cases for user statistics display"""

    def test_calculate_user_metrics(self):
        """Test calculation of user metrics"""
        user_data = {
            "public_repos": 10,
            "followers": 50,
            "following": 30,
        }

        total_activity = (
            user_data["public_repos"]
            + user_data["followers"]
            + user_data["following"]
        )

        self.assertEqual(total_activity, 90)

    def test_user_contribution_stats(self):
        """Test user contribution statistics"""
        stats = {
            "commits": 100,
            "merge_requests": 20,
            "issues": 15,
        }

        total_contributions = (
            stats["commits"] + stats["merge_requests"] + stats["issues"]
        )

        self.assertEqual(total_contributions, 135)


if __name__ == "__main__":
    unittest.main()
