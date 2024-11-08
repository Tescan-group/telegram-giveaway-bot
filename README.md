# Telegram Giveaway Bot

This bot enables seamless giveaway management on Telegram with Google Sheets integration for tracking giveaways, participants, winners, and promotional messages.

## Table of Contents

1. [Requirements](#requirements)
2. [Setup Instructions](#setup-instructions)
3. [Connecting to Google Sheets](#connecting-to-google-sheets)
4. [Bot Commands](#bot-commands)
5. [Usage](#usage)
6. [Preview](#preview)

---

## Requirements

- **Python 3.7+**
- **Telegram Bot Token**: Create a bot on [BotFather](https://core.telegram.org/bots#botfather).
- **Google Cloud Project**: With Google Sheets API enabled.
- **Required Pip Packages**:
    ```bash
    pip install python-telegram-bot google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    ```

## Setup Instructions

1. **Clone this repository** and navigate into it:
    ```bash
    git clone https://github.com/Tescan-group/telegram-giveaway-bot.git
    cd telegram-giveaway-bot
    ```

2. **Replace API Keys**:
   - In the bot's code, replace `TOKEN` with your Telegram bot's token.
   - Replace `BOT_OWNER_ID` with your Telegram user ID.
   - Update `SPREADSHEET_ID` with the Google Spreadsheet ID.
   - Update `channel_id` with your channel's username or ID where winner will be announced. (The bot needs to be an admin of the channel.)

3. **Set up Google Sheets Credentials**:
   - Download your `google-credentials.json` file from your Google Cloud project.
   - Place it in the root directory of this project.
   - Make sure to update the path in the bot’s code if necessary.

4. **Run the Bot**:
    ```bash
    script.py
    ```

---

## Connecting to Google Sheets

1. **Google Cloud Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project and enable the **Google Sheets API**.
   - Under **APIs & Services > Credentials**, create a service account and download the JSON key file. Save it as `google-credentials.json`.

2. **Export Credentials JSON**:
   - Ensure that `google-credentials.json` is accessible to your bot's environment. For Linux/macOS, you can export it:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="path/to/google-credentials.json"
     ```

3. **Spreadsheet and Sheets**:
   - Your Google Spreadsheet should contain the following sheets with exact names:
      - **Giveaways**: To log giveaway details (ID, description, end time, status).
      - **Entries**: To track entries (giveaway ID, username, user ID).
      - **Winners**: To log winners (giveaway ID, winner username, date).
      - **PromotionsLog**: To log promotional messages sent (date, message, successful sends, failed sends).

---

## Bot Commands

| Command | Description | Example Usage |
| ------- | ----------- | ------------- |
| `/start` | Shows available options based on user permissions. | `/start` |
| `/create_giveaway <duration> <description>` | Owner only: Creates a new giveaway with specified duration in minutes and description. | `/create_giveaway 60 iPhone Giveaway` |
| `/pick_winner` | Owner only: Selects a winner from the active giveaway(s) through random or manual selection. | `/pick_winner` |
| `/send_promo <message>` | Owner only: Sends a promotional message to all participants. | `/send_promo Check out our new campaign!` |
| `/enter_giveaway` | Allows users to enter an active giveaway. | `/enter_giveaway` |

---

## Usage

1. **Creating a Giveaway**:
   - Only the bot owner can create a giveaway.
   - Example:
     ```bash
     /create_giveaway 120 New Year Special Giveaway
     ```

2. **Entering a Giveaway**:
   - Users can enter by clicking **Enter Giveaway** on the bot’s start menu or using `/enter_giveaway`.
   - The bot will record their entry in the **Entries** sheet.

3. **Picking a Winner**:
   - Owner uses `/pick_winner` to initiate the winner selection. Options to pick a winner randomly or manually will be displayed.
   - The winner’s username is logged in the **Winners** sheet.

4. **Sending Promotional Messages**:
   - Use `/send_promo <message>` to send a message to all giveaway participants.
   - The promotion's details and success rate will be logged in **PromotionsLog**.

---

## Preview

> **Admin Side Preview**: 
![IMG_1727](https://github.com/user-attachments/assets/6ae54cf6-e098-40a2-9d74-9aed6d2a9110)
<img height="300" alt="Screenshot 2024-11-08 at 4 42 38 PM" src="https://github.com/user-attachments/assets/029d3d55-11a3-4127-9ad8-8a293e23c9cc">
<img height="747" alt="Screenshot 2024-11-08 at 4 43 25 PM" src="https://github.com/user-attachments/assets/4c6a83e8-b65a-41e7-ae47-87d61694d14c">

> **User Side Preview**: 
![IMG_1730](https://github.com/user-attachments/assets/1de4c62a-4590-45fc-a0dd-4b9713c03b63)

---

## Important Notes

- **Replace API Keys and JSON Paths**: Update `TOKEN`, `BOT_OWNER_ID`, `SPREADSHEET_ID`, `channel_id` and `google-credentials.json` path in the code as needed.
- **Bot Permissions**: Ensure the bot is an admin in any channels where it needs to announce winners.

---
