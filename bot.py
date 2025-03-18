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
import random


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

    if not hasattr(bot, "random_message_task_started"):
        bot.loop.create_task(random_general_messages())
        bot.random_message_task_started = True

    # Initialize bot variables
    bot.current_event_slug = None
    bot.attendee_cap = DEFAULT_ATTENDEE_CAP
    bot.registration_day = "wed"
    bot.registration_hour = 8
    bot.registration_minute = 30

    # Set up scheduled jobs
    await setup_scheduled_jobs()

async def setup_scheduled_jobs():
    pst = pytz.timezone('America/Los_Angeles')
    scheduler.remove_all_jobs()

    scheduler.add_job(
        scheduled_task_wrapper,
        CronTrigger(
            day_of_week=bot.registration_day,
            hour=bot.registration_hour,
            minute=bot.registration_minute,
            timezone=pst
        )
    )
    scheduler.start()

    # Send confirmation message to channel
    announce_channel = bot.get_channel(1317322917129879562)
    if announce_channel:
        await announce_channel.send("✅ I am running the scheduler.")
    else:
        print("Announce channel not found.")

# lock all threads when provided with an ID
async def lock_all_threads_in_channel(ctx, channel_id):
    forum_channel = bot.get_channel(channel_id)

    if not forum_channel:
        await ctx.send("Forum channel not found.")
        return

    active_threads = await ctx.guild.active_threads()
    locked_count = 0

    for thread in active_threads:
        if thread.parent_id == forum_channel.id and not thread.locked:
            await thread.edit(locked=True)
            await ctx.send(f"Locked thread: {thread.name}")
            locked_count += 1

    await ctx.send(f"✅ Locked {locked_count} thread(s) in that forum channel.")

def shorten_slug(slug: str) -> str:
    # Example slug: tournament/microspacing-vancouver-87/event/ultimate-singles
    parts = slug.split('/')
    if len(parts) >= 4:
        return f"{parts[1]}/{parts[3]}"
    return slug  # fallback if unexpected format

def truncate_to_100_chars(s: str) -> str:
    if len(s) < 100:
        return s
    return s[:96] + "..."

@bot.command()
@commands.has_permissions(administrator=True)
async def do_pre_tournament_setup(ctx):
    try:
        # Lock the unlocked waitlist posts, if any exist
        await lock_all_threads_in_channel(ctx, 1193295598166737118)

        # (1) Create Top 8 Graphic thread
        top8_channel_id = 1193298151503831163
        await lock_all_threads_in_channel(ctx, top8_channel_id)
        top8_channel = bot.get_channel(top8_channel_id)
        if top8_channel:
            title = truncate_to_100_chars(f"Top 8 graphic for {shorten_slug(bot.current_event_slug)}")
            content = "Reply below w/ your characters and alts for the top 8"
            await top8_channel.create_thread(name=title, content=content)
            await ctx.send("Top 8 graphic thread created.")
        else:
            await ctx.send("Top 8 channel not found.")

        # (2) Create Dropping Out thread
        dropout_channel_id = 1193304496583999588
        await lock_all_threads_in_channel(ctx, dropout_channel_id)
        dropout_channel = bot.get_channel(dropout_channel_id)
        if dropout_channel:
            title = truncate_to_100_chars(f"Dropping Out from {shorten_slug(bot.current_event_slug)}?")
            content = "Let me know below!"
            if bot.attendee_cap == 32:
                content += (
                    "\n\nThe deadline to drop-out without penalty is 9AM on Monday. "
                    "If you drop out after 9AM but before 3PM, you're banned from next event. "
                    "If you drop out after 3PM, you're banned from the next 2 events. "
                    "For more details, see #faq ."
                )
            if bot.attendee_cap == 64:
                content += (
                    "\n\nThe deadline to drop-out without penalty is Sunday midnight. "
                )
            await dropout_channel.create_thread(name=title, content=content)
            await ctx.send("Drop-out thread created.")
        else:
            await ctx.send("Drop-out channel not found.")

        # (3) Create Priority Registration thread
        pri_reg_channel_id = 1194324348014698496
        await lock_all_threads_in_channel(ctx, pri_reg_channel_id)
        pri_reg_channel = bot.get_channel(pri_reg_channel_id)
        if pri_reg_channel:
            title = truncate_to_100_chars(f"Pri. Reg. for {shorten_slug(bot.current_event_slug)}")
            if bot.attendee_cap == 32:
                content = (
                    "If you were in the top 8 for the waitlist for this last micro event, "
                    "you have priority registration for next week, so, if you can make it, "
                    "I'll add you to bracket!~ just let me know before Wednesday 'cause reg. goes live then."
                )
            else:
                content = "See below!"
            await pri_reg_channel.create_thread(name=title, content=content)
            await ctx.send("Priority registration thread created.")
        else:
            await ctx.send("Priority registration channel not found.")

        await ctx.send("All lock and thread creation operations completed successfully. Don't forget to lock old remaining threads!")

    except Exception as e:
        await ctx.send(f"An error occurred during lock and thread creation: {e}")

async def scheduled_task_wrapper(
    announcement_channel_override: discord.TextChannel = None,
    waitlist_channel_override: discord.TextChannel = None):
    if not bot.current_event_slug:
        print('No current event slug set.')
        return

    # Post the announcement
    announcement_channel = announcement_channel_override or bot.get_channel(1066863301885173800)
    if announcement_channel:
        message = (
            f"@everyone ~ registration for next week's event is open!\n\n"
            f"- {bot.attendee_cap} player cap.\n"
            f"- for venue access, see: #how-to-get-to-the-venue .\n"
            f"- **:warning: BRING YOUR NINTENDO SWITCHES (DOCK, CONSOLE, POWER CABLE, AND HDMI) WITH GAME CUBE ADAPTERS :warning:** "
        )

        if bot.attendee_cap == 32:
            message += (
                f"(running Swiss is dependent on having at least 20 setups; otherwise, we'll do normal Redemption). We've got monitors.\n"
            )

        message += (
            f"- if you are trying to register, but we’ve already reached the cap, please drop your StartGG tag "
            f"(and say if you can bring a setup) at #add-me-to-the-waitlist once it opens. Are you from out-of-region? If so, you have priority in the waitlist!\n\n"
            f"PS If you can’t bring a full setup, but would still like to contribute, _please bring your GCC adapter_. "
            f"There are some people that can bring full setups but only play w/ pro cons., so it’s always best to have extras.\n\n"
            f"https://start.gg/{bot.current_event_slug}"
        )

        await announcement_channel.send(message)


    # Check attendees
    await check_attendees(waitlist_channel_override)

async def check_attendees(
    waitlist_channel_override: discord.TextChannel = None
):
    channel = waitlist_channel_override or bot.get_channel(1193295598166737118)

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

    slug_to_use = (
        "tournament/macrospacing-vancouver-4/event/ultimate-singles"
        if waitlist_channel_override
        else bot.current_event_slug
    )

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
                    "slug": slug_to_use
                }

                async with session.post(
                    'https://api.start.gg/gql/alpha',
                    json={'query': query, 'variables': variables},
                    headers=headers
                ) as resp:
                    data = await resp.json()

                    if data.get('data') and data['data'].get('event'):
                        attendee_count = data['data']['event']['numEntrants']
                        print(f'Current entrants (slug: {slug_to_use}): {attendee_count}')
                    else:
                        print(f"Event not found for slug: {slug_to_use}.")
                        break
            except Exception as e:
                print(f'Error fetching data: {e}')
                await asyncio.sleep(30)
                continue

            if attendee_count >= bot.attendee_cap:
                title = truncate_to_100_chars(f'Waitlist for {shorten_slug(slug_to_use)}')
                content = (
                    'Answer in the thread if you\'d like to be added to the waitlist!\n\n'
                )

                if bot.attendee_cap == 32:
                    content += (
                        'Top 8 of this waitlist get priority registration for next week. '
                    )

                content += (
                    'Please, let me know if you are bringing a setup. For example, "Dantotto setup"'
                )

                await channel.create_thread(name=title, content=content)
                break  # Important: break here once thread is created

            await asyncio.sleep(30)  # Wait before checking again

@bot.command()
@commands.has_permissions(administrator=True)
async def set_reg_time(ctx, time_str: str):
    try:
        parts = time_str.lower().split("_")
        if len(parts) != 3:
            await ctx.send("Invalid format! Use: `!set_reg_time <day>_<hour>_<minute>`, e.g., `!set_reg_time wed_8_30`")
            return

        day, hour, minute = parts
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        if day not in days:
            await ctx.send("Invalid day! Use one of: mon, tue, wed, thu, fri, sat, sun.")
            return

        hour = int(hour)
        minute = int(minute)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            await ctx.send("Invalid time! Hour must be 0-23 and minute 0-59.")
            return

        bot.registration_day = day
        bot.registration_hour = hour
        bot.registration_minute = minute

        setup_scheduled_jobs()

        await ctx.send(f"Registration scheduler updated: registration announcement every **{day}** at **{hour}:{minute:02d} PST**.")

    except Exception as e:
        await ctx.send(f"Failed to update registration time: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def set_current_event(ctx, url: str):
    bot.current_event_slug = '/'.join(url.split('/')[-4:])  # Extracts the slug from the URL
    await ctx.send(f'Current event set to: {bot.current_event_slug}')

@bot.command()
@commands.has_permissions(administrator=True)
async def set_attendee_cap(ctx, cap: int):
    #
    bot.attendee_cap = cap
    await ctx.send(f'Attendee cap set to: {bot.attendee_cap}')

@bot.command()
async def check_current_event(ctx):
    await ctx.send(
        f"Current event details:\n"
        f"- URL: {bot.current_event_slug or 'Not set'}\n"
        f"- Attendee cap: {bot.attendee_cap}\n"
        f"- Registration time: {bot.registration_day} at {bot.registration_hour}:{bot.registration_minute:02d} PST\n"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def cancel_run(ctx):
    bot.current_event_slug = None
    await ctx.send('The bot will no longer run until `!set_current_event` is called.')

@bot.command()
@commands.has_permissions(administrator=True)
async def test(ctx):
    try:
        test_announcement_channel = bot.get_channel(1317322763043864616)
        test_waitlist_channel = bot.get_channel(1317322581938016317)

        if not test_announcement_channel or not test_waitlist_channel:
            await ctx.send("Test announcement or waitlist channels not found.")
            return

        await ctx.send("Running full test cycle...")
        await scheduled_task_wrapper(
            announcement_channel_override=test_announcement_channel,
            waitlist_channel_override=test_waitlist_channel
        )
        await ctx.send("Test cycle completed successfully.")

    except Exception as e:
        await ctx.send(f"Test failed with error: {e}")

@bot.command()
async def roll_dice(ctx):
    import random
    result = random.randint(1, 6)
    await ctx.send(f'🎲 You rolled a {result}!')

@bot.command()
async def quote(ctx):
    try:
        general_channel = bot.get_channel(1066863005591162961)
        if not general_channel:
            await ctx.send("I couldn't find the general channel.")
            return

        # Fetch recent messages (last 200), skipping bot messages and empty content
        messages = [
            msg async for msg in general_channel.history(limit=200)
            if not msg.author.bot and msg.content.strip()
        ]
        if not messages:
            await ctx.send("I couldn't find anything interesting to quote in #general.")
            return

        message = random.choice(messages)
        await ctx.send(
            f'📜 Random quote from **{message.author.display_name}** in #general:\n"> {message.content}"'
        )

    except Exception as e:
        await ctx.send(f"Something went wrong: {e}")

@bot.command()
async def thanks(ctx):
    responses = [
        "No worries!",
        "You're welcome!",
        "Anytime 😎",
        "All good!",
        "You got it!",
        "np 👍"
    ]
    await ctx.send(random.choice(responses))

@bot.command()
async def who_is_da_goat(ctx):
    try:
        active_members = set()
        general_channel = bot.get_channel(1066863005591162961)
        async for msg in general_channel.history(limit=500):
            if not msg.author.bot:
                active_members.add(msg.author)

        if not active_members:
            await ctx.send("I couldn't find anyone active... I guess I'm the goat 😎!")
            return

        goat = random.choice(list(active_members))
        await ctx.send(f"🐐 The GOAT is... **{goat.display_name}** (based on recent activity)!")
    except Exception as e:
        await ctx.send(f"Something went wrong: {e}")

async def random_general_messages():
    await bot.wait_until_ready()
    general_channel = bot.get_channel(1066863005591162961)
    random_messages = [
        "Hey, everyone! 👋",
        "Remember to hydrate! 💧",
        "Who's cooking up something spicy in bracket next week? 🔥",
        "Did you practice today? 🎮",
        "The setups don't set themselves up 😏",
        "Shoutout to everyone grinding! 🫡"
    ]
    while not bot.is_closed():
        wait_time = random.randint(48 * 60 * 60, 72 * 60 * 60)  # between 48 and 72 hours
        await asyncio.sleep(wait_time)

        if general_channel:
            try:
                await general_channel.send(random.choice(random_messages))
            except Exception as e:
                print(f"Failed to send random message: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def batch(ctx, *, block: str):
    try:
        # Strip surrounding braces if present
        block = block.strip()
        if block.startswith("{") and block.endswith("}"):
            block = block[1:-1].strip()

        # Split commands by line
        commands_list = [line.strip() for line in block.splitlines() if line.strip()]

        if not commands_list:
            await ctx.send("No commands found in batch.")
            return

        await ctx.send(f"Running batch of {len(commands_list)} commands...")

        for command_line in commands_list:
            if not command_line.startswith("!"):
                await ctx.send(f"Skipping invalid line (does not start with '!'): `{command_line}`")
                continue

            await ctx.send(f"🔹 Running `{command_line}`")

            # Simulate a user message with that exact command line in the same channel
            fake_message = ctx.message
            # Create a new Message object like the bot received
            fake_message.content = command_line
            new_ctx = await bot.get_context(fake_message)

            # Call the command and stop if errors occur
            try:
                await bot.invoke(new_ctx)
            except Exception as e:
                await ctx.send(f"Command `{command_line}` failed with error: {e}. Stopping batch.")
                return

        await ctx.send("✅ Batch completed successfully.")

    except Exception as e:
        await ctx.send(f"Batch failed with error: {e}")


@bot.command()
async def yes_or_no(ctx):
    responses = ["Yes", "No"]
    await ctx.send(random.choice(responses))

bot.run(DISCORD_TOKEN)
