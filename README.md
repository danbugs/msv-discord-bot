
# Microspacing Vancouver Discord Bot

> Note: This project was developed during Microsoft Vancouver's 2024 Hackathon!

A Discord bot that automates the management of Microspacing Vancouver (MSV) events.

## Commands

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

- **`!set_reg_time`** (must be admin)
  - **Description**: Sets the time for the weekly announcement. The default is set to *;30 AM on Wednesdays.
  - **Usage**: `!set_reg_time wed_8_30` (for Wednesday, 8:30 AM)

- **`!do_pre_tournament_setup`** (must be admin)
  - **Description**: Performs the pre-tournament setup, including:
    - Locking the previous waitlist post.
    - Creating necessary threads (pri. reg., top 8, dropping out, etc.)
  - **Usage**: `!do_pre_tournament_setup`

- **`!quote`**
  - **Description**: Displays a random quote from a public channel in the server.
    - **Usage**: `!quote`

- **`!thanks`**
  - **Description**: Displays a random "You're welcome!"-like message.
    - **Usage**: `!thanks`

- **`!test`** (must be admin)
  - **Description**: Simulates the bot's functionality for testing purposes:
    - Locks the previous waitlist post (if any).
    - Posts the announcement to a test channel.
    - Creates a waitlist thread in a test channel.
  - **Usage**: `!test`

- **`!roll_dice`**
  - **Description**: Rolls a random number between 1 and 6.
  - **Usage**: `!roll_dice`

- **`!who_is_da_goat`**
  - **Description**: Picks a random member from the server and declares them the "Greatest of All Time" (GOAT).
  - **Usage**: `!who_is_the_goat`

- **`!batch`** (must be admin)
  - **Description**: Batch a bunch of commands together to be executed serially and stop if any fail.
  - **Usage**:
  ```
  !batch {
  !check_current_event
  !set_current_event https://www.start.gg/tournament/macrospacing-vancouver-5-battle-of-bc-7-monday-pre-local/event/ultimate-singles

  !set_attendee_cap 64
  !set_reg_time wed_8_30

  !check_current_event
  }
  ```
  
- **`!yes_or_no`**
  - **Description**: Randomly responds with "yes" or "no".
  - **Usage**: `!yes_or_no`

## Other Features

- **Weekly Announcements**: Posts a detailed registration announcement in a dedicated channel when scheduled.
- **Random posts**: Randomly posts pre-determined messages in general.

## Note on Tokens and Deployment

The Start.gg token this bot uses (i.e., `waitlist-bot` in the Dantotto profile) was created around October 2024. The token should be updated around August 2025 at the latest by changing the `.env` file in the deployed Ubuntu server and re-running PM2 with the following command:

```bash
pm2 restart <some num> --update-env
```
