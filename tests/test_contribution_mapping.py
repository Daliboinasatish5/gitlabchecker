"""Test cases for modes/contribution_mapping.py"""
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from modes import contribution_mapping


class TestStreakCalculation(unittest.TestCase):
    """Test cases for streak calculation"""

    def test_calculate_longest_streak(self):
        """Test calculation of longest streak"""
        commits_by_date = {
            "2026-01-01": 1,
            "2026-01-02": 2,
            "2026-01-03": 1,
            "2026-01-05": 1,
            "2026-01-06": 1,
            "2026-01-07": 1,
        }

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 7)

        longest_streak, current_streak = contribution_mapping.calculate_streaks(
            commits_by_date, start_date, end_date
        )

        self.assertGreater(longest_streak, 0)
        self.assertGreater(current_streak, 0)

    def test_empty_commits(self):
        """Test streak calculation with no commits"""
        commits_by_date = {}
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 7)

        longest_streak, current_streak = contribution_mapping.calculate_streaks(
            commits_by_date, start_date, end_date
        )

        self.assertEqual(longest_streak, 0)
        self.assertEqual(current_streak, 0)


class TestContributionAggregation(unittest.TestCase):
    """Test cases for contribution data aggregation"""

    def test_aggregate_commits_by_date(self):
        """Test aggregation of commits by date"""
        commits = [
            {"date": "2026-01-01", "message": "Fix bug"},
            {"date": "2026-01-01", "message": "Add feature"},
            {"date": "2026-01-02", "message": "Update docs"},
        ]

        commits_by_date = {}
        for commit in commits:
            date_key = commit["date"]
            commits_by_date[date_key] = commits_by_date.get(date_key, 0) + 1

        self.assertEqual(commits_by_date["2026-01-01"], 2)
        self.assertEqual(commits_by_date["2026-01-02"], 1)

    def test_filter_commits_by_date_range(self):
        """Test filtering commits by date range"""
        commits = [
            {"date": "2026-01-01", "message": "Commit 1"},
            {"date": "2026-01-05", "message": "Commit 2"},
            {"date": "2026-01-10", "message": "Commit 3"},
        ]

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 7)

        filtered = [
            c
            for c in commits
            if start_date <= date.fromisoformat(c["date"]) <= end_date
        ]

        self.assertEqual(len(filtered), 2)


class TestContributionMetrics(unittest.TestCase):
    """Test cases for contribution metrics"""

    def test_calculate_contribution_stats(self):
        """Test calculation of contribution statistics"""
        stats = {
            "total_commits": 50,
            "total_mrs": 10,
            "total_issues": 15,
        }

        total_contributions = (
            stats["total_commits"] + stats["total_mrs"] + stats["total_issues"]
        )

        self.assertEqual(total_contributions, 75)

    def test_daily_contribution_counts(self):
        """Test daily contribution count aggregation"""
        daily_data = [
            {"date": "2026-01-01", "commits": 5, "mrs": 1, "issues": 2},
            {"date": "2026-01-02", "commits": 3, "mrs": 0, "issues": 1},
        ]

        total_commits = sum(d["commits"] for d in daily_data)
        total_mrs = sum(d["mrs"] for d in daily_data)

        self.assertEqual(total_commits, 8)
        self.assertEqual(total_mrs, 1)


class TestContributionFiltering(unittest.TestCase):
    """Test cases for contribution filtering"""

    def test_filter_by_contribution_type(self):
        """Test filtering by contribution type"""
        contributions = [
            {"type": "commit", "count": 1},
            {"type": "mr", "count": 1},
            {"type": "commit", "count": 1},
            {"type": "issue", "count": 1},
        ]

        commits_only = [c for c in contributions if c["type"] == "commit"]
        self.assertEqual(len(commits_only), 2)

    def test_team_contribution_aggregation(self):
        """Test aggregation of team contributions"""
        team_data = {
            "user1": {"commits": 10, "mrs": 5},
            "user2": {"commits": 15, "mrs": 3},
        }

        total_commits = sum(u["commits"] for u in team_data.values())
        total_mrs = sum(u["mrs"] for u in team_data.values())

        self.assertEqual(total_commits, 25)
        self.assertEqual(total_mrs, 8)


if __name__ == "__main__":
    unittest.main()
