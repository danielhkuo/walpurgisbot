# Walpurgis Bot

Walpurgis Bot automates the archiving, management, and verification of daily image posts by a specific user (Johan) on Discord. It supports automatic detection, manual overrides, status reporting, deletion, and scheduled reminders, utilizing Discord's application commands and context menus alongside an SQLite database for data persistence.

## Commands

### Slash Commands

#### `/manual_archive`
**Description:**  
Manually archive a message for one or more days.

**Parameters:**
- `message_id` *(string, required)*: The ID of the message containing images to archive.
- `days` *(string, required)*: Space or comma-separated list of day numbers (e.g., "5,6,7" or "5 6 7").

**Usage Example:**
```
/manual_archive message_id:123456789012345678 days:5,6,7
```

**Functionality:**  
Archives the specified message for each provided day number. Supports:
- **One-to-One Assignment:** Each image is assigned to a different day.
- **Multiple-to-One Assignment:** Multiple images are assigned to a single day if only one day is specified.

#### `/daily_johan_status`
**Description:**  
Displays the archiving status of Daily Johans within a specified range.

**Parameters:**
- `start` *(integer, optional)*: Starting day number (default is 1).
- `end` *(integer, optional)*: Ending day number. If omitted, the latest day in the database is used.

**Usage Example:**
```
/daily_johan_status start:1 end:10
```

**Functionality:**  
Provides a paginated list indicating which days have been archived (✅) and which are missing (❌). Navigate through pages using "Previous" and "Next" buttons.

### Context Menu Commands

#### "Delete Daily Johan"
**Description:**  
Deletes all archived entries associated with a specific message.

**Functionality:**  
1. **Trigger:** Right-click on a message and select "Delete Daily Johan."
2. **Process:** 
   - Identifies all day numbers linked to the selected message.
   - Prompts for confirmation.
   - Upon confirmation, deletes all related entries from the database.

**Note:**  
Handles cases where a single message is associated with multiple days.

## Docker Compose Deployment

Deploying Walpurgis Bot using Docker Compose streamlines the setup process. Below is the configuration required to get your bot up and running.

### `docker-compose.yml`

```yaml
version: '3'
services:
  walpurgisbot:
    image: ghcr.io/danielhkuo/walpurgisbot:latest
    environment:
      - TOKEN=your_discord_bot_token
      - DEFAULT_CHANNEL_ID=your_default_channel_id
      - JOHAN_USER_ID=your_johan_user_id
      - TIMEZONE=America/Chicago  # Optional: Set your desired timezone
    volumes:
      - ./data:/app/data  # Persist the SQLite database
    restart: unless-stopped
```

### Environment Variables

- **`TOKEN`** *(string, required)*:  
  Your Discord bot token. **Keep this secure** and **never share it publicly**.

- **`DEFAULT_CHANNEL_ID`** *(integer, required)*:  
  The Discord channel ID where the bot will send reminders and public notifications.

- **`JOHAN_USER_ID`** *(integer, required)*:  
  The Discord user ID of Johan, whose messages the bot will monitor and archive.

- **`TIMEZONE`** *(string, optional)*:  
  The IANA timezone string to configure the bot's timezone settings (default is `America/Chicago`).  
  **Examples:**
  - `America/New_York`
  - `Europe/London`
  - `Asia/Tokyo`

### Deployment Steps

1. **Install Docker and Docker Compose:**  
   Ensure Docker and Docker Compose are installed on your system. Download them from the [official Docker website](https://www.docker.com/get-started) if necessary.

2. **Create `docker-compose.yml`:**  
   Save the above Docker Compose configuration into a file named `docker-compose.yml` in your project directory.

3. **Configure Environment Variables:**  
   Replace the placeholder values with your actual Discord bot token, channel ID, Johan's user ID, and desired timezone.

4. **Deploy the Bot:**  
   Open a terminal in your project directory and run:
   ```bash
   docker-compose up -d
   ```
   This command will pull the latest Docker image from GitHub Container Registry, create the container, and start the bot in detached mode.

5. **Verify Deployment:**  
   Check the logs to ensure the bot is running correctly:
   ```bash
   docker-compose logs -f walpurgisbot
   ```
   Look for messages indicating that the bot has successfully logged in and is operational.

6. **Manage the Bot:**
   - **Stop the Bot:**
     ```bash
     docker-compose stop walpurgisbot
     ```
   - **Restart the Bot:**
     ```bash
     docker-compose restart walpurgisbot
     ```
   - **Remove the Bot:**
     ```bash
     docker-compose down
     ```

---

## Setup and Configuration (Development)

**Note:** These steps are for setting up the bot in a development environment.

1. **Environment Variables:**
   - Create a `.env` file in your project root to store sensitive information:
     ```
     TOKEN=your_discord_bot_token
     DEFAULT_CHANNEL_ID=your_default_channel_id
     JOHAN_USER_ID=your_johan_user_id
     TIMEZONE=America/Chicago
     ```
   - Ensure your development environment loads these variables appropriately.

2. **Install Dependencies:**
   - Activate your virtual environment:
     ```bash
     source venv/bin/activate
     ```
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```

3. **Database Initialization:**
   - The SQLite database (`daily_johans.db`) initializes automatically upon the bot's first run.

4. **Load Cogs:**
   - Ensure all cog files are placed in the `cogs/` directory and are being loaded in `bot.py`.

---

## Usage

- **Automatic Archiving:**  
  Have Johan post images normally. The bot will automatically detect and archive them based on the defined logic.

- **Manual Archiving:**  
  Use the `/manual_archive` command to manually archive specific messages for one or multiple days.

- **Deleting Entries:**  
  Right-click on a message and select "Delete Daily Johan" to remove all associated daily records.

- **Checking Status:**  
  Use the `/daily_johan_status` command to view which days have been archived and navigate through pages.

- **Daily Reminders:**  
  The bot automatically sends public reminders if a new Daily Johan is missing or if there's a gap in entries.
