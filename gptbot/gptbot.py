
import discord
from discord.ext import commands
import openai
from json import dumps
from traceback import print_exc
import time
from threading import Thread
from server import run

TOKEN = "MTA4NjUwMTE0MTU5NDAwMTQyOQ.G28Xmj.wFmque89bngTFMeYtJUgHdzkMZbipSPzfXoYAM"
openai.api_key="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"

class Conversations:
    def __init__(self):
        self.conversations:dict[int,list[dict[str,str]]] = {}
        self.system_messages:dict[int,str] = {} # added to the conversation history before next_prompt is called

    def __iter__(self):
        return self.conversations.__iter__()
    
    def __getitem__(self, key):
        return self.conversations[key]
    
    def __setitem__(self, key, value):
        self.conversations[key] = value
    
    def get_history(self, member:discord.Member, stringify:bool=False):
        try:
            history = self.conversations[member.id].append({
                "role": "system",
                "content": self.system_messages[member.id]
            })
            if stringify:
                return dumps(history)
            return history
        except KeyError:
            return []

    def add_history(self, member:discord.Member, role:str, content:str):
        try:
            self.conversations[member.id].append({"role": role, "content": content})
        except KeyError:
            self.conversations[member.id] = [{"role": role, "content": content}]
    
    def next_prompt(self, member:discord.Member, new_prompt:str):
        self.add_history(member, "user", new_prompt)
        response = None
        while response is None:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=self.get_history(member)
                )
            except openai.error.RateLimitError:
                time.sleep(5)

        content:str = response.choices[0]["message"]["content"]
        self.add_history(member, "assistant", content)
        return content

    def one(self,prompt:str):
        response = None
        while response is None:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
            except openai.error.RateLimitError:
                time.sleep(5)

        content:str = response.choices[0]["message"]["content"]
        return content
    
    def clear(self, member:discord.Member):
        self.conversations[member.id] = []
        

conversations = Conversations()

intents = discord.Intents.default()
intents.members = True
intents.messages = True

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
            content = content[:2000]
        await ctx.edit(content=content)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="one", description="Will not create a persistent conversation. This is useful for instructions or quick questions.")
async def one(ctx: discord.commands.context.ApplicationContext, message: str):
    try:
        # send a temporary message to the user
        await ctx.respond("Thinking...", ephemeral=True)
        # now let the model think
        content = conversations.one(message)
        # ensure <2000 characters
        if len(content) > 2000:
            content = content[:2000]
        await ctx.edit(content=content)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="reset", description="Reset command")
async def reset(ctx: discord.commands.context.ApplicationContext):
    try:
        conversations.clear(ctx.author)
        await ctx.respond("Conversation history cleared", ephemeral=True)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="history", description="Sends a ")
async def history(ctx: discord.commands.context.ApplicationContext):
    try:
        history = conversations.get_history(ctx.author, stringify=True)
        stringify = f"```json\n{history}\n```"
        if len(stringify) > 2000:
            stringify = stringify[:2000]
        await ctx.respond(stringify, ephemeral=True)
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

system = bot.create_group(name="system", description="System commands")

@system.command()
async def set(ctx: discord.commands.context.ApplicationContext, content:str):
    try:
        conversations.add_history(ctx.author, "system", content)
        await ctx.respond(f"Set system message to `{content}`", ephemeral=True)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@system.command()
async def clear(ctx: discord.commands.context.ApplicationContext):
    try:
        conversations.clear(ctx.author)
        await ctx.respond("Cleared system messages", ephemeral=True)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

if __name__ == "__main__":
    http_server = Thread(target=run, args=(conversations,))
    try:
        http_server.start()
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("Exiting...")
        http_server.join()
        exit(0)
