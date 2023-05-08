import requests
import discord
from discord.ext import commands, pages
from datetime import datetime
import gpt4free
from gpt4free import Provider

with open("bot_keys.txt", "r") as f: # Opens the bot_keys.txt file and reads the keys.
    keys = [i.strip() for i in f.readlines()] # removes the newline characters from the keys
    # print(keys)

botID = keys[0] # discord ID of our bot, just for reference
botToken = keys[1] # discord bot token
animeDBKey = keys[2] # API key for the Anime DB API

intents = discord.Intents.default() # Sets the bot's intents to default.
intents.message_content = True # Allows the bot to read messages.

client = commands.Bot(command_prefix="$", intents=intents) # Sets the bot's prefix to "$" and intents to the intents variable.

Token = botToken 
       
@client.event
async def on_ready():
    print("Bot has started running") # Prints "Bot has started running" to the console when the bot is ready.
    await client.change_presence(activity=discord.Game(name="prefix: $")) # Sets the bot's status to "prefix: $"

@client.command()
async def ping(ctx):
    '''checks if the bot is online'''
    await ctx.send("Pong!")

@client.command()
async def readme(ctx):
    '''quick readme with commands. slightly neater than the default help command'''
    embed = discord.Embed(title="Commands", description="Here are the commands for this bot", color=discord.Color.blue())
    embed.add_field(name="$readme", value="Shows this message. Kinda redundant, huh.", inline=False)
    embed.add_field(name="$ping", value="Checks if the bot is online", inline=False)
    embed.add_field(name="$search", value="Searches for anime using the Anime DB API", inline=False)
    await ctx.send(embed=embed)

@client.command()
async def search(ctx, *terms, page="1", size="50", genres="", sortBy="ranking", sortOrder="desc", types=""):
    '''anime lookup using the Anime DB API'''
    url = "https://anime-db.p.rapidapi.com/anime" # API URL
    # this bot relies on Brian Rofiq's Anime DB API on RapidAPI, 
    # which can be found at https://rapidapi.com/brian.rofiq/api/anime-db/

    search_term = " ".join(terms) # Converts the search terms to a string.
    # if the search term is comprised of multiple words, add quotation marks around it
    if len(terms) > 1:
        search_term = "\"" + search_term + "\""

    headers = {
        "X-RapidAPI-Key": animeDBKey,
        "X-RapidAPI-Host": "anime-db.p.rapidapi.com"
    }

    querystring = {"page":page, "size":size, "search":search_term, "genres":genres, "sortBy":sortBy, "sortOrder":sortOrder, "types":types} # Query parameters
    # note: it looks like the sortBy and sortOrder parameters are not working as intended, 
    # so I guess we'll have to account for that in the code.
     
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

    paginator = pages.Paginator(pages=embeds) # Creates a paginator object.
    await paginator.send(ctx) # Sends the paginator object to the user.

@client.command()
async def chat(ctx, *, message):
    '''GPT-4 powered chat, powered by You through GPT4Free'''
    # message = " ".join(text) # don't need this atm but I'll keep it here just in case
    response = gpt4free.Completion.create(Provider.You, prompt=message)
    await ctx.send(response)

@client.command()
async def searchid(ctx, *, message):
    '''anime search by Anilist ID using the Anilist GraphQL APIv2'''
    # define query as a multi-line string. You can also use triple quotes.
    query = ''' 
    query ($id: Int) { # Define which variables will be used in the query (id)
    Media (id: $id, type: ANIME) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
        id
        title {
        romaji
        english
        native
        }
    }
    }
    '''
    url = 'https://graphql.anilist.co'
    try:
        id = int(message.replace(" ", ""))
    except ValueError:
        embed = discord.Embed(title = "Error", description="Sorry, you need to enter a valid numerical ID.", color=discord.Color.red())
        await ctx.send(embed = embed)
        return
    if type(id) == int:
        variables = {
            'id': id
        }
        response = requests.post(url, json={'query': query, 'variables': variables})
        # response is a json object, parse it for titles
        response = response.json()
        try:
            title_dict = response["data"]["Media"]["title"]
            embed = discord.Embed(title = title_dict["english"], color=discord.Color.blue())
            embed.add_field(name="Original Title", value=title_dict["native"], inline=False)
            embed.add_field(name="Romaji Title", value=title_dict["romaji"], inline=True)
            embed.add_field(name="Query ID", value=id, inline=True)
            await ctx.send(embed = embed)
        except TypeError:
            embed = discord.Embed(title = "Error", description="Sorry, that ID doesn't exist.", color=discord.Color.red())
            await ctx.send(embed = embed)
            return

@client.command()
async def search2(ctx, *, message):
    '''anime search by title using the Anilist GraphQL APIv2'''
    # define query as a multi-line string. You can also use triple quotes.
    query = ''' 
    query ($id: Int) { # Define which variables will be used in the query (id)
    Media (id: $id, type: ANIME) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
        id
        title {
        romaji
        english
        native
        }
    }
    }
    '''

    url = 'https://graphql.anilist.co'
    try:
        val = int(message.replace(" ", ""))
    except ValueError:
        val = message

    if type(val) == int:
        variables = {
            'id': val
        }
        response = requests.post(url, json={'query': query, 'variables': variables})
        # response is a json object, parse it for titles
        response = response.json()
        title_dict = response["data"]["Media"]["title"]
        await ctx.send("Romaji: " + title_dict["romaji"] + "\nEnglish: " + title_dict["english"] + "\nNative: " + title_dict["native"])

    elif type(val) == str:
        variables = {
            'search': val
        }
        response = requests.post(url, json={'query': query, 'variables': variables})
    # input_type = type(val)
    # await ctx.send(input_type)

client.run(Token)
