# Discord Economy Bot

A Discord bot implementing an economy system and role shop using SQLite for data storage. The bot allows managing user balances, purchasing roles, adding reputation, and displaying leaderboards.

## Features
- **Balance Management**: Check balance (`!balance`), award funds (`!award`), and deduct funds (`!take`).
- **Role Shop**: Add (`!add-shop`), remove (`!remove-shop`), and purchase roles (`!buy`).
- **Reputation**: Add reputation to other users (`!rep`).
- **Leaderboard**: Display the top 10 users by balance (`!leaderboard`).
- **Paginated Shop**: View roles in the shop with pagination (`!shop`).

## Requirements
- Python 3.8+
- Libraries:
  - `discord.py`
  - `sqlite3` (built into Python)
  - `python-dotenv` (recommended for secure token storage)

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/0xRaiseX/Discord-Economy-Bot.git
   cd Discord-Economy-Bot
   ```

2. **Install dependencies**:
   ```bash
   pip install discord.py python-dotenv
   ```

3. **Create a `.env` file**:
   In the root directory, create a `.env` file and add your bot token:
   ```
   DISCORD_TOKEN=your_bot_token
   ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```

## Usage
### Commands
- `!balance [@user]`: Shows the balance of the specified user (or yourself if no user is mentioned).
- `!award @user <amount>`: Awards the specified amount to a user (admin only).
- `!take @user <amount|all>`: Deducts the specified amount or all funds from a user (admin only).
- `!add-shop @role <cost>`: Adds a role to the shop (admin only).
- `!remove-shop @role`: Removes a role from the shop (admin only).
- `!buy @role`: Purchases a role from the shop.
- `!rep @user`: Adds 1 reputation point to a user.
- `!leaderboard`: Displays the top 10 users by balance.
- `!shop`: Shows the role shop with pagination (reactions for navigation: ⏮, ◀, ▶, ⏭).

### Notes
- The bot requires `manage_roles` permissions to assign roles and `manage_messages` for shop pagination.
- All commands include error handling for permissions and invalid inputs.

## Database Structure
The bot uses SQLite (`server.db`) with two tables:
1. **users**:
   - `name`: User name (text).
   - `id`: User ID (integer).
   - `cash`: Balance (integer).
   - `rep`: Reputation (integer).
   - `lvl`: Level (integer).
   - `server_id`: Server ID (integer).
2. **shop**:
   - `role_id`: Role ID (integer).
   - `server_id`: Server ID (integer).
   - `cost`: Role cost (integer).
   - `category`: Role category (text, currently set to `default`).

## Known Issues and Recommendations
- **Database Connection**: The SQLite connection is not closed, which may cause issues during long-term operation. Use a context manager (`with sqlite3.connect(...)`) for queries.
- **Duplicate Role Check**: The `!add-shop` command does not check if a role already exists in the shop. Add a check before inserting.
- **Negative Balance**: The `!take` command allows balances to go negative. Add a check to prevent this.
- **Logging**: Errors are printed to the console. Use the `logging` library to log errors to a file.
- **Help Command**: No built-in `!help` command exists. Consider implementing one for user convenience.

## License
MIT License. See the `LICENSE` file for details.