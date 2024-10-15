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

INITIAL_EVENT_NUMBER = 69  # Hard-coded starting event number

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


    # Initialize bot variables
    bot.canceled_this_week = False
    bot.previous_post = None
    bot.current_event_number = INITIAL_EVENT_NUMBER  # Start at 70 on bot's first run

    # Set up the scheduler to run every Wednesday at 8:30 AM PST
    pst = pytz.timezone('America/Los_Angeles')
    scheduler.add_job(
        scheduled_task_wrapper,
        CronTrigger(day_of_week='wed', hour=8, minute=30, timezone=pst)
    )

    # Set up the scheduler to run every minute for testing
    # scheduler.add_job(
    #     scheduled_task_wrapper,
    #     CronTrigger(minute='*/1')  # Runs every minute
    # )


    scheduler.start()

async def scheduled_task_wrapper():
    # Increment the event number
    bot.current_event_number += 1
    print(f'Event number incremented to {bot.current_event_number}')

    await check_attendees()

async def check_attendees():
    # Check if admin has canceled the run for this week
    if bot.canceled_this_week:
        print('Run canceled for this week.')
        return

    channel = bot.get_channel(1193295598166737118) # Hard-coded waitlist channel ID

    if channel is None:
        print('Channel not found. Please check the channel ID.')
        return

    # Updated GraphQL query
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

        while attendee_count < 32:
            try:
                # Construct variables with the current event number
                variables = {
                    "slug": f"tournament/microspacing-vancouver-{bot.current_event_number}/event/ultimate-singles"
                }

                async with session.post(
                    'https://api.start.gg/gql/alpha',
                    json={'query': query, 'variables': variables},
                    headers=headers
                ) as resp:
                    data = await resp.json()

                    # Check if the event exists
                    if data.get('data') and data['data'].get('event'):
                        attendee_count = data['data']['event']['numEntrants']
                        print(f'Current entrants: {attendee_count}')
                    else:
                        print(f"Event not found for event number {bot.current_event_number}.")
                        break  # Exit the loop if the event doesn't exist
            except Exception as e:
                print(f'Error fetching data: {e}')
                await asyncio.sleep(30)
                continue

            if attendee_count >= 32:
                # Lock the previous week's post
                if bot.previous_post:
                    await bot.previous_post.edit(locked=True)

                # Create a new post
                title = f'Waitlist for MSV#{bot.current_event_number}'
                content = (
                    'Answer in the thread if you\'d like to be added to the waitlist!\n\n'
                    'Top 8 of this waitlist get priority registration for next week. '
                    'Please, let me know if you are bringing a setup. For example, "Dantotto setup"'
                )

                new_thread = await channel.create_thread(name=title, content=content)
                bot.previous_post = new_thread.thread  # Update previous_post
                break

            await asyncio.sleep(30)  # Wait for 30 seconds before checking again

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
async def set_event_number(ctx, number: int):
    bot.current_event_number = number
    await ctx.send(f'Current event number updated to {bot.current_event_number}. Note, next run will apply to {bot.current_event_number + 1}')

bot.run(DISCORD_TOKEN)
