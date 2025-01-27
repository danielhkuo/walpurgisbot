# Walpurgis Bot

Walpurgis Bot automates the archiving, management, and verification of daily image posts by a specific user (**Johan**) on Discord. It supports:
- **Automatic Detection** of new image posts
- **Manual Overrides** for edge cases
- **Status Reporting** via slash commands
- **Deletion** of archived entries
- **Daily Reminders** to ensure continuity
- **Backup** commands for data integrity

All data is stored in an **SQLite** database for easy persistence.

---

## Commands

### Slash Commands

#### `/manual_archive`
**Description:**  
Manually archive a message for one or more days.

**Parameters:**
- `message_id` *(string, required)*  
  The ID of the message containing images to archive.
- `days` *(string, required)*  
  Space- or comma-separated list of day numbers (e.g., `"5,6,7"` or `"5 6 7"`).

**Usage Example:**
```
/manual_archive message_id:123456789012345678 days:5,6,7
```

**Functionality:**  
Archives the specified message for each provided day number. Supports:
- **One-to-One Assignment:** Each image is assigned to a different day.
- **Multiple-to-One Assignment:** Multiple images are assigned to a single day if only one day is specified.

---

#### `/daily_johan_status`
**Description:**  
Displays the archiving status of Daily Johans within a specified day range.

**Parameters:**
- `start` *(integer, optional)*  
  Starting day number (default is 1).
- `end` *(integer, optional)*  
  Ending day number. If omitted, the latest day in the database is used.

**Usage Example:**
```
/daily_johan_status start:1 end:10
```

**Functionality:**  
Provides a paginated list indicating which days have been archived (**✅**) and which are missing (**❌**). Navigate through pages with the **Previous** and **Next** buttons (or jump directly to a page).

---

### Context Menu Commands

#### "Manual Archive Daily Johan"
**Description:**  
Allows you to manually archive a message via right-click (Message → Apps → Manual Archive Daily Johan).

**Functionality:**  
1. **Trigger:** Right-click on a message containing images.  
2. **Auto-Scan:** Attempts to automatically detect day numbers and assign images to them.  
3. **Fallback Manual Input:** If automatic detection fails, prompts you to enter the day number(s) manually.  
4. **Archiving Completion:** Stores the message in the SQLite database for the specified days.

---

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

---

## Docker Compose Deployment

Deploying Walpurgis Bot using **Docker Compose** simplifies the setup process. Below is a sample configuration to get your bot running quickly.

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
    restart: unless-stopped
```

### Environment Variables

- **`TOKEN`** *(string, required)*  
  Your Discord bot token. **Keep this secure** and **never** share it publicly.

- **`DEFAULT_CHANNEL_ID`** *(integer, required)*  
  The ID of the channel where the bot sends reminders and notifications.

- **`JOHAN_USER_ID`** *(integer, required)*  
  The Discord user ID of Johan, whose messages the bot will monitor and archive.

- **`TIMEZONE`** *(string, optional)*  
  The IANA timezone string to configure the bot's local time (default: `America/Chicago`). Examples:
  - `America/New_York`
  - `Europe/London`
  - `Asia/Tokyo`

---

### Deployment Steps

1. **Install Docker & Docker Compose**  
   Follow the [official Docker documentation](https://www.docker.com/get-started) for installation instructions.

2. **Create `docker-compose.yml`**  
   Copy the above snippet into a new `docker-compose.yml` file in your project directory.

3. **Configure Environment Variables**  
   Replace the placeholder values (`your_discord_bot_token`, etc.) with your actual credentials and preferences.

4. **Deploy the Bot**  
   ```bash
   docker-compose up -d
   ```
   The command pulls the latest Docker image, spins up the container, and runs the bot in detached mode.

5. **Verify Deployment**  
   Check the container logs:
   ```bash
   docker-compose logs -f walpurgisbot
   ```
   Look for messages confirming the bot is successfully logged in.

6. **Manage the Bot**  
   - **Stop**  
     ```bash
     docker-compose stop walpurgisbot
     ```
   - **Restart**  
     ```bash
     docker-compose restart walpurgisbot
     ```
   - **Remove**  
     ```bash
     docker-compose down
     ```

---

## Setup and Configuration (Development)

**Note**: The following steps apply if you’re developing or testing locally without Docker.

1. **Environment Variables**  
   Create a `.env` file in your project root:
   ```bash
   TOKEN=your_discord_bot_token
   DEFAULT_CHANNEL_ID=your_default_channel_id
   JOHAN_USER_ID=your_johan_user_id
   TIMEZONE=America/Chicago
   ```
   Make sure you load these variables (e.g., with `dotenv`).

2. **Install Dependencies**  
   Create and activate a Python virtual environment, then install:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Initialization**  
   A local SQLite file (`daily_johans.db`) is created automatically on first run.

4. **Load Cogs**  
   Place all `.py` cog files (e.g., `archive_daily_cog.py`, `fun_cog.py`) in a `cogs/` folder.  
   The `bot.py` file calls `await bot.load_extension("cogs.example_cog")` for each cog.

---

## Usage

- **Automatic Archiving**  
  Have Johan post images. The bot automatically detects attachments, assigns day numbers, and archives them if they match expectations.

- **Manual Archiving**  
  Use `/manual_archive` to override the automatic logic for specific messages.

- **Deleting Entries**  
  Right-click a message → *Apps* → **Delete Daily Johan** to remove its entries from the DB.

- **Checking Status**  
  `/daily_johan_status` to view archived or missing days in a given range, with pagination.

- **Daily Reminders**  
  The bot regularly checks if new Johans are missing. If so, it sends a reminder in the configured channel.

---

Happy archiving with Walpurgis Bot! If you run into issues or want to contribute, open an issue or pull request in the project repository.
