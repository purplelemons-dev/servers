
import discord
from server import run
from json import dumps
from threading import Thread
from traceback import print_exc
from discord.ext import commands
from conversations import Conversations, shared_resource
from time import sleep, perf_counter
from requests import get as requests_get

TOKEN = "MTA4NjUwMTE0MTU5NDAwMTQyOQ.G28Xmj.wFmque89bngTFMeYtJUgHdzkMZbipSPzfXoYAM"

conversations = Conversations()
conversations.tryload("conversations.json")

intents = discord.Intents.default()
intents.members = True
intents.messages = True

class Bot(commands.Bot):

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        while self.res.running:
            # a bit janky, but the bot will essentially wait until the resource is stopped
            # basically a polling rate of 1 second
            sleep(1)
        print("Stopping bot...")
        await self.close()

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.slash_command(name="prompt", description="Prompt command")
async def prompt(ctx: discord.commands.context.ApplicationContext, message: str):
    try:
        # send a temporary message to the user
        await ctx.respond("Thinking...", ephemeral=True)
        # now let the model think
        content = conversations.next_prompt(ctx.author, message)
        # ensure <2000 characters
        if len(content) > 2000:
            with open("big.txt", "w") as f:
                f.write(content)
            await ctx.respond("My response seems to be too large for discord, here's a file that contains it.", file=discord.File("big.txt", filename="big.txt"), ephemeral=True)
            return            
        await ctx.edit(content=content)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="big", description="functions just like /prompt (adds to your history), but allows for large amounts of text")
async def big(ctx: discord.commands.context.ApplicationContext, file: discord.Attachment):
    # read the file
    text = await file.read()
    text = text.decode("utf-8")
    try:
        # send a temporary message to the user
        await ctx.respond("Thinking...", ephemeral=True)
        # now let the model think
        content = conversations.next_prompt(ctx.author, text)
        # ensure <2000 characters
        if len(content) > 2000:
            # if it's too long, send it as a file
            with open("big.txt", "w") as f:
                f.write(content)
            await ctx.respond("My response seems to be too large for discord, here's a file that contains it.", file=discord.File("big.txt", filename="big.txt"), ephemeral=True)
            return
        await ctx.edit(content=content)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="one", description="Will not create a persistent conversation. This is useful for instructions or quick questions.")
async def one(ctx: discord.commands.context.ApplicationContext, message: str, system:str=None):
    try:
        # send a temporary message to the user
        await ctx.respond("Thinking...", ephemeral=True)
        # now let the model think
        content = conversations.one(message, system)
        # ensure <2000 characters
        if len(content) > 2000:
            with open("big.txt", "w") as f:
                f.write(content)
            await ctx.respond("My response seems to be too large for discord, here's a file that contains it.", file=discord.File("big.txt", filename="big.txt"), ephemeral=True)
            return
        await ctx.edit(content=content)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="reset", description="Reset command")
async def reset(ctx: discord.commands.context.ApplicationContext):
    try:
        conversations.clear(ctx.author)
        await ctx.respond("Conversation history cleared", ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="history", description="Sends a copy of your conversation history in a code block.")
async def history(ctx: discord.commands.context.ApplicationContext):
    try:
        history = conversations.get_history(ctx.author, stringify=True)
        history = dumps(history).replace('```','``‎`')
        stringify = f"```json\n{history}\n```"
        if len(stringify) > 2000:
            with open("big.txt", "w") as f:
                f.write(stringify)
            await ctx.respond("Your conversation history seems to be too large for discord, here's a file that contains it.", file=discord.File("big.txt", filename="big.txt"), ephemeral=True)
            return
        await ctx.respond(stringify, ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="subscribe", description="Subscribe to the server's AI newsfeed. You will be pinged in #news")
async def subscribe(ctx: discord.commands.context.ApplicationContext):
    try:
        news_role = discord.utils.get(ctx.guild.roles, name="news")
        if news_role not in ctx.author.roles:
            await ctx.author.add_roles(news_role)
            await ctx.respond("Subscribed to the AI newsfeed", ephemeral=True)
        else:
            await ctx.respond("You're already subscribed to the AI newsfeed use /unsubscribe to no longer be pinged.", ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="unsubscribe", description="Unsubscribe from the server's AI newsfeed")
async def unsubscribe(ctx: discord.commands.context.ApplicationContext):
    try:
        news_role = discord.utils.get(ctx.guild.roles, name="news")
        if news_role in ctx.author.roles:
            await ctx.author.remove_roles(news_role)
            await ctx.respond("Unsubscribed from the AI newsfeed", ephemeral=True)
        else:
            await ctx.respond("You're not subscribed to the AI newsfeed use /subscribe to do so.", ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

system = bot.create_group(name="system", description="System commands")

@system.command()
async def set(ctx: discord.commands.context.ApplicationContext, content:str):
    try:
        conversations.system_messages[ctx.author.id] = content
        await ctx.respond(f"Set system message to `{content}`", ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@system.command()
async def clear(ctx: discord.commands.context.ApplicationContext):
    try:
        conversations.clear(ctx.author)
        await ctx.respond("Cleared system messages", ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@system.command()
async def query(ctx: discord.commands.context.ApplicationContext):
    try:
        content = conversations.system_messages.get(ctx.author.id, "None")
        await ctx.respond(f"System message is `{content}`", ephemeral=True)
    except Exception:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

if __name__ == "__main__":
    res = shared_resource(conversations)

    http_server = Thread(target=run, args=(res,))
    bot_thread = Thread(target=bot.run, args=(TOKEN,))
    try:
        bot_thread.start()
        http_server.start()
        while True:
            user_input = input(">>> ")
            if user_input == "exit":
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("Exiting...")
        res.stop()
        # dont make fun of me for this. its the only way.
        #requests_get("http://127.0.0.1:10002/")
        bot_thread.join()
        http_server.join()
        conversations.save()
        exit(0)
