import requests
import discord
from discord.ext import commands, pages
from datetime import datetime
import gpt4free
from gpt4free import Provider
import re # i wanted to avoid regex sigh

# search functionality works using the Anilist GraphQL APIv2:
# https://anilist.gitbook.io/anilist-apiv2-docs/
# https://anilist.github.io/ApiV2-GraphQL-Docs/


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
    # get the latency of the bot
    latency = client.latency
    await ctx.send(f"Pong! Latency: {round(latency * 1000)}ms")

@client.command()
async def readme(ctx):
    '''quick readme with commands. slightly neater than the default help command'''
    embed = discord.Embed(title="Commands", description="Here are the commands for this bot", color=discord.Color.green())
    embed.add_field(name="$readme", value="Shows this message. Kinda redundant, huh.", inline=False)
    embed.add_field(name="$ping", value="Checks if the bot is online", inline=False)
    embed.add_field(name="$search", value="Searches for anime by title using the Anilist GraphQL APIv2", inline=False)
    embed.add_field(name="$searchid", value="Searches for anime by Anilist ID using the Anilist GraphQL APIv2", inline=False)
    await ctx.send(embed=embed)

@client.command()
async def searchid(ctx, *, message):
    '''anime search by Anilist ID using the Anilist GraphQL APIv2'''
    now = datetime.now() # Gets the current time. 

    current_time = now.strftime("%H:%M:%S") # Formats the time to HH:MM:SS
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
            embed.add_field(name="Checked at", value=current_time, inline=True)
            await ctx.send(embed = embed)
        except TypeError:
            embed = discord.Embed(title = "Error", description="Sorry, that ID doesn't exist.", color=discord.Color.red())
            await ctx.send(embed = embed)
            return

@client.command()
async def search(ctx, *, message):
    '''anime search by title using the Anilist GraphQL APIv2.
    usage: $search [num=XX] [search terms]
    num=XX is optional, where XX is the number of results to return. Default is 10.'''
    now = datetime.now() # Gets the current time. 

    current_time = now.strftime("%H:%M:%S") # Formats the time to HH:MM:SS
    # define query as a multi-line string. You can also use triple quotes.
    query = '''
    query ($id: Int, $page: Int, $perPage: Int, $search: String) {
        Page (page: $page, perPage: $perPage) {
            pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            media (id: $id, search: $search) {
                id
                title {
                    native
                    english
                    romaji
                }
                description
            }
        }
    }
    '''

    url = 'https://graphql.anilist.co'

    if len(message) > 5 and message[0:4] == "num=": # if the message is structured in the form "num=XX + search terms"
        # get the num value as an int
        n = 4
        while message[n].isdigit():
            n += 1
        num = int(message[4:n]) # get the number of results to return
        # get the search terms
        search_terms = message[n+1:]
    else:
        num = 10 # return 10 results by default
        search_terms = message
    
    variables = {
        'search': search_terms,
        'page': 1,
        'perPage': num
    }

    response = requests.post(url, json={'query': query, 'variables': variables})
    response = response.json()

    embeds = []
    try:
        for i in response["data"]["Page"]["media"]:
            description = i["description"]
            # remove the html tags from the description
            description = re.sub('<[^<]+?>', '', description)
            # if an english title exists, use that, otherwise use the romaji title
            if i["title"]["english"] == None:
                embed = discord.Embed(title = i["title"]["romaji"], color=discord.Color.blue())
            else:
                embed = discord.Embed(title = i["title"]["english"], color=discord.Color.blue())
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Original Title", value=i["title"]["native"], inline=False)
            embed.add_field(name="Anilist ID", value=i["id"], inline=True)
            embed.add_field(name="Checked at", value=current_time, inline=True)
            embeds.append(embed)
            paginator = pages.Paginator(pages=embeds) # Creates a paginator object.
        await paginator.send(ctx) # Sends the paginator object to the user.
        
    except TypeError:
        embed = discord.Embed(title = "Error", description="Sorry, no results found.", color=discord.Color.red())
        await ctx.send(embed = embed)
        return
    
@client.command()
async def chat(ctx, *, message):
    '''GPT-4 powered chat, powered by You through GPT4Free'''
    # message = " ".join(text) # don't need this atm but I'll keep it here just in case
    response = gpt4free.Completion.create(Provider.You, prompt=message)
    # remove "As an AI language model, " from the beginning of the response
    response = response.replace("As an AI language model, ", "")
    await ctx.send(response)
    
client.run(Token)
