# Walpurgis Bot

This bot automates the archiving, management, and verification of daily image posts by a specific user (Johan). It includes features for automatic detection, manual overrides, status reporting, deletion, and scheduled reminders. The bot uses Discord's application commands, context menus, and scheduled tasks, along with an SQLite database for persistence.

## Features

### Automatic Archiving
- **Message Listener**: Listens for messages from Johan containing images.
- **Day Number Detection**: 
  - Scans message content for day numbers using regex.
  - Handles cases with multiple numbers, recent posts, or incorrect next day numbers.
- **Checks Before Archiving**:
  1. If multiple numbers are found, prompts manual submission.
  2. If the message is less than 12 hours old, requests manual confirmation.
  3. If the detected day isn't the immediate next expected number, alerts for manual verification.
- **Archiving**: If conditions are met, archives the image and associated day number into an SQLite database.
- **Public Notifications**: Sends public messages in the channel for warnings, errors, or confirmations during automatic archiving.

### Archive Series Command
- **Slash Command**: `/archive_series`
  - **Parameters**:
    - `message_id`: The ID of a message containing images.
    - `days`: Comma-separated list of day numbers.
  - **Function**: Archives the specified message for each provided day number using the same logic as automatic archiving.

### Deletion
- **Context Menu Command**: "Delete Daily Johan"
  - **Function**: When right-clicking a message, the bot:
    - Finds all archived days associated with that message.
    - Lists these days and asks for confirmation.
    - Deletes all related entries from the database upon confirmation.
- **Handles Multiple Entries**: Accounts for cases where one message is associated with multiple days.

### Status Reporting
- **Slash Command**: `/daily_johan_status`
  - **Parameters**:
    - `start`: Starting day number (default 1).
    - `end`: Ending day number (optional; if omitted, uses the latest day in the database).
  - **Function**: Displays a paginated list of days with their status (✅ for archived, ❌ for missing).
  - **Pagination**: 
    - Limits to 20 days per page.
    - Provides "Previous" and "Next" buttons to navigate pages.

### Daily Check & Reminders
- **Dedicated Cog**: `DailyCheckCog`
- **Scheduled Task**:
  - Runs every 24 hours.
  - Checks if the latest daily entry is missing or if there are gaps.
  - **Public Reminders**:
    - If a new Daily Johan is missing, pings Johan publicly in a designated channel.
    - Alerts publicly if there's a gap in daily entries.

## Architecture and Modules

- **Cogs**: The bot is modular, with separate cogs for archiving, deletion, status reporting, and daily checks.
- **Database Module** (`database.py`): Centralizes database operations such as initializing the database, archiving entries, fetching existing records, and deleting records.
- **Commands & Interactions**: Uses Discord's application commands and context menus for interactive functionality.
- **Scheduling**: Uses `discord.ext.tasks` to schedule daily checks and reminders.

## Setup and Configuration

**Docker Compose Option**
```yaml
version: '3'
services:
  walpurgisbot:
    image: ghcr.io/danielhkuo/walpurgisbot:latest
    environment:
      - TOKEN=your_discord_bot_token
      - DEFAULT_CHANNEL_ID=your_default_channel_id
      - JOHAN_USER_ID="johan"_user_id
    restart: unless-stopped
```


1. **Environment Variables (for use in development)**:
   - Use a `.env` file to store sensitive information like the bot token.
   - Example:
     ```
     TOKEN=your_discord_bot_token
     ```
2. **Database**:
   - The bot uses an SQLite database (`daily_johans.db`) to store archived entries.
   - The database is initialized automatically upon bot startup.

3. **User and Channel IDs (Must change for use in a different server!)**:
   - Update constants like `JOHAN_USER_ID` and `DEFAULT_CHANNEL_ID` in the code with the appropriate Discord user and channel IDs.

4. **Loading Cogs**:
   - The main bot file loads all cogs on startup, ensuring modular features are initialized.

## Usage

- **Automatic Archiving**: Simply have Johan post images normally. The bot will automatically detect and archive them based on the logic defined.
- **Manual Override for Archive Series**: Use the `/archive_series` command when a single message should cover multiple days.
- **Deleting Entries**: Right-click on a message and select "Delete Daily Johan" to remove all associated daily records.
- **Checking Status**: Use the `/daily_johan_status` command to view which days have been archived and navigate through pages.
- **Daily Reminders**: The bot will automatically send public reminders if a new Daily Johan is missing or if there's a gap.