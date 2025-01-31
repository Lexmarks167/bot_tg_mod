from typing import Dict, List, Tuple, Optional
import logging
from database import Database
from config import MAIN_DB_PATH, DAILY_DB_PATH, TIMEZONE_OFFSET
from graph_generator import GraphGenerator
import schedule
import time
from datetime import datetime, timedelta

class StatsHandler:
    def __init__(self):
        self.main_db = Database(MAIN_DB_PATH)
        self.daily_db = Database(DAILY_DB_PATH)
        self.graph_generator = GraphGenerator()
        self._setup_daily_reset()

    def _get_next_reset_time(self) -> str:
        """Calculate next reset time in UTC+3"""
        now = datetime.utcnow() + TIMEZONE_OFFSET
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        reset_time = (next_day - TIMEZONE_OFFSET).strftime('%H:%M')
        return reset_time

    def _setup_daily_reset(self):
        """Setup daily statistics reset at midnight UTC+3"""
        reset_time = self._get_next_reset_time()
        schedule.every().day.at(reset_time).do(self.reset_daily_stats)
        logging.info(f"Daily reset scheduled for {reset_time} UTC")

    def generate_activity_graph(self, is_daily: bool = False) -> Optional[bytes]:
        """Generate activity graph for top users"""
        try:
            db = self.daily_db if is_daily else self.main_db
            data = db.get_top_users(10)
            title = "Ежедневная активность" if is_daily else "Общая активность"
            return self.graph_generator.generate_activity_graph(data, title)
        except Exception as e:
            logging.error(f"Error generating activity graph: {e}")
            return None

    def generate_timeline_graph(self, days: int = 7) -> Optional[bytes]:
        """Generate timeline graph for the specified period"""
        try:
            data = self.main_db.get_activity_timeline(days)
            return self.graph_generator.generate_timeline_graph(data, days)
        except Exception as e:
            logging.error(f"Error generating timeline graph: {e}")
            return None

    def update_stats(self, user_id: int, username: str):
        """Update both main and daily statistics for a user"""
        try:
            self.main_db.update_user_stats(user_id, username)
            self.daily_db.update_user_stats(user_id, username)
        except Exception as e:
            logging.error(f"Error updating stats: {e}")

    def get_user_stats(self, user_id: int, include_daily: bool = True) -> Dict:
        """Get combined statistics for a user"""
        try:
            main_stats = self.main_db.get_user_stats(user_id)
            daily_stats = self.daily_db.get_user_stats(user_id) if include_daily else None

            if main_stats:
                stats = {
                    "username": main_stats["username"],
                    "total_messages": main_stats["message_count"],
                    "last_message": main_stats["last_message"],
                    "is_banned": main_stats.get("is_banned", False)
                }
                if daily_stats:
                    stats["daily_messages"] = daily_stats["message_count"]
                return stats
            return {
                "username": "Unknown",
                "total_messages": 0,
                "daily_messages": 0 if include_daily else None,
                "last_message": "Never",
                "is_banned": False
            }
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return {
                "username": "Error",
                "total_messages": 0,
                "daily_messages": 0 if include_daily else None,
                "last_message": "Error",
                "is_banned": False
            }

    def get_top_users(self, limit: int = 10) -> Dict[str, List]:
        """Get top users for both all-time and daily statistics"""
        try:
            return {
                "all_time": self.main_db.get_top_users(limit),
                "daily": self.daily_db.get_top_users(limit)
            }
        except Exception as e:
            logging.error(f"Error getting top users: {e}")
            return {"all_time": [], "daily": []}

    def get_all_stats(self) -> List[Dict]:
        """Get complete statistics for all users"""
        try:
            all_users = set()
            main_stats = self.main_db.get_all_users()
            daily_stats = self.daily_db.get_all_users()

            # Combine user IDs from both databases
            for stats in [main_stats, daily_stats]:
                for user_id, _ in stats:
                    all_users.add(user_id)

            # Get complete stats for each user
            complete_stats = []
            for user_id in all_users:
                stats = self.get_user_stats(user_id)
                if stats:
                    complete_stats.append(stats)

            return complete_stats
        except Exception as e:
            logging.error(f"Error getting all stats: {e}")
            return []

    def reset_daily_stats(self):
        """Reset daily statistics"""
        try:
            if self.daily_db.reset_stats():
                logging.info("Daily statistics reset successfully")
                return True
            else:
                logging.error("Failed to reset daily statistics")
                return False
        except Exception as e:
            logging.error(f"Error resetting daily stats: {e}")
            return False

    def export_stats(self) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Export statistics to CSV format"""
        try:
            return (
                self.main_db.export_stats_to_csv(),
                self.daily_db.export_stats_to_csv()
            )
        except Exception as e:
            logging.error(f"Error exporting stats: {e}")
            return None, None