import matplotlib.pyplot as plt
import io
from typing import List, Tuple
from datetime import datetime, timedelta

class GraphGenerator:
    @staticmethod
    def generate_activity_graph(data: List[Tuple[str, int]], title: str = "User Activity") -> bytes:
        """Generate a bar graph of user activity"""
        plt.figure(figsize=(10, 6))
        plt.clf()

        usernames = [item[0] for item in data]
        counts = [item[1] for item in data]

        plt.bar(usernames, counts)
        plt.title(title)
        plt.xlabel("Пользователи")
        plt.ylabel("Количество сообщений")

        # Rotate labels for better readability
        plt.xticks(rotation=45, ha='right')

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf.getvalue()

    @staticmethod
    def generate_timeline_graph(data: List[Tuple[str, int, str]], period_days: int = 7) -> bytes:
        """Generate a line graph showing activity over time"""
        plt.figure(figsize=(10, 6))
        plt.clf()

        # Create timeline data
        timeline = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Initialize timeline with zeros
        current_date = start_date
        while current_date <= end_date:
            timeline[current_date.strftime('%Y-%m-%d')] = 0
            current_date += timedelta(days=1)

        # Fill in actual data
        for _, count, date_str in data:
            if date_str in timeline:
                timeline[date_str] = count

        dates = list(timeline.keys())
        counts = list(timeline.values())

        plt.plot(dates, counts, marker='o')
        plt.title("Активность за период")
        plt.xlabel("Дата")
        plt.ylabel("Количество сообщений")

        # Rotate date labels
        plt.xticks(rotation=45, ha='right')

        # Adjust layout
        plt.tight_layout()

        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf.getvalue()