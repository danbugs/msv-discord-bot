# Microspacing Vancouver Discord Bot

> Note: This project was developed during Microsoft Vancouver's 2024 Hackathon!

A Discord bot that automates the management for Microspacing Vancouver (MSV) events.

## What the Bot Does

- **Monitors Event Registrations**: Checks the number of entrants for MSV events on Start.gg.
- **Creates Waitlist Threads**: Automatically creates a new waitlist thread in the MSV Discord server when the entrant cap (32) is reached.
- **Locks Previous Threads**: Locks the previous waitlist thread to prevent further entries.
- **Administrator Commands**: Provides commands for admins to control the bot's behavior.

## Administrator Commands

- **`!cancel_run`**
  - **Description**: Cancels the bot's operations until resumed.
  - **Usage**: `!cancel_run`

- **`!resume_run`**
  - **Description**: Resumes the bot's operations after a cancellation.
  - **Usage**: `!resume_run`

- **`!set_event_number <number>`**
  - **Description**: Manually sets the current event number.
  - **Usage**: `!set_event_number 70`

> Note to self: The StartGG token this bot uses (i.e., `waitlist-bot` in Dantotto profile) was created around October 2024, the token should be updated around August 2025 at the latest by changing the `.env` file in the deployed Ubuntu server and re-running pm2 (`pm2 restart 6 --update-env`).