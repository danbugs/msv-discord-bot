import os
import discord
import asyncio
import aiohttp
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import pytz
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
DISCORD_TOKEN = os.getenv('BALROG_DISCORD_TOKEN')
STARTGG_TOKEN = os.getenv('BALROG_STARTGG_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
scheduler = AsyncIOScheduler()

DEFAULT_ATTENDEE_CAP = 32

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    # Initialize bot variables
    bot.canceled_this_week = False
    bot.previous_post = None
    bot.current_event_slug = None
    bot.attendee_cap = DEFAULT_ATTENDEE_CAP

    # Set up the scheduler to run every Tuesday at 8:30 AM PST for locking previous posts
    pst = pytz.timezone('America/Los_Angeles')
    scheduler.add_job(
        lock_previous_post,
        CronTrigger(day_of_week='tue', hour=8, minute=30, timezone=pst)
    )

    # Set up the scheduler to run every Wednesday at 8:30 AM PST for announcements and checks
    scheduler.add_job(
        scheduled_task_wrapper,
        CronTrigger(day_of_week='wed', hour=8, minute=30, timezone=pst)
    )

    scheduler.start()

async def lock_previous_post():
    if bot.previous_post:
        await bot.previous_post.edit(locked=True)
        await bot.previous_post.send("Waitlist locked, new one will be created once the next event caps.")
        print("Locked the previous waitlist thread.")

async def scheduled_task_wrapper():
    if bot.canceled_this_week:
        print('Run canceled for this week.')
        return

    if not bot.current_event_slug:
        print('No current event slug set.')
        return

    # Post the announcement
    announcement_channel = bot.get_channel(1066863301885173800)
    if announcement_channel:
        await announcement_channel.send(
            f"@everyone ~ registration for next week's event is open!\n\n"
            f"- {bot.attendee_cap} player cap.\n"
            f"- public reg goes out tomorrow at 8:30AM (if cap isn't hit).\n"
            f"- for venue access, see: #how-to-get-to-the-venue .\n"
            f"- **:warning: BRING YOUR NINTENDO SWITCHES (DOCK, CONSOLE, POWER CABLE, AND HDMI) WITH GAME CUBE ADAPTERS :warning:** "
            f"(running Swiss is dependent on having at least 20 setups; otherwise, we'll do normal Redemption). We've got monitors.\n"
            f"- if you are trying to register, but we’ve already reached the cap, please drop your StartGG tag "
            f"(and say if you can bring a setup) at #add-me-to-the-waitlist once it opens. Are you from out-of-region? If so, you have priority in the waitlist!\n\n"
            f"PS If you can’t bring a full setup, but would still like to contribute, _please bring your GCC adapter_. "
            f"There are some people that can bring full setups but only play w/ pro cons., so it’s always best to have extras.\n\n"
            f"https://start.gg/{bot.current_event_slug}"
        )

    # Check attendees
    await check_attendees()

async def check_attendees():
    channel = bot.get_channel(1193295598166737118)  # Hard-coded waitlist channel ID

    if channel is None:
        print('Channel not found. Please check the channel ID.')
        return

    query = '''
    query getEventEntrants($slug: String!) {
      event(slug: $slug) {
        numEntrants
      }
    }
    '''

    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f'Bearer {STARTGG_TOKEN}',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }

        attendee_count = 0

        while attendee_count < bot.attendee_cap:
            try:
                variables = {
                    "slug": bot.current_event_slug
                }

                async with session.post(
                    'https://api.start.gg/gql/alpha',
                    json={'query': query, 'variables': variables},
                    headers=headers
                ) as resp:
                    data = await resp.json()

                    if data.get('data') and data['data'].get('event'):
                        attendee_count = data['data']['event']['numEntrants']
                        print(f'Current entrants: {attendee_count}')
                    else:
                        print(f"Event not found for slug: {bot.current_event_slug}.")
                        break
            except Exception as e:
                print(f'Error fetching data: {e}')
                await asyncio.sleep(30)
                continue

            if attendee_count >= bot.attendee_cap:
                if bot.previous_post:
                    await bot.previous_post.edit(locked=True)
                    await bot.previous_post.send("Waitlist locked, new one will be created once the next event caps.")

                title = f'Waitlist for {bot.current_event_slug}'
                content = (
                    'Answer in the thread if you\'d like to be added to the waitlist!\n\n'
                    'Top 8 of this waitlist get priority registration for next week. '
                    'Please, let me know if you are bringing a setup. For example, "Dantotto setup"'
                )

                new_thread = await channel.create_thread(name=title, content=content)
                bot.previous_post = new_thread.thread
                break

            await asyncio.sleep(30)  # Wait for 30 seconds before checking again

@bot.command()
@commands.has_permissions(administrator=True)
async def set_current_event(ctx, url: str):
    bot.current_event_slug = '/'.join(url.split('/')[-4:])  # Extracts the slug from the URL
    await ctx.send(f'Current event set to: {bot.current_event_slug}')

@bot.command()
@commands.has_permissions(administrator=True)
async def set_attendee_cap(ctx, cap: int):
    bot.attendee_cap = cap
    await ctx.send(f'Attendee cap set to: {bot.attendee_cap}')

@bot.command()
async def check_current_event(ctx):
    await ctx.send(
        f"Current event details:\n"
        f"- URL: {bot.current_event_slug or 'Not set'}\n"
        f"- Attendee cap: {bot.attendee_cap}\n"
        f"- Run canceled: {bot.canceled_this_week}"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def cancel_run(ctx):
    bot.canceled_this_week = True
    await ctx.send('The bot will no longer run until `!resume_run` is called.')

@bot.command()
@commands.has_permissions(administrator=True)
async def resume_run(ctx):
    bot.canceled_this_week = False
    await ctx.send('The bot has been resumed.')

@bot.command()
@commands.has_permissions(administrator=True)
async def clean_previous_post(ctx):
    """
    Cleans the `previous_post` reference to avoid conflicts between test and actual runs.
    """
    try:
        if bot.previous_post:
            bot.previous_post = None
            await ctx.send("Previous post reference cleared successfully.")
        else:
            await ctx.send("No previous post reference to clean.")
    except Exception as e:
        await ctx.send(f"An error occurred while cleaning previous post reference: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def test(ctx):
    """
    Tests the following functionality:
    - Locks the previous waitlist post (if any).
    - Posts the announcement in a designated test channel.
    - Creates a waitlist post in a designated test channel.
    """
    try:
        # Lock the previous waitlist post (if any)
        if bot.previous_post:
            await bot.previous_post.edit(locked=True)
            await bot.previous_post.send(
                "Waitlist locked (test mode). A new one will be created once the next event caps."
            )
            await ctx.send("Previous waitlist locked successfully (test mode).")
        else:
            await ctx.send("No previous waitlist post to lock (test mode).")

        # Post the announcement in a test channel
        test_announcement_channel = bot.get_channel(1317322763043864616)  # Replace with your test announcement channel ID
        if test_announcement_channel:
            await test_announcement_channel.send(
                f"@everyone ~ registration for next week's event is open! (TEST MODE)\n\n"
                f"- {bot.attendee_cap} player cap.\n"
                f"- public reg goes out tomorrow at 8:30AM (if cap isn't hit).\n"
                f"- for venue access, see: #how-to-get-to-the-venue .\n"
                f"- **:warning: BRING YOUR NINTENDO SWITCHES (DOCK, CONSOLE, POWER CABLE, AND HDMI) WITH GAME CUBE ADAPTERS :warning:** "
                f"(running Swiss is dependent on having at least 20 setups; otherwise, we'll do normal Redemption). We've got monitors.\n"
                f"- if you are trying to register, but we’ve already reached the cap, please drop your StartGG tag "
                f"(and say if you can bring a setup) at #add-me-to-the-waitlist once it opens. Are you from out-of-region? If so, you have priority in the waitlist!\n\n"
                f"PS If you can’t bring a full setup, but would still like to contribute, _please bring your GCC adapter_. "
                f"There are some people that can bring full setups but only play w/ pro cons., so it’s always best to have extras.\n\n"
                f"https://www.start.gg/{bot.current_event_slug or 'test-event'}"
            )
            await ctx.send("Test announcement posted successfully.")

        # Create a new waitlist post in a test channel
        test_waitlist_channel = bot.get_channel(1317322581938016317)  # Replace with your test waitlist channel ID
        if test_waitlist_channel:
            title = f"Waitlist for {bot.current_event_slug or 'Test Event'} (TEST MODE)"
            content = (
                "Answer in the thread if you'd like to be added to the waitlist! (TEST MODE)\n\n"
                "Top 8 of this waitlist get priority registration for next week. "
                "Please, let me know if you are bringing a setup. For example, 'TestUser setup'"
            )
            new_thread = await test_waitlist_channel.create_thread(name=title, content=content)
            bot.previous_post = new_thread  # Update the previous post for testing
            await ctx.send("Test waitlist thread created successfully.")

        await ctx.send("All test operations completed successfully.")

    except Exception as e:
        await ctx.send(f"An error occurred during the test: {e}")    

@bot.command()
async def roll_dice(ctx):
    import random
    result = random.randint(1, 6)
    await ctx.send(f'🎲 You rolled a {result}!')    

bot.run(DISCORD_TOKEN)
