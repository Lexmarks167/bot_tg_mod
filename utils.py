from typing import List, Dict
from datetime import datetime

def format_user_stats(stats: dict) -> str:
    """Format user statistics for display"""
    if not stats:
        return "Статистика не найдена."

    return (f"📊 Статистика пользователя @{stats['username']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📝 Всего сообщений: {stats['message_count']}\n"
            f"🕒 Последнее сообщение: {stats['last_message']}\n"
            f"━━━━━━━━━━━━━━━")

def format_top_users(stats: Dict[str, List], limit: int = 10) -> str:
    """Format top users statistics for display"""
    if not stats or not stats.get('all_time'):
        return "📊 Нет данных о сообщениях."

    result = "📊 Общая статистика сообщений\n"
    result += "━━━━━━━━━━━━━━━\n\n"
    result += "🏆 Топ активных пользователей:\n"

    for i, (username, count) in enumerate(stats['all_time'][:limit], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
        result += f"{medal} {i}. @{username}: {count} сообщений\n"

    if 'daily' in stats and stats['daily']:
        result += "\n📅 Статистика за сегодня:\n"
        result += "━━━━━━━━━━━━━━━\n"
        for i, (username, count) in enumerate(stats['daily'][:limit], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
            result += f"{medal} {i}. @{username}: {count} сообщений\n"

    return result

def format_staff_stats(stats: List[Dict]) -> str:
    """Format staff statistics for display"""
    if not stats:
        return "📊 Нет данных о сообщениях персонала."

    result = "👥 Детальная статистика пользователей\n"
    result += "━━━━━━━━━━━━━━━\n\n"

    for i, stat in enumerate(stats, 1):
        result += (f"{i}. 👤 @{stat['username']}\n"
                  f"   📝 Всего сообщений: {stat['message_count']}\n"
                  f"   🕒 Последняя активность: {stat['last_message']}\n"
                  f"   ━━━━━━━━━━━━━━━\n")

    return result

def is_admin(user_id: int, admin_ids: List[int]) -> bool:
    """Check if user is an admin"""
    return user_id in admin_ids