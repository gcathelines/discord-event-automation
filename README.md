# Discord Event Automation Bot

A Python bot that automatically starts Discord scheduled voice events at their scheduled times. Perfect for community servers that want to ensure voice events begin on time without manual intervention.

## Features

- 🤖 **Automatic Event Starting**: Monitors and starts voice/stage channel events at their scheduled times
- 🔄 **Smart Conflict Resolution**: Automatically ends existing events in the same voice channel when starting new ones
- ⚡ **Real-time Scheduling**: Uses APScheduler for precise event timing
- 📊 **Slash Commands**: Easy-to-use Discord slash commands for management
- 🛡️ **Error Handling**: Comprehensive logging and error recovery
- 🎯 **Voice Channel Focus**: Only manages voice and stage channel events

## Requirements

- Python 3.13+
- Discord Bot with appropriate permissions and intents
- Discord Server (Guild) ID

## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd discord-event-automation
   ```

2. **Install dependencies:**

   ```bash
   # Using uv (recommended)
   uv sync
   ```

3. **Set up environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your values:

   ```env
   DISCORD_BOT_TOKEN=your_bot_token_here
   GUILD_ID=your_server_id_here
   ```

## Discord Bot Setup

1. **Create a Discord Application:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token to your `.env` file

2. **Enable Required Intents:**
   In the Discord Developer Portal, under "Bot" section, enable these **Privileged Gateway Intents**:
   - ✅ **Server Members Intent** - Required for guild member access
   - ✅ **Message Content Intent** - Required for message processing

   These intents are essential for the bot to function properly.

3. **Set Bot Permissions:**
   The bot needs the following permissions:
   - `Manage Events` - To start/end scheduled events
   - `View Channels` - To access voice channels
   - `Use Slash Commands` - For bot commands

4. **Invite Bot to Server:**
   - Go to "OAuth2" > "URL Generator"
   - Select scopes: `bot` and `applications.commands`
   - Select the permissions listed above
   - Use the generated URL to invite the bot

5. **Get Guild ID:**
   - Enable Developer Mode in Discord settings
   - Right-click your server name
   - Click "Copy Server ID"
   - Add this to your `.env` file

## Usage

### Running the Bot

```bash
# Activate virtual environment (if using one)
source .venv/bin/activate

# Run the bot
python main.py
```

### Slash Commands

The bot provides several slash commands:

- **`/sync_events`** - Refresh and sync all voice channel events for automation
- **`/list_scheduled`** - Show all voice events that will auto-start with their status
- **`/start_event <event_id>`** - Manually start a specific voice event
- **`/bot_status`** - Show bot status and scheduled jobs count

### How It Works

1. **Event Discovery**: Bot scans for scheduled voice/stage channel events
2. **Job Scheduling**: Creates timed jobs using APScheduler for each event's start time
3. **Conflict Resolution**: Before starting an event, ends any active events in the same voice channel
4. **Event Starting**: Automatically starts the event at the scheduled time
5. **Monitoring**: Provides logging and status updates throughout the process

### Event Behavior

- **Multiple channels**: Events in different voice channels can run simultaneously
- **Same channel conflicts**: New events automatically end existing events in the same channel
- **Member presence**: Events can start/end regardless of who's in the voice channel
- **Past events**: Events with past start times are scheduled to start in 60 seconds

## Project Structure

```
discord-event-automation/
├── main.py              # Main bot application
├── config.yaml          # Configuration file (currently unused)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment template
├── pyproject.toml       # Python project configuration
├── uv.lock             # Dependency lock file
└── README.md           # This file
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_BOT_TOKEN` | Your Discord bot token | Yes |
| `GUILD_ID` | Your Discord server ID | Yes |

### Bot Settings

The bot uses these default settings:

- **Command Prefix**: `!` (for future text commands)
- **Status**: "Automating voice events"
- **Timezone**: UTC for all scheduling

## Logging

The bot provides detailed logging for:

- ✅ Successful event starts
- ❌ Permission errors
- 🔄 Job scheduling and execution
- 🛑 Event conflicts and resolutions
- 💥 Error tracking with full tracebacks

Log levels can be adjusted in the code (default: INFO).

## Troubleshooting

### Common Issues

1. **Bot not connecting or crashing on startup:**
   - Verify **Server Members Intent** and **Message Content Intent** are enabled in Discord Developer Portal
   - Check that bot token is correct in `.env` file

2. **Bot not responding to slash commands:**
   - Ensure bot has `Use Slash Commands` permission
   - Try running `/sync_events` to refresh commands

3. **"No permission" errors:**
   - Verify bot has `Manage Events` permission
   - Check that bot can access the voice channels

4. **Events not starting automatically:**
   - Run `/bot_status` to check scheduler status
   - Use `/sync_events` to refresh event list
   - Check bot logs for error messages

5. **"Guild not found" errors:**
   - Verify `GUILD_ID` in `.env` is correct
   - Ensure bot is invited to the correct server

### Debug Steps

1. Check bot permissions in Discord server settings
2. Verify **both required intents are enabled** in Discord Developer Portal
3. Verify environment variables are set correctly
4. Look at bot logs for specific error messages
5. Use `/bot_status` to check internal bot state
6. Test manually with `/start_event <id>`
