
import discord
from discord.ext import commands
import openai
from json import dumps
from traceback import print_exc

TOKEN = "MTA4NjUwMTE0MTU5NDAwMTQyOQ.G28Xmj.wFmque89bngTFMeYtJUgHdzkMZbipSPzfXoYAM"
openai.api_key="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"

class Conversations:
    def __init__(self):
        self.conversations:dict[int,list[dict[str,str]]] = {}
        # self.conversations:
        # key: member.id
        # value: list of dicts
        #  key: role
        #  value: content
        
        
    def __iter__(self):
        return self.conversations.__iter__()
    
    def __getitem__(self, key):
        return self.conversations[key]
    
    def __setitem__(self, key, value):
        self.conversations[key] = value
    
    def get_history(self, member:discord.Member, stringify:bool=False):
        try:
            history = self.conversations[member.id]
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.get_history(member)
        )
        content = response.choices[0]["message"]["content"]
        self.add_history(member, "assistant", content)
        return content
    
    def clear(self, member:discord.Member):
        self.conversations[member.id] = []
        

conversations = Conversations()

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.slash_command(name="prompt", description="Prompt command")
async def prompt(ctx: commands.Context, message: str):
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

@bot.slash_command(name="reset", description="Reset command")
async def reset(ctx: commands.Context):
    try:
        conversations.clear(ctx.author)
        await ctx.respond("Conversation history cleared", ephemeral=True)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.slash_command(name="history", description="Sends a ")
async def history(ctx: commands.Context):
    try:
        history = conversations.get_history(ctx.author, stringify=True)
        stringify = f"```json\n{history}\n```"
        if len(stringify) > 2000:
            stringify = stringify[:2000]
        await ctx.respond(stringify, ephemeral=True)
    except Exception as e:
        print_exc()
        await ctx.respond("there was an error. let MR_H3ADSH0T#0001 know", ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.run(TOKEN)

