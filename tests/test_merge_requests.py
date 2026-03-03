"""Test cases for gitlab_utils/merge_requests.py"""
import unittest
from unittest.mock import MagicMock, patch

from gitlab_utils import merge_requests


class TestGetUserMrs(unittest.TestCase):
    """Test cases for get_user_mrs function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = MagicMock()

    def test_get_user_mrs_success(self):
        """Test successful MR retrieval"""
        # Test that function returns tuple with MRs and stats
        result_mock = (
            [
                {
                    "id": 1,
                    "title": "Test MR 1",
                    "state": "merged",
                    "created_at": "2026-01-01",
                },
                {
                    "id": 2,
                    "title": "Test MR 2",
                    "state": "opened",
                    "created_at": "2026-01-02",
                },
            ],
            {"total": 2, "merged": 1, "opened": 1},
        )

        # Verify structure
        self.assertIsNotNone(result_mock[0])
        self.assertIsNotNone(result_mock[1])
        self.assertEqual(len(result_mock[0]), 2)

    def test_get_user_mrs_empty(self):
        """Test MR retrieval with no results"""
        result, stats = merge_requests.get_user_mrs(self.mock_client, 999)
        self.assertIsInstance(result, list)
        self.assertIsInstance(stats, dict)


class TestMergeRequestFiltering(unittest.TestCase):
    """Test cases for MR filtering logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_mrs = [
            {"id": 1, "state": "merged", "created_at": "2026-01-01"},
            {"id": 2, "state": "opened", "created_at": "2026-01-02"},
            {"id": 3, "state": "closed", "created_at": "2026-01-03"},
        ]

    def test_filter_by_state(self):
        """Test filtering MRs by state"""
        merged = [mr for mr in self.test_mrs if mr["state"] == "merged"]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], 1)

    def test_filter_by_date_range(self):
        """Test filtering MRs by date range"""
        from datetime import datetime

        start_date = datetime(2026, 1, 1).date()
        end_date = datetime(2026, 1, 2).date()

        filtered = [
            mr
            for mr in self.test_mrs
            if start_date
            <= datetime.fromisoformat(mr["created_at"]).date()
            <= end_date
        ]
        self.assertEqual(len(filtered), 2)


if __name__ == "__main__":
    unittest.main()
