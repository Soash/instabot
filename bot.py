import logging, re, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from scrapper import check_if_liked
from dotenv import load_dotenv

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

from database import (
    init_db, 
    increment_score,
    decrement_score,
    get_user_score, 
    get_leaderboard, 
    save_link, 
    load_links, 
    set_username, 
    get_username, 
    has_liked, 
    save_user_like, 
    get_link_by_id, 
    get_total_score
)





load_dotenv()

# === Config ===
# BOT_TOKEN = os.environ["BOT_TOKEN"]
# TARGET_GROUP_ID = os.environ["GROUP_ID"]
# BOT_USERNAME = os.environ["BOT_USERNAME"]
# GROUP_LINK = os.environ["GROUP_LINK"]

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
TARGET_GROUP_ID = int(os.getenv("GROUP_ID"))


GROUP_LINK = os.getenv("GROUP_LINK")

INSTAGRAM_PATTERN = r'(https?:\/\/(?:www\.)?instagram\.com\/(?:p|reel|tv)\/[a-zA-Z0-9_\-]+\/?)|(https?:\/\/(?:www\.)?instagr\.am\/(?:p|reel|tv)\/[a-zA-Z0-9_\-]+\/?)'

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

COOKIES_FILE_PATH = "cookies.json"

# === Command Handlers ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return

    param = context.args[0] if context.args else None

    if param == "queue":
        await queue(update, context)
    elif param == "rules":
        await show_rules(update, context)
    else:
        await show_welcome(update)

async def show_welcome(update: Update):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    msg = (
        "🌟 Welcome to the Instagram Link Bot! 🌟\n\n"
        "📋 Available commands:\n"
        "• /start - Show welcome message\n"
        "• /help - Show this help menu\n"
        "• /rules - Show rules\n"
        "• /queue - Show last 7 shared links\n"
        "• /status - Show your score and username\n"
        "• /leaderboard - See the top sharers\n"
        "• /username <your_IG_username> - Set your Instagram username\n"
        "• /done <link_number> - Mark a post as liked\n\n"
        "💡 Tip: Share links, engage with others, and climb the leaderboard!"
    )

    keyboard = [[
        InlineKeyboardButton("🔗 Join Group", url=GROUP_LINK)
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(msg, reply_markup=markup)

async def set_instagram_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    user = update.message.from_user
    if len(context.args) == 1:
        username = context.args[0]
        set_username(user.id, username)
        await update.message.reply_text(f"✅ Your Instagram username ({username}) has been saved!")
    else:
        await update.message.reply_text("❌ Please provide your Instagram username (e.g., /username ironman).")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    if len(context.args) == 1 and context.args[0].isdigit():
        link_id = int(context.args[0])
        user = update.message.from_user
        user_id = user.id
        username = get_username(user_id)

        if not username:
            await update.message.reply_text(
                "❌ You need to set your Instagram username first using /username <your_instagram_username>."
            )
            return

        # Get link by ID
        link_data = get_link_by_id(link_id)
        if not link_data:
            await update.message.reply_text("❌ Invalid link ID.")
            return

        link = link_data["link"]

        # Check if already marked as liked
        if has_liked(user_id, link_id):
            await update.message.reply_text("✅ You've already marked this link as liked.")
            return

        # Call your async scraper to check if they actually liked it
        liked = await check_if_liked(username, link)

        if liked:
            save_user_like(user_id, link_id)
            increment_score(user_id, username)
            await update.message.reply_text("✅ You liked this post! Score +1.")
        else:
            await update.message.reply_text("❌ You have not liked this post.")
    else:
        await update.message.reply_text("❌ Please provide a valid link ID (e.g., /done 12).")

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    msg = (
        "📜 Rules:\n\n"
        "1. Share only Instagram links.\n"
        "2. Be respectful to others.\n"
        "3. Follow the group guidelines."
    )
    await update.message.reply_text(msg)

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    if update.message:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        chat_id = user_id
        await context.bot.answer_callback_query(update.callback_query.id)
    else:
        return

    all_links = load_links(user_id)
    links = [item for item in all_links if item.get('user_id') != user_id]
    
    if not links:
        text = "📭 <b>No unliked Instagram links available.</b>"
    else:
        text = "📋 <b>Recent Instagram Links</b>\nYou need to /done as soon as possible after engaging (within 5 min). Only love react will count as engage.\n\n"
        for item in links:
            text += (
                f"🔗 <b>ID:</b> <code>{item['id']}</code>\n"
                f"📎 <a href=\"{item['link']}\">{item['link']}</a>\n\n"
            )

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    """Command to display the leaderboard of top 5 users based on total_score."""
    leaderboard_data = get_leaderboard()

    if leaderboard_data:
        text = "🏆 <b>Top 5 Users</b> (Total Score)\n\n"
        for idx, (username, total_score) in enumerate(leaderboard_data, start=1):
            text += f"{idx}. <b>{username}</b> - <b>{total_score}</b> points\n"
    else:
        text = "❌ No users found in the leaderboard."

    # Send the leaderboard message
    await update.message.reply_text(text, parse_mode="HTML")
    
async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    user = update.message.from_user
    score = get_user_score(user.id)
    total_score = get_total_score(user.id)
    username = get_username(user.id)

    msg = f"📊 Your current score is: {score} point{'s' if score != 1 else ''}.\n"
    msg += f"🏆 Your total score is: {total_score} point{'s' if total_score != 1 else ''}.\n\n"
    if username:
        msg += f"\n👤 Your Instagram username: {username}"
    else:
        msg += "\n⚠️ You haven't set your Instagram username yet. Use /username <your_username> to set it."

    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    await show_welcome(update)

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.delete()
        return
    """Handle file uploads and save cookies.json, replacing the old one."""
    if update.message and update.message.document:
        file = update.message.document
    
        # Check if the file name is 'cookies.json'
        if file.file_name == "cookies.json":
            # Download the file
            new_file = await context.bot.get_file(file.file_id)
            
            # Save the file to the server, replacing the old one
            new_file.download(COOKIES_FILE_PATH)
            
            await update.message.reply_text("✅ File 'cookies.json' has been successfully saved.")
        else:
            await update.message.reply_text("Group Link: " + GROUP_LINK)
    else:
        await update.message.reply_text("Group Link: " + GROUP_LINK)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await update.message.reply_text("Sorry, I didn't understand that. Please use one of the available commands.")
    await update.message.delete()

        
# === Message Handler ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        
    if update.message and update.effective_chat.id == TARGET_GROUP_ID:
        # Ignore bot commands in the group
        
        user = update.message.from_user
        text = update.message.text
               
        match = re.search(INSTAGRAM_PATTERN, text, re.IGNORECASE)
        if match:
            link = match.group(0)

            # Check if the user has a score greater than 0
            current_score = get_user_score(user.id)
            
            username = get_username(user.id)  
            if not username:
                # User hasn't set their Instagram username
                await update.message.delete()  # Delete the message

                try:
                    # Send a message to the user indicating they need to set an Instagram username
                    await context.bot.send_message(
                        chat_id=user.id,
                        text="❌ You need to set an Instagram username to use this bot. Use /username <your_username>."
                    )
                except:
                    logger.warning(f"Couldn’t message user {user.id}")
                return  # Stop further execution for this message
            
            if current_score > 0:
                # Decrement the score for the user
                decrement_score(user.id)
                
                # Save the Instagram link to the database
                save_link(user.id, link)

                keyboard = [[
                    InlineKeyboardButton("📋 View List", url=f"https://t.me/{BOT_USERNAME}?start=queue"),
                    InlineKeyboardButton("📜 View Rules", url=f"https://t.me/{BOT_USERNAME}?start=rules")
                ]]
                markup = InlineKeyboardMarkup(keyboard)

                try:
                    await context.bot.send_message(
                        chat_id=user.id,
                        text="✅ Your Instagram link has been added successfully!\n\nUse the buttons below to view the list or rules.",
                        reply_markup=markup
                    )
                except:
                    logger.warning(f"Couldn’t message user {user.id}")

                await update.message.reply_text(text="✅ Link saved. Check your DMs!", reply_markup=markup)

                logger.info(f"New link saved: {link}")
            else:
                await update.message.delete()
                try:
                    await context.bot.send_message(
                        chat_id=user.id,
                        text="❌ You can't add a link yet! Go engage with others' posts, earn points, and then post here."
                    )
                except:
                    logger.warning(f"Couldn’t message user {user.id}")

                logger.info(f"User {user.id} tried to post with a score of 0.")
        else: 
            await update.message.delete()
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text="⚠️ Only Instagram links are allowed!\n❌ Your message has been deleted."
                )
            except:
                logger.warning(f"Couldn’t message user {user.id}")
            logger.info("Non-approved message deleted")
            
        # await update.message.reply_text("Test", text)



# === Main ===

if __name__ == '__main__':
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add specific handlers first
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("username", set_instagram_username))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", mystats))
    app.add_handler(CommandHandler("queue", queue))
    app.add_handler(CommandHandler("rules", show_rules))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    # Add handlers for documents and regular text messages
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add the unknown handler last to catch any unmatched text messages
    app.add_handler(MessageHandler(filters.TEXT, unknown))
    
    print("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    


