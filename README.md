
# Microspacing Vancouver Discord Bot

> Note: This project was developed during Microsoft Vancouver's 2024 Hackathon!

A Discord bot that automates the management of Microspacing Vancouver (MSV) events.

## What the Bot Does

- **Monitors Event Registrations**: Checks the number of entrants for MSV events on Start.gg using a configurable event URL.
- **Creates Waitlist Threads**: Automatically creates a new waitlist thread in the MSV Discord server when the entrant cap is reached (default: 32, but configurable).
- **Locks Previous Threads**: Locks the previous waitlist thread every Tuesday, notifying users with a message that a new one will be created once the next event caps.
- **Announcements**: Posts an announcement every Wednesday morning, providing registration details and encouraging attendees to bring setups.
- **Administrator Commands**: Provides commands for admins to control and configure the bot's behavior.
- **Testing and Cleanup**: Includes commands for testing the bot's functionality and resetting its state for accurate operation.

## Administrator Commands

- **`!set_current_event <url>`** (must be admin)
  - **Description**: Sets the current event Start.gg URL that the bot will monitor.
  - **Usage**: `!set_current_event https://www.start.gg/tournament/microspacing-vancouver-77/event/ultimate-singles`

- **`!set_attendee_cap <number>`** (must be admin)
  - **Description**: Sets the maximum number of entrants for the current event (default: 32).
  - **Usage**: `!set_attendee_cap 40`

- **`!check_current_event`**
  - **Description**: Displays the current event details, including URL, attendee cap, and whether the bot’s operations are currently canceled.
  - **Usage**: `!check_current_event`

- **`!cancel_run`** (must be admin)
  - **Description**: Cancels the bot's operations until resumed.
  - **Usage**: `!cancel_run`

- **`!resume_run`** (must be admin)
  - **Description**: Resumes the bot's operations after a cancellation.
  - **Usage**: `!resume_run`

- **`!test`** (must be admin)
  - **Description**: Simulates the bot's functionality for testing purposes:
    - Locks the previous waitlist post (if any).
    - Posts the announcement to a test channel.
    - Creates a waitlist thread in a test channel.
  - **Usage**: `!test`

- **`!clean_previous_post`** (must be admin)
  - **Description**: Cleans up the bot's reference to the previous waitlist post, ensuring test runs do not affect actual operations.
  - **Usage**: `!clean_previous_post`

## Other Features

- **Weekly Announcements**: Posts a detailed registration announcement in a dedicated channel every Wednesday morning.
- **Automatic Thread Management**: Locks previous waitlist threads and creates new ones dynamically based on event registration status.
- **Fun Additions**: Includes a `!roll_dice` command for entertainment, rolling a random number between 1 and 6.

## Note on Tokens and Deployment

The Start.gg token this bot uses (i.e., `waitlist-bot` in the Dantotto profile) was created around October 2024. The token should be updated around August 2025 at the latest by changing the `.env` file in the deployed Ubuntu server and re-running PM2 with the following command:

```bash
pm2 restart 6 --update-env
```
