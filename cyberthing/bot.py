
import discord
from discord import app_commands
from discord.ext import tasks
import server
from .env import TOKEN
from asyncio import run as async_run
from json import loads

class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        self.message_queue:list[str] = []
        self.running=False
        self.TOKEN = TOKEN
        self.CYBERGUILD:discord.Guild = discord.Object(1066424595617423420) # type: ignore
        self.BOT_CHANNEL=1068380985424621598
        self.httpServer = server.create_server(self)
        super().__init__(intents=discord.Intents.all(),*args, **kwargs)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        @tasks.loop(seconds=1)
        async def send_messages():
            print(client.message_queue)
            if client.message_queue:
                await client.get_channel(self.BOT_CHANNEL).send(client.message_queue.pop(0))

        send_messages.start()
        if not self.running:
            print("serving...")
            self.running=True
            self.httpServer.serve_forever()

    async def on_connect(self):
        print("Connected")
        await self.tree.sync(guild=self.CYBERGUILD)
        #self.httpServer.serve_forever()
        print("didnt serve forever")
    
    def run(self, token: str=None, *args, **kwargs) -> None:
        token = self.TOKEN if token is None else token
        return super().run(token, *args, **kwargs)


# TODO: fix blocking and make it async
# https://stackoverflow.com/questions/65881761/discord-gateway-warning-shard-id-none-heartbeat-blocked-for-more-than-10-second

client = Client()
client.tree = app_commands.CommandTree(client)

@client.tree.command(
    name="ping",
    description="Pong!",
    guilds=[client.CYBERGUILD]
)
async def _ping(ctx:discord.Interaction):
    await ctx.response.send_message("Pong!")

client.run()
