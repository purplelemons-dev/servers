
import discord
from discord import app_commands
from server import server

TOKEN = "MTA2ODM2OTkxMDMyNzE0ODY0NA.GsYvcu.PMEgafS0BTMIxp5tyQZRPFauBRzKy_ZSFFf7D8"
CYBERGUILD:discord.Guild = discord.Object(1066424595617423420) # type: ignore

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_connect():
    await tree.sync(guild=CYBERGUILD)
    server.serve_forever()

@tree.command(
    name="ping",
    description="Pong!",
    guilds=[CYBERGUILD]
)
async def _ping(ctx:discord.Interaction):
    await ctx.response.send_message("Pong!")

client.run(TOKEN)
