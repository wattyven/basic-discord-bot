import requests
import discord
from discord.ext import commands, pages
from datetime import datetime

# TO-DO: (probably at some point in the distant future when i get bored again or if i remember to come back to this)
# help command + documentation for commands
# command for getting most popular anime, as well as most popular anime by genre etc
# improving search for multi-word / multi-term searches and better matching
# switching to a better API (not super important as I'm the only one using this bot rn)
# maybe user tracking for anime they've watched, anime they're currently watching, etc,
# so eventually, users can get anime recommendations based on activity
# also maybe social features like sharing anime with friends, etc


intents = discord.Intents.default() # Sets the bot's intents to default.
intents.message_content = True # Allows the bot to read messages.

client = commands.Bot(command_prefix="$", intents=intents) # Sets the bot's prefix to "$" and intents to the intents variable.

# bot = "###################"  # bot id, for personal reference

Token = '---------------------------------------' # Replace with Discord Bot Token.
       
@client.event
async def on_ready():
    print("Bot has started running") # Prints "Bot has started running" to the console when the bot is ready.
    await client.change_presence(activity=discord.Game(name="prefix: $")) # Sets the bot's status to "prefix: $", 
    # because there's no help command atm and people are bound to ask what the prefix is.

@client.command()
async def ping(ctx):
    '''ping function to check if the bot is online'''
    await ctx.send("Pong!")

@client.command()
async def search(ctx, search_term, page="1", size="50", genres="", sortBy="ranking", sortOrder="desc", types=""):
    '''search function to search for anime using the API'''
    url = "https://anime-db.p.rapidapi.com/anime" # API URL
    # this bot relies on Brian Rofiq's Anime DB API on RapidAPI, 
    # which can be found at https://rapidapi.com/brian.rofiq/api/anime-db/

    headers = {
        "X-RapidAPI-Key": "------------------------------------------------", # API key
        "X-RapidAPI-Host": "anime-db.p.rapidapi.com"
    }

    querystring = {"page":page, "size":size, "search":search_term, "genres":genres, "sortBy":sortBy, "sortOrder":sortOrder, "types":types} # Query parameters
    # note: it looks like the sortBy and sortOrder parameters are not working as intended, 
    # so I guess we'll have to account for that in the code.

    # did that below using a lambda function because i'm fucking lazy
     
    response = requests.get(url, headers=headers, params=querystring) # Sends a GET request to the API.

    now = datetime.now() # Gets the current time. 

    current_time = now.strftime("%H:%M:%S") # Formats the time to HH:MM:SS

    embeds = []
        
    for i in response.json()["data"]: # Loops through the data and adds the title, ranking, status and synopsis to the embed.
        embed = discord.Embed(title = i["title"], # Embed title
                          description="Synopsis: " + i["synopsis"], color=discord.Color.blue()) # search time as description
        alt_names_str = str("\n".join(i["alternativeTitles"])) # Converts the list of alternative titles to a string.
        embed.add_field(name="Alternative Titles", value=alt_names_str, inline=False) # Adds the alternative titles to the embed.
        embed.add_field(name="Ranking", value=i["ranking"], inline=True)
        embed.add_field(name="Status", value=i["status"], inline=True)
        embed.add_field(name="Checked at", value=current_time, inline=True)
        embeds.append(embed) # Adds the embed to the embeds list.

    # sort our embeds by ranking, numerically, so that the highest ranking anime is first
    embeds.sort(key=lambda x: int(x.fields[1].value))

    paginator = pages.Paginator(pages=embeds) # Creates a paginator object. https://docs.pycord.dev/en/stable/ext/pages/index.html#paginator
    await paginator.send(ctx) # Sends the paginator object to the user.

client.run(Token) # Runs the bot with the token.