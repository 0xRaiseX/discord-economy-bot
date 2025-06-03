import sqlite3
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from uuid import uuid4
from dotenv import load_dotenv
import os

# Инициализация бота с префиксом и намерениями
Bot = commands.Bot(command_prefix="!", intents=discord.Intents.default() | discord.Intents.members)
Bot.remove_command('help')

# Подключение к базе данных
connection = sqlite3.connect('server.db')
cursor = connection.cursor()

@Bot.event
async def on_ready():
    """Инициализация базы данных и синхронизация пользователей при запуске бота."""
    try:
        # Создание таблицы users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                name TEXT,
                id INTEGER,
                cash BIGINT,
                rep INTEGER,
                lvl INTEGER,
                server_id INTEGER
            )
        """)
        
        # Создание единой таблицы shop с полем category
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop (
                role_id INTEGER,
                server_id INTEGER,
                cost BIGINT,
                category TEXT
            )
        """)
        
        # Синхронизация пользователей
        for guild in Bot.guilds:
            async for member in guild.fetch_members():
                if not cursor.execute("SELECT id FROM users WHERE id = ?", (member.id,)).fetchone():
                    cursor.execute(
                        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                        (str(member), member.id, 0, 0, 1, guild.id)
                    )
        connection.commit()
        print('Bot connected successfully')
    except sqlite3.Error as e:
        print(f"Database error during initialization: {e}")

@Bot.event
async def on_member_join(member):
    """Добавление нового участника в базу данных."""
    try:
        if not cursor.execute("SELECT id FROM users WHERE id = ?", (member.id,)).fetchone():
            cursor.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                (str(member), member.id, 0, 0, 1, member.guild.id)
            )
            connection.commit()
    except sqlite3.Error as e:
        print(f"Database error on member join: {e}")

@Bot.command(aliases=['balance', 'cash'])
async def balance(ctx, member: discord.Member = None):
    """Показывает баланс указанного пользователя."""
    try:
        member = member or ctx.author
        cash = cursor.execute("SELECT cash FROM users WHERE id = ?", (member.id,)).fetchone()
        if cash is None:
            await ctx.send(f"Пользователь {member.mention} не найден в базе данных.")
            return
        embed = discord.Embed(description=f"Баланс пользователя {member.mention} составляет **{cash[0]}** 💰")
        await ctx.send(embed=embed)
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")

@Bot.command(aliases=['award'])
@commands.has_permissions(administrator=True)
async def award(ctx, member: discord.Member = None, amount: int = None):
    """Начисляет указанную сумму пользователю (только для администраторов)."""
    try:
        if member is None:
            await ctx.send(f"{ctx.author.mention}, укажите пользователя для начисления.")
            return
        if amount is None:
            await ctx.send(f"{ctx.author.mention}, укажите сумму для начисления.")
            return
        if amount < 1:
            await ctx.send(f"{ctx.author.mention}, сумма должна быть больше 0.")
            return
        
        cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (amount, member.id))
        connection.commit()
        await ctx.message.add_reaction('✅')
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для выполнения команды.")

@Bot.command(aliases=['take'])
@commands.has_permissions(administrator=True)
async def take(ctx, member: discord.Member = None, amount: str = None):
    """Снимает указанную сумму с баланса пользователя (только для администраторов)."""
    try:
        if member is None:
            await ctx.send(f"{ctx.author.mention}, укажите пользователя для списания.")
            return
        if amount is None:
            await ctx.send(f"{ctx.author.mention}, укажите сумму для списания.")
            return
        
        if amount.lower() == 'all':
            cursor.execute("UPDATE users SET cash = 0 WHERE id = ?", (member.id,))
            connection.commit()
            await ctx.message.add_reaction('✅')
            return
        
        amount = int(amount)
        if amount < 1:
            await ctx.send(f"{ctx.author.mention}, сумма должна быть больше 0.")
            return
        
        cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?", (amount, member.id))
        connection.commit()
        await ctx.message.add_reaction('✅')
    except ValueError:
        await ctx.send(f"{ctx.author.mention}, укажите корректную сумму или 'all'.")
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для выполнения команды.")

@Bot.command(aliases=['add-shop'])
@commands.has_permissions(administrator=True)
async def add_shop(ctx, role: discord.Role = None, cost: int = None):
    """Добавляет роль в магазин (только для администраторов)."""
    try:
        if role is None:
            await ctx.send(f"{ctx.author.mention}, укажите роль для добавления в магазин.")
            return
        if cost is None:
            await ctx.send(f"{ctx.author.mention}, укажите стоимость роли.")
            return
        if cost < 0:
            await ctx.send(f"{ctx.author.mention}, стоимость роли не может быть отрицательной.")
            return
        
        cursor.execute(
            "INSERT INTO shop (role_id, server_id, cost, category) VALUES (?, ?, ?, ?)",
            (role.id, ctx.guild.id, cost, 'default')
        )
        connection.commit()
        await ctx.message.add_reaction('✅')
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для выполнения команды.")

@Bot.command(aliases=['remove-shop'])
@commands.has_permissions(administrator=True)
async def remove_shop(ctx, role: discord.Role = None):
    """Удаляет роль из магазина (только для администраторов)."""
    try:
        if role is None:
            await ctx.send(f"{ctx.author.mention}, укажите роль для удаления из магазина.")
            return
        
        cursor.execute("DELETE FROM shop WHERE role_id = ? AND server_id = ?", (role.id, ctx.guild.id))
        if cursor.rowcount == 0:
            await ctx.send(f"Роль {role.mention} не найдена в магазине.")
            return
        connection.commit()
        await ctx.message.add_reaction('✅')
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для выполнения команды.")

@Bot.command(aliases=['buy', 'buy-role'])
async def buy(ctx, role: discord.Role = None):
    """Покупает роль из магазина."""
    try:
        if role is None:
            await ctx.send(f"{ctx.author.mention}, укажите роль для покупки.")
            return
        if role in ctx.author.roles:
            await ctx.send(f"{ctx.author.mention}, у вас уже есть эта роль.")
            return
        
        cost = cursor.execute("SELECT cost FROM shop WHERE role_id = ? AND server_id = ?", 
                             (role.id, ctx.guild.id)).fetchone()
        if cost is None:
            await ctx.send(f"{ctx.author.mention}, эта роль не продается в магазине.")
            return
        
        user_cash = cursor.execute("SELECT cash FROM users WHERE id = ?", (ctx.author.id,)).fetchone()
        if user_cash is None or user_cash[0] < cost[0]:
            await ctx.send(f"{ctx.author.mention}, у вас недостаточно средств для покупки роли.")
            return
        
        await ctx.author.add_roles(role)
        cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?", (cost[0], ctx.author.id))
        connection.commit()
        await ctx.message.add_reaction('✅')
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для выдачи роли.")
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")

@Bot.command(aliases=['rep', '+rep'])
async def rep(ctx, member: discord.Member = None):
    """Добавляет репутацию пользователю."""
    try:
        if member is None:
            await ctx.send(f"{ctx.author.mention}, укажите пользователя для добавления репутации.")
            return
        if member.id == ctx.author.id:
            await ctx.send(f"{ctx.author.mention}, вы не можете добавить репутацию себе.")
            return
        
        cursor.execute("UPDATE users SET rep = rep + 1 WHERE id = ?", (member.id,))
        connection.commit()
        await ctx.message.add_reaction('✅')
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")

@Bot.command(aliases=['leaderboard', 'lb'])
async def leaderboard(ctx):
    """Показывает топ-10 пользователей по балансу."""
    try:
        embed = discord.Embed(title="Топ 10 сервера")
        rows = cursor.execute(
            "SELECT name, cash FROM users WHERE server_id = ? ORDER BY cash DESC LIMIT 10",
            (ctx.guild.id,)
        ).fetchall()
        
        for i, row in enumerate(rows, 1):
            embed.add_field(
                name=f"#{i} | `{row[0]}`",
                value=f"Баланс: {row[1]} 💰",
                inline=False
            )
        if not rows:
            embed.description = "Лидерборд пуст."
        await ctx.send(embed=embed)
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")

@Bot.command(aliases=['shop', 'магазин'])
async def shop(ctx):
    """Показывает магазин ролей с пагинацией."""
    try:
        await ctx.channel.purge(limit=1)
        rows = cursor.execute(
            "SELECT role_id, cost FROM shop WHERE server_id = ?",
            (ctx.guild.id,)
        ).fetchall()
        
        if not rows:
            await ctx.send("Магазин ролей пуст.")
            return
        
        pages = []
        for i in range(0, len(rows), 5):  # Пагинация по 5 ролей на страницу
            embed = discord.Embed(title=f"Магазин ролей (стр. {i//5 + 1})")
            for j, row in enumerate(rows[i:i+5], i+1):
                role = ctx.guild.get_role(row[0])
                if role:
                    embed.add_field(
                        name=f"Роль #{j} | Стоимость: {row[1]} 💰",
                        value=role.mention,
                        inline=False
                    )
            if embed.fields:  # Добавлять только непустые страницы
                pages.append(embed)
        
        if not pages:
            await ctx.send("Магазин ролей пуст.")
            return
        
        message = await ctx.send(embed=pages[0])
        if len(pages) == 1:
            return
        
        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id

        i = 0
        while True:
            try:
                reaction, user = await Bot.wait_for('reaction_add', timeout=30.0, check=check)
                await message.remove_reaction(reaction, user)
                
                if str(reaction) == '⏮':
                    i = 0
                elif str(reaction) == '◀' and i > 0:
                    i -= 1
                elif str(reaction) == '▶' and i < len(pages) - 1:
                    i += 1
                elif str(reaction) == '⏭':
                    i = len(pages) - 1
                await message.edit(embed=pages[i])
            except asyncio.TimeoutError:
                break
        
        await message.clear_reactions()
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для управления сообщениями.")
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}")

@Bot.command(aliases=['h'])
async def help(ctx):
    embed = discord.Embed(title="Список команд", description="Доступные команды бота:")
    embed.add_field(name="!balance [@user]", value="Показать баланс пользователя", inline=False)
    embed.add_field(name="!award @user <amount>", value="Начислить валюту (админ)", inline=False)
    embed.add_field(name="!shop", value="Показать магазин ролей", inline=False)
    await ctx.send(embed=embed)

Bot.run(os.getenv("DISCORD_TOKEN"))