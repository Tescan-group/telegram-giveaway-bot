import random
import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import telegram
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configurations for Google Sheets and Bot
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'
creds = Credentials.from_service_account_file('google-credentials.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

TOKEN = 'YOUR_TELEGRAM_BOT_API_KEY'
BOT_OWNER_ID = 123456789  # Replace with your Telegram user ID

# Store giveaways in memory
giveaways = {}

# Owner-only decorator
def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != BOT_OWNER_ID:
            await update.message.reply_text("You are not authorized to perform this action.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# Handle /start command to show menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Enter Giveaway", callback_data="enter_giveaway")]
    ]
    
    # Show owner-only options only to the bot owner
    if update.effective_user.id == BOT_OWNER_ID:
        keyboard.extend([
            [InlineKeyboardButton("Create Giveaway", callback_data="create_giveaway")],
            [InlineKeyboardButton("Pick Winner", callback_data="pick_winner")],
            [InlineKeyboardButton("Send Promo", callback_data="send_promo")]
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Please choose a command:", reply_markup=reply_markup)


# Register Callback Query Handlers for menu options
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "enter_giveaway":
        await enter_giveaway(update, context)
    elif query.data == "create_giveaway":
        await create_giveaway(update, context)
    elif query.data == "pick_winner":
        await pick_winner(update, context)
    elif query.data == "send_promo":
        await send_promo(update, context)


# Log giveaway details to Google Sheets
async def log_giveaway_details(giveaway_id, description, end_time):
    sheet_range = 'Giveaways!A:D'  # Adjust this range based on where you want to log the data
    values = [
        [giveaway_id, description, end_time.strftime('%Y-%m-%d %H:%M:%S'), '']
    ]
    body = {
        'values': values
    }
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range,
        valueInputOption="RAW",
        body=body
    ).execute()

# Log winner
async def log_winner(giveaway_id, winner_username):
    sheet_range = 'Winners!A:C'  # Adjust as needed
    values = [
        [giveaway_id, winner_username, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    body = {
        'values': values
    }
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range,
        valueInputOption="RAW",
        body=body
    ).execute()

async def announce_winner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    winner_id = int(query.data.split("_")[-1])  # Extract user ID from callback data
    giveaway_id = context.user_data.get('selected_giveaway_id')
    
    if not giveaway_id:
        await query.edit_message_text("No giveaway selected.")
        return
    
    giveaway = giveaways[giveaway_id]
    
    if winner_id not in giveaway['participants']:
        await query.edit_message_text("The selected winner is not a participant.")
        return

    await announce_winner(update, context, giveaway_id, winner_id)


# Create Giveaway Command (Owner only)
@owner_only
async def create_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if not context.args or len(context.args) < 2:
        # Prompt for duration and description
        # Check if it's a callback query update
        if update.message:
            await update.message.reply_text("Please enter the giveaway duration in minutes and description, separated by a space. \nExample: /create_giveaway 60 Giveaway Name Here")
        else:
            await update.callback_query.message.reply_text("Please enter the giveaway duration in minutes and description, separated by a space. \nExample: /create_giveaway 60 Giveaway Name Here")

        return

    duration = int(context.args[0])
    description = ' '.join(context.args[1:])
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
    
    giveaway_id = len(giveaways) + 1  # Unique ID for each giveaway
    chat_id = update.message.chat_id
    giveaways[giveaway_id] = {
        'description': description,
        'end_time': end_time,
        'participants': [],
        'chat_id': chat_id  # Store chat_id along with giveaway details
    }
    
    await update.message.reply_text(f"Giveaway created!\nDescription: {description}\nEnds in {duration} minutes.")
    await log_giveaway_details(giveaway_id, description, end_time)

# Register the handler for "Pick Winner" and show giveaway options
async def pick_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not giveaways:
        await update.callback_query.message.reply_text("No active giveaways!")
        return

    keyboard = [
        [InlineKeyboardButton(f"Giveaway {gid}: {data['description']}", callback_data=f"select_giveaway_{gid}")]
        for gid, data in giveaways.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Select a giveaway to pick a winner:", reply_markup=reply_markup)


# Callback for selecting a giveaway to pick winner
async def select_giveaway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    giveaway_id = int(query.data.split("_")[-1])
    context.user_data['selected_giveaway_id'] = giveaway_id
    
    keyboard = [
        [InlineKeyboardButton("Pick Winner Randomly", callback_data="pick_winner_random")],
        [InlineKeyboardButton("Pick Winner Manually", callback_data="pick_winner_manual")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose winner selection method:", reply_markup=reply_markup)


# Callback to pick a winner randomly
async def pick_winner_random_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    giveaway_id = context.user_data.get('selected_giveaway_id')
    if not giveaway_id or not giveaways[giveaway_id]['participants']:
        await update.callback_query.edit_message_text("No participants to pick from.")
        return

    winner_id = random.choice(giveaways[giveaway_id]['participants'])
    await announce_winner(update, context, giveaway_id, winner_id)

    

# Callback for manual winner selection
async def pick_winner_manual_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    giveaway_id = context.user_data.get('selected_giveaway_id')
    participants = giveaways[giveaway_id]['participants']
    
    if not giveaway_id or not participants:
        await update.callback_query.edit_message_text("No participants to choose from.")
        return
    
    # Ask the owner for a username
    await update.callback_query.edit_message_text("Please enter the username of the winner (e.g., @username):")
    return

# Handle the owner's response for selecting the winner manually
async def handle_manual_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip('@')  # Strip '@' if present
    
    # Search for the username in the participants list
    giveaway_id = context.user_data.get('selected_giveaway_id')
    participants = giveaways[giveaway_id]['participants']
    
    winner_id = None
    for part in participants:
        user = await context.bot.get_chat(part)
        if user.username == username:
            winner_id = user.id
            break
    
    if winner_id:
        await announce_winner(update, context, giveaway_id, winner_id)
    else:
        await update.message.reply_text(f"User @{username} not found in the participants list.")

# Function to enter giveaway (open to all users)
async def enter_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not giveaways:
        # Check if it's a message or a callback query update
        if update.message:
            await update.message.reply_text("No active giveaways!")
        elif update.callback_query:
            await update.callback_query.message.reply_text("No active giveaways!")
        return

    chat_id = list(giveaways.keys())[0]  # Assuming a single active giveaway for simplicity
    user = update.effective_user
    if user.id in giveaways[chat_id]['participants']:
        if update.message:
            await update.message.reply_text("You've already entered this giveaway.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("You've already entered this giveaway.")
        return

    giveaways[chat_id]['participants'].append(user.id)
    if update.message:
        await update.message.reply_text("You've been entered into the giveaway!")
    elif update.callback_query:
        await update.callback_query.message.reply_text("You've been entered into the giveaway!")

    await log_entry(chat_id, user.username, user.id)


# Log each entry into Google Sheets
async def log_entry(giveaway_id, username, user_id):
    sheet = service.spreadsheets()
    values = [[giveaway_id, username, user_id]]
    body = {'values': values}
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Entries!A:C",
        valueInputOption="RAW",
        body=body
    ).execute()

# Send promotional messages (owner-only) to all giveaway participants
@owner_only
async def send_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args is None or len(context.args) < 1:
        # Handle the case where no message is provided.
        if update.message:
            await update.message.reply_text("Please provide the promotional message. \nExample: /send_promo Your Promotional Text")
        elif update.callback_query:
            await update.callback_query.message.reply_text("Please provide the promotional message. \nExample: /send_promo Your Promotional Text")
        return

    promo_message = ' '.join(context.args)
    sheet = service.spreadsheets()
    
    # Retrieve all users from Entries sheet
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Entries!C:C").execute()
    user_ids = result.get('values', [])

    successful, failed = 0, 0
    for user in user_ids:
        try:
            await context.bot.send_message(int(user[0]), promo_message)
            successful += 1
        except Exception:
            failed += 1

    # Log promo results in Sheets
    promo_log = [[datetime.datetime.now().isoformat(), promo_message, successful, failed]]
    body = {'values': promo_log}
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="PromotionsLog!A:D",
        valueInputOption="RAW",
        body=body
    ).execute()

    # Ensure a response is given whether from message or callback query
    if update.message:
        await update.message.reply_text(f"Promotional message sent: {promo_message}")
    elif update.callback_query:
        await update.callback_query.message.reply_text(f"Promotional message sent: {promo_message}")



# Announce winner and notify participants and channel
async def announce_winner(update: Update, context: ContextTypes.DEFAULT_TYPE, giveaway_id, winner_id):
    # First, retrieve the giveaway details
    giveaway = giveaways.get(giveaway_id)
    
    if not giveaway:
        await update.callback_query.edit_message_text("Giveaway not found.")
        return

    # The winner's details are stored in `winner_id`
    winner = await context.bot.get_chat(winner_id)  # Directly using `get_chat` as the user is interacting in private

    if not winner:
        await update.callback_query.edit_message_text(f"Failed to retrieve winner details for {winner_id}.")
        return

    # Announce to the bot owner
    await context.bot.send_message(
        chat_id=BOT_OWNER_ID,
        text=f"The winner of giveaway '{giveaway['description']}' is: @{winner.username} 🎉"
    )

    # Notify all participants (they are in private chat, so we can send them direct messages)
    for participant_id in giveaway['participants']:
        await context.bot.send_message(
            chat_id=participant_id,
            text=f"The winner of the giveaway '{giveaway['description']}' is @{winner.username}! Thank you for participating."
        )
    
    # Announce in the default channel
    channel_id = "@Channel_USERNAME"  # The username or ID of the channel
    try:
        await context.bot.send_message(
            chat_id=channel_id,
            text=f"🎉 Congratulations to @{winner.username} for winning the giveaway: '{giveaway['description']}'!"
        )
    except telegram.error.BadRequest:
        # Handle if there's any issue with sending the message (e.g., bot not added to the channel)
        await update.callback_query.edit_message_text("Failed to announce in @testinggiveawayproject.")

    # Optionally announce in a channel
    await update.callback_query.edit_message_text("Winner announced in the channel.")

    # Log winner and cleanup giveaway
    await log_winner(giveaway_id, winner.username)
    del giveaways[giveaway_id]




# Register Command Handlers and Callbacks
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("create_giveaway", create_giveaway))
    app.add_handler(CommandHandler("pick_winner", pick_winner))
    app.add_handler(CallbackQueryHandler(select_giveaway_callback, pattern="^select_giveaway_"))
    app.add_handler(CallbackQueryHandler(pick_winner_random_callback, pattern="^pick_winner_random"))
    app.add_handler(CallbackQueryHandler(pick_winner_manual_callback, pattern="^pick_winner_manual"))
    app.add_handler(CallbackQueryHandler(announce_winner_callback, pattern="^select_winner_"))
    app.add_handler(CommandHandler("enter_giveaway", enter_giveaway))
    app.add_handler(CommandHandler("send_promo", send_promo))
    app.add_handler(CallbackQueryHandler(announce_in_channel_callback, pattern="^announce_in_channel_"))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(BOT_OWNER_ID), handle_manual_winner))

    # Register Callback Query Handlers for menu buttons and actions
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(enter_giveaway|create_giveaway|pick_winner|send_promo)$"))
    app.add_handler(CallbackQueryHandler(select_giveaway_callback, pattern="^select_giveaway_"))
    app.add_handler(CallbackQueryHandler(pick_winner_random_callback, pattern="^pick_winner_random"))
    app.add_handler(CallbackQueryHandler(pick_winner_manual_callback, pattern="^pick_winner_manual"))
    app.add_handler(CallbackQueryHandler(announce_winner_callback, pattern="^select_winner_"))
    app.add_handler(CallbackQueryHandler(announce_in_channel_callback, pattern="^announce_in_channel_"))
    app.add_handler(CallbackQueryHandler(send_promo, pattern="^send_promo$"))

    app.run_polling()

if __name__ == "__main__":
    main()
