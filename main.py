#!/usr/bin/env python3
"""
Discord Voice Event Automation Bot

This bot automatically starts Discord scheduled events in voice channels
based on their scheduled start times.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EventBot')

class VoiceEventBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_scheduled_events = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

        self.scheduler = AsyncIOScheduler()
        self.guild_id = int(os.getenv('GUILD_ID'))

        # Register slash commands
        self.tree.command(name="sync_events", description="Refresh and sync all voice channel events")(self.sync_events_command)
        self.tree.command(name="list_scheduled", description="Show all voice events that will auto-start")(self.list_scheduled_command)
        self.tree.command(name="start_event", description="Manually start a specific voice event")(self.start_event_command)
        self.tree.command(name="bot_status", description="Show bot status and scheduled jobs")(self.bot_status_command)

    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up voice event automation...")

        # Start scheduler
        self.scheduler.start()

        # Sync slash commands
        await self.tree.sync()
        logger.info("Slash commands synced")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')

        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="Automating voice events")
        )

        # Auto-sync events on startup
        await self.sync_voice_events()

    async def get_voice_events(self) -> List[discord.ScheduledEvent]:
        """Get all scheduled voice/stage channel events that are not yet active"""
        guild = self.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild {self.guild_id} not found")
            return []

        voice_events = []
        now = datetime.now(timezone.utc)

        for event in guild.scheduled_events:
            # Only process scheduled events (not active/completed)
            if event.status != discord.EventStatus.scheduled:
                continue

            # Only process future events
            if event.start_time <= now:
                continue

            # Only process voice/stage channel events
            if event.entity_type in [
                discord.EntityType.voice,
                discord.EntityType.stage_instance
            ]:
                voice_events.append(event)

        return voice_events

    async def sync_voice_events(self) -> int:
        """Sync all voice events and create cron jobs"""
        # Clear existing jobs
        self.scheduler.remove_all_jobs()

        voice_events = await self.get_voice_events()
        scheduled_count = 0

        for event in voice_events:
            try:
                # Schedule job for event start time
                self.scheduler.add_job(
                    self.start_voice_event,
                    DateTrigger(run_date=event.start_time),
                    args=[event.id],
                    id=f"event_{event.id}",
                    replace_existing=True
                )

                logger.info(
                    f"Scheduled: {event.name} at {event.start_time} "
                    f"(Channel: {event.channel.name if event.channel else 'Unknown'})"
                )
                scheduled_count += 1

            except Exception as e:
                logger.error(f"Error scheduling event {event.name}: {e}")

        logger.info(f"Synced {scheduled_count} voice events")
        return scheduled_count

    async def start_voice_event(self, event_id: int):
        """Start a specific voice event"""
        logger.info(f"🔄 Attempting to start event {event_id}")
        try:
            guild = self.get_guild(self.guild_id)
            if not guild:
                logger.error(f"❌ Guild {self.guild_id} not found")
                return

            # Get the event
            event = guild.get_scheduled_event(event_id)
            if not event:
                logger.error(f"❌ Event {event_id} not found")
                return

            logger.info(f"📍 Found event: {event.name} (Status: {event.status})")

            # Check if already active
            if event.status == discord.EventStatus.active:
                logger.info(f"⚠️ Event '{event.name}' is already active")
                return

            # Start the event
            logger.info(f"🚀 Starting event: {event.name}")
            await event.start()
            logger.info(f"✅ Successfully started event: {event.name}")

        except discord.Forbidden as e:
            logger.error(f"❌ No permission to start event {event_id}: {e}")
        except discord.HTTPException as e:
            logger.error(f"❌ HTTP error starting event {event_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error starting event {event_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # Slash Commands
    async def sync_events_command(self, interaction: discord.Interaction):
        """Slash command to sync events"""
        # Check permissions - need to get from guild member, not user
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)
        # Temporarily disable permission check for testing
        # if not member or not member.guild_permissions.manage_events:
        #     await interaction.response.send_message(
        #         "❌ You need 'Manage Events' permission to use this command.",
        #         ephemeral=True
        #     )
        #     return

        await interaction.response.defer()

        try:
            count = await self.sync_voice_events()

            embed = discord.Embed(
                title="🔄 Events Synced",
                description=f"Successfully synced **{count}** voice events",
                color=0x00ff00
            )

            if count > 0:
                embed.add_field(
                    name="Next Steps",
                    value="Events will automatically start at their scheduled times!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="No Events Found",
                    value="Create some voice channel events and run this command again.",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in sync command: {e}")
            await interaction.followup.send(
                f"❌ Error syncing events: {e}",
                ephemeral=True
            )

    async def list_scheduled_command(self, interaction: discord.Interaction):
        """List all scheduled voice events"""
        await interaction.response.defer()

        try:
            voice_events = await self.get_voice_events()
            jobs = self.scheduler.get_jobs()

            embed = discord.Embed(
                title="📅 Scheduled Voice Events",
                color=0x0099ff
            )

            if not voice_events:
                embed.description = "No voice events currently scheduled for automation."
                await interaction.followup.send(embed=embed)
                return

            for event in voice_events[:10]:  # Show max 10 events
                # Check if this event has a scheduled job
                has_job = any(job.id == f"event_{event.id}" for job in jobs)
                status_emoji = "✅" if has_job else "❌"

                channel_name = event.channel.name if event.channel else "Unknown Channel"

                embed.add_field(
                    name=f"{status_emoji} {event.name}",
                    value=(
                        f"**Start:** <t:{int(event.start_time.timestamp())}:F>\n"
                        f"**Channel:** {channel_name}\n"
                        f"**ID:** {event.id}"
                    ),
                    inline=False
                )

            if len(voice_events) > 10:
                embed.set_footer(text=f"Showing 10 of {len(voice_events)} events")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in list command: {e}")
            await interaction.followup.send(
                f"❌ Error listing events: {e}",
                ephemeral=True
            )

    async def start_event_command(self, interaction: discord.Interaction, event_id: str):
        """Manually start an event"""
        # Check permissions
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)
        # Temporarily disable permission check for testing
        # if not member or not member.guild_permissions.manage_events:
        #     await interaction.response.send_message(
        #         "❌ You need 'Manage Events' permission to use this command.",
        #         ephemeral=True
        #     )
        #     return

        await interaction.response.defer()

        try:
            event_id_int = int(event_id)
            await self.start_voice_event(event_id_int)

            # Get event name for response
            guild = self.get_guild(self.guild_id)
            event = guild.get_scheduled_event(event_id_int) if guild else None
            event_name = event.name if event else f"Event {event_id}"

            await interaction.followup.send(f"✅ Started event: **{event_name}**")

        except ValueError:
            await interaction.followup.send("❌ Invalid event ID format", ephemeral=True)
        except Exception as e:
            logger.error(f"Error manually starting event: {e}")
            await interaction.followup.send(f"❌ Error starting event: {e}", ephemeral=True)

    async def bot_status_command(self, interaction: discord.Interaction):
        """Show bot status"""
        jobs = self.scheduler.get_jobs()

        embed = discord.Embed(
            title="🤖 Bot Status",
            color=0x0099ff
        )

        embed.add_field(name="Guilds", value=len(self.guilds), inline=True)
        embed.add_field(name="Scheduled Jobs", value=len(jobs), inline=True)
        embed.add_field(name="Scheduler Status",
                       value="✅ Running" if self.scheduler.running else "❌ Stopped",
                       inline=True)

        if jobs:
            next_job = min(jobs, key=lambda j: j.next_run_time)
            embed.add_field(
                name="Next Event",
                value=f"<t:{int(next_job.next_run_time.timestamp())}:R>",
                inline=True
            )

        await interaction.response.send_message(embed=embed)

async def main():
    """Main function to run the bot"""
    # Check environment variables
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    guild_id = os.getenv('GUILD_ID')

    if not bot_token:
        print("❌ ERROR: DISCORD_BOT_TOKEN environment variable is required!")
        print("Please copy .env.example to .env and add your bot token.")
        return

    if not guild_id:
        print("❌ ERROR: GUILD_ID environment variable is required!")
        print("Please add your Discord server ID to the .env file.")
        return

    # Create and run bot
    bot = VoiceEventBot()

    try:
        await bot.start(bot_token)
    except KeyboardInterrupt:
        logger.info("Shutting down bot...")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())