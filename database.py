import sqlite3
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from config import TIMEZONE_OFFSET

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_current_time(self) -> str:
        """Get current time in UTC+3"""
        return (datetime.utcnow() + TIMEZONE_OFFSET).strftime('%Y-%m-%d %H:%M:%S')

    def init_database(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Drop existing table to recreate with correct schema
                cursor.execute("DROP TABLE IF EXISTS user_stats")
                cursor.execute("""
                    CREATE TABLE user_stats (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        message_count INTEGER DEFAULT 0,
                        last_message_time TIMESTAMP,
                        is_banned BOOLEAN DEFAULT 0
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")

    def update_user_stats(self, user_id: int, username: str):
        try:
            current_time = self.get_current_time()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_stats (user_id, username, message_count, last_message_time, is_banned)
                    VALUES (?, ?, 1, ?, 0)
                    ON CONFLICT(user_id) DO UPDATE SET
                        message_count = message_count + 1,
                        last_message_time = ?,
                        username = ?
                        WHERE is_banned = 0
                """, (user_id, username, current_time, current_time, username))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error updating user stats: {e}")

    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, message_count, last_message_time, is_banned
                    FROM user_stats
                    WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        "username": result[0],
                        "message_count": result[1],
                        "last_message": result[2],
                        "is_banned": bool(result[3])
                    }
                return None
        except sqlite3.Error as e:
            logging.error(f"Error getting user stats: {e}")
            return None

    def get_top_users(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top users by message count, excluding banned users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, message_count
                    FROM user_stats
                    WHERE is_banned = 0
                    ORDER BY message_count DESC
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting top users: {e}")
            return []

    def get_activity_timeline(self, days: int = 7) -> List[Tuple[str, int, str]]:
        """Get activity timeline for the specified period, excluding banned users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get dates for the specified period
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                cursor.execute("""
                    SELECT username, COUNT(*) as msg_count, date(last_message_time) as msg_date
                    FROM user_stats
                    WHERE last_message_time >= ?
                    AND is_banned = 0
                    GROUP BY date(last_message_time)
                    ORDER BY msg_date DESC
                """, (start_date.strftime('%Y-%m-%d'),))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting activity timeline: {e}")
            return []

    def ban_user(self, user_id: int, ban: bool = True):
        """Ban or unban a user. When a user is banned:
        1. Their messages won't be counted in statistics
        2. They won't appear in top users list
        3. Their existing messages remain in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_stats
                    SET is_banned = ?
                    WHERE user_id = ?
                """, (1 if ban else 0, user_id))
                conn.commit()
                logging.info(f"User {user_id} {'banned' if ban else 'unbanned'} successfully")
        except sqlite3.Error as e:
            logging.error(f"Error {'banning' if ban else 'unbanning'} user: {e}")

    def reset_stats(self):
        """Reset all statistics while preserving ban status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Обнуляем счетчик сообщений и время последнего сообщения
                cursor.execute("""
                    UPDATE user_stats 
                    SET message_count = 0, 
                        last_message_time = NULL 
                    WHERE is_banned = 0
                """)
                affected_rows = cursor.rowcount
                conn.commit()
                logging.info(f"Successfully reset stats for {affected_rows} users")
                return True
        except sqlite3.Error as e:
            logging.error(f"Error resetting stats: {e}")
            return False

    def export_stats_to_csv(self) -> Optional[bytes]:
        """Export statistics to CSV format including ban status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, message_count, last_message_time, is_banned
                    FROM user_stats
                    ORDER BY message_count DESC
                """)
                rows = cursor.fetchall()

                if not rows:
                    return None

                import io
                import csv
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['user_id', 'username', 'message_count', 'last_message_time', 'is_banned'])
                writer.writerows(rows)

                return output.getvalue().encode('utf-8')
        except sqlite3.Error as e:
            logging.error(f"Error exporting stats: {e}")
            return None

    def get_all_users(self) -> List[Tuple[int, str]]:
        """Get all users from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username
                    FROM user_stats
                    WHERE is_banned = 0
                    ORDER BY message_count DESC
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting all users: {e}")
            return []