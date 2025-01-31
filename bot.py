import logging
import threading
import time
from telegram import Update, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import schedule # Added import for scheduler

from config import BOT_TOKEN, ALLOWED_USERS, ADMIN_USERS, MESSAGES
from stats_handler import StatsHandler
from utils import format_user_stats, format_top_users, format_staff_stats, is_admin

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize stats handler
stats_handler = StatsHandler()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text(MESSAGES["not_allowed"])
        return
    await update.message.reply_text(MESSAGES["start"])

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stats command"""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text(MESSAGES["not_allowed"])
        return

    stats = stats_handler.get_user_stats(user_id)
    # Форматируем статистику для одного пользователя
    formatted_stats = {
        'username': stats.get('username', 'Unknown'),
        'message_count': stats.get('total_messages', 0),
        'last_message': stats.get('last_message', 'Never')
    }
    await update.message.reply_text(format_user_stats(formatted_stats))

async def topusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /topusers command - shows statistics for all allowed users"""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text(MESSAGES["not_allowed"])
        return

    top_stats = stats_handler.get_top_users(10)  # Get top 10 users
    logger.info(f"Retrieved top stats: {top_stats}")  # Add logging for debugging

    # Проверяем наличие данных перед форматированием
    if not top_stats or (not top_stats.get('all_time') and not top_stats.get('daily')):
        await update.message.reply_text("📊 Пока нет данных о сообщениях.")
        return

    formatted_stats = format_top_users(top_stats)
    logger.info(f"Formatted stats: {formatted_stats}")  # Add logging for debugging
    await update.message.reply_text(formatted_stats)

async def staff_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /staff_stats command - shows statistics for staff members"""
    user_id = update.effective_user.id

    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id, ADMIN_USERS):
        await update.message.reply_text(MESSAGES["admin_only"])
        return

    # Добавляем логирование для отладки
    logger.info(f"Staff stats requested by admin {user_id}")

    # Получаем статистику для всех разрешенных пользователей
    staff_stats = []
    for allowed_user_id in ALLOWED_USERS:
        stats = stats_handler.get_user_stats(allowed_user_id)
        if stats:
            staff_stats.append({
                'username': stats.get('username', 'Unknown'),
                'message_count': stats.get('total_messages', 0),
                'last_message': stats.get('last_message', 'Never')
            })
            logger.info(f"Retrieved stats for user {allowed_user_id}: {stats}")

    # Сортируем по количеству сообщений
    staff_stats.sort(key=lambda x: x['message_count'], reverse=True)

    # Форматируем и отправляем статистику
    formatted_stats = format_staff_stats(staff_stats)
    logger.info(f"Formatted staff stats: {formatted_stats}")
    await update.message.reply_text(formatted_stats)

    # Сбрасываем ежедневную статистику после отображения
    # logger.info(f"Resetting daily stats after staff_stats command by admin {user_id}")
    # if stats_handler.reset_daily_stats():
    #     await update.message.reply_text("📊 Ежедневная статистика успешно сброшена")
    #     logger.info("Daily statistics reset successful")
    # else:
    #     await update.message.reply_text("❌ Ошибка при сбросе статистики")
    #     logger.error("Failed to reset daily statistics")

async def staff_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /staff_all command - shows complete statistics for all users"""
    user_id = update.effective_user.id

    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id, ADMIN_USERS):
        await update.message.reply_text(MESSAGES["admin_only"])
        return

    logger.info(f"Complete stats requested by admin {user_id}")

    # Получаем полную статистику для всех пользователей
    complete_stats = stats_handler.get_all_stats()

    if not complete_stats:
        await update.message.reply_text("📊 Нет данных о сообщениях.")
        return

    # Сортируем по общему количеству сообщений
    complete_stats.sort(key=lambda x: x['total_messages'], reverse=True)

    # Форматируем статистику
    formatted_stats = "📊 Полная статистика всех пользователей\n"
    formatted_stats += "━━━━━━━━━━━━━━━\n\n"

    for i, stat in enumerate(complete_stats, 1):
        daily_msg = stat.get('daily_messages', 0)
        formatted_stats += (
            f"{i}. 👤 @{stat['username']}\n"
            f"   📝 Всего сообщений: {stat['total_messages']}\n"
            f"   📅 Сообщений за день: {daily_msg}\n"
            f"   🕒 Последняя активность: {stat['last_message']}\n"
            f"   ━━━━━━━━━━━━━━━\n"
        )

    await update.message.reply_text(formatted_stats)

async def staff_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /staff_off command - manually reset daily statistics"""
    user_id = update.effective_user.id

    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id, ADMIN_USERS):
        await update.message.reply_text(MESSAGES["admin_only"])
        return

    logger.info(f"Manual daily stats reset requested by admin {user_id}")
    if stats_handler.reset_daily_stats():
        await update.message.reply_text("📊 Ежедневная статистика успешно сброшена")
        logger.info("Daily statistics reset successful")
    else:
        await update.message.reply_text("❌ Ошибка при сбросе статистики")
        logger.error("Failed to reset daily statistics")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if not update.effective_user:
        return

    user = update.effective_user
    chat = update.effective_chat

    logger.info(f"Received message from user {user.id} ({user.username or user.first_name}) in chat {chat.id} ({chat.type})")

    # Check if user is in allowed list
    if user.id not in ALLOWED_USERS:
        logger.info(f"Message from unauthorized user {user.id}, ignoring")
        return

    # For private chats
    if chat.type == 'private':
        logger.info(f"Processing private message from allowed user {user.id}")
        stats_handler.update_stats(user.id, user.username or user.first_name)
        return

    # For groups/supergroups
    if chat.type in ['group', 'supergroup']:
        try:
            # Check if bot is admin in the group
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            logger.info(f"Bot status in group {chat.id}: {bot_member.status}")

            if isinstance(bot_member, (ChatMemberAdministrator, ChatMemberOwner)):
                logger.info(f"Processing message from allowed user {user.id} in group {chat.id}")
                stats_handler.update_stats(user.id, user.username or user.first_name)
                logger.info(f"Successfully updated stats for user {user.id}")
            else:
                logger.warning(f"Bot is not admin in group {chat.id}")
                await update.message.reply_text(MESSAGES["not_admin"])
        except Exception as e:
            logger.error(f"Error checking bot status in group: {e}")

def main():
    """Start the bot"""
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("topusers", topusers_command))
        application.add_handler(CommandHandler("staff_stats", staff_stats_command))
        application.add_handler(CommandHandler("staff_all", staff_all_command))
        application.add_handler(CommandHandler("staff_off", staff_off_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start scheduler in a separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        # Start polling
        logger.info("Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()