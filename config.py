import os
from datetime import timedelta

# Bot configuration
BOT_TOKEN = "7984172523:AAGmpKpt2iwY9weAAFDKgc9GaFm5BKUvrj8"

# User access lists
ALLOWED_USERS = [1627702114, 7261404992, 1991533921, 5825174093, 1220910064, 6149704332, 7803169645]
ADMIN_USERS = [1627702114, 7261404992, 6149704332, 1492862809]  # Список администраторов

# Database configuration
MAIN_DB_PATH = "stats.db"
DAILY_DB_PATH = "daily_stats.db"

# Timezone configuration (UTC+3)
TIMEZONE_OFFSET = timedelta(hours=3)

# Message templates
MESSAGES = {
    "start": "👋 Привет! Я бот для отслеживания активности пользователей в чате.\n\n"
            "📊 Доступные команды:\n"
            "/stats - Посмотреть свою статистику\n"
            "/topusers - Посмотреть общую статистику пользователей\n"
            "\n👑 Команды для администраторов:\n"
            "/staff_stats - Детальная статистика пользователей\n"
            "/staff_all - Полная статистика всех пользователей\n"
            "/staff_off - Сбросить ежедневную статистику\n"
            "\nСтатистика автоматически обновляется каждые 24 часа в полночь (UTC+3).",
    "unauthorized": "❌ У вас нет прав для выполнения этой команды.",
    "not_allowed": "❌ У вас нет доступа к этому боту.",
    "not_admin": "❌ Для работы в группе мне нужны права администратора.",
    "admin_only": "❌ Эта команда доступна только администраторам."
}