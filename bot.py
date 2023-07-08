import requests
import discord
from discord.ext import commands, pages
import datetime
import time
from pprint import pprint # used for debugging, probably won't be seen here
import re # i wanted to avoid regex sigh

# search functionality works using the Anilist GraphQL APIv2:
# https://anilist.gitbook.io/anilist-apiv2-docs/
# https://anilist.github.io/ApiV2-GraphQL-Docs/

with open("bot_keys.txt", "r") as f: # Opens the bot_keys.txt file and reads the keys.
    keys = [i.strip() for i in f.readlines()] # removes the newline characters from the keys
    # print(keys)

botID = keys[0] # discord ID of our bot, just for reference
botToken = keys[1] # discord bot token
holodexKey = keys[2] # API key for Holodex

intents = discord.Intents.default() # Sets the bot's intents to default.
intents.message_content = True # Allows the bot to read messages.

client = commands.Bot(command_prefix="$", intents=intents) # Sets the bot's prefix to "$" and intents to the intents variable.

Token = botToken 

id_query = ''' 
    query ($id: Int) { # Define which variables will be used in the query (id)
    Media (id: $id) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
        id
        title {
            romaji
            english
            native
        }
        type
        coverImage {
            extraLarge
        }
        status
        description (asHtml: false)
        synonyms
    }
    }
    '''

big_query = '''
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
                description (asHtml: false)
                type
                status
                coverImage {
                    extraLarge
                }
                synonyms
            }
        }
    }
    '''

rec_query = ''' 
        query ($id: Int, $page: Int, $perPage: Int) { # Define which variables will be used in the query (id)
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                    perPage
                }
                recommendations (mediaId:$id) {
                    id
                }
            }
        }
        '''

rec_media_query = ''' 
        query ($id: Int) { # Define which variables will be used in the query (id)
        Recommendation (id: $id) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
            mediaRecommendation {
                id
                title {
                    romaji
                    english
                    native
                }
                description (asHtml: false)
                type
                status
                coverImage {
                    extraLarge
                }
                synonyms
            }
        }
        }
        '''
 
def lookup(query, variables):
    '''anime search by Anilist ID using the Anilist GraphQL APIv2'''
    url = 'https://graphql.anilist.co'
    variables = variables
    response = requests.post(url, json={'query': query, 'variables': variables})
    # response is a json object, parse it for titles
    response = response.json()
    return response

def get_terms(message):
    '''gets the search terms and search count from the message'''
    if len(message) > 5 and message[0:4] == "num=": # if the message is structured in the form "num=XX + search terms"
        # get the num value as an int
        n = 4
        while message[n].isdigit():
            n += 1
        num = int(message[4:n]) # get the number of results to return
        # get the search terms
        search_terms = message[n+1:]
        return (num, search_terms)
    else:
        num = 10 # return 10 results by default
        search_terms = message
        return (num, search_terms)
    
def detailed_embed(media, discord_time):
    gen_url = "https://anilist.co/" + str(media["type"]) + "/" + str(media["id"])
    try:
        try:
            description = media["description"]
            # remove the html tags from the description
            description = re.sub('<[^<]+?>', '', description)
            # if an english title exists, use that, otherwise use the romaji title
        except:
            description = "No description available."
        if media["title"]["english"] == None:
            try:
                embed = discord.Embed(title = media["title"]["romaji"], description=description, url=gen_url, color=discord.Color.blue())
            except:
                embed = discord.Embed(title = media["title"]["native"], description=description, url=gen_url, color=discord.Color.blue())
        else:
            embed = discord.Embed(title = media["title"]["english"], description=description, url=gen_url, color=discord.Color.blue())
        try:
            embed.set_thumbnail(url=media["coverImage"]["extraLarge"])
        except:
            pass
        embed.add_field(name="Original Title", value=media["title"]["native"], inline=False)
        try:
            syns = media["synonyms"]
            # keep only syns that use the ascii chars
            for i in syns:
                if not i.isascii(): 
                    syns.remove(i)
            syns = ", ".join(syns)
            # only if there are synonyms, add the synonyms field
            if syns != "":
                embed.add_field(name="Alternate Titles", value=syns, inline=False)
        except:
            pass
        embed.add_field(name="Media Type", value=media["type"], inline=True)
        embed.add_field(name="Status", value=media["status"], inline=True)
        embed.add_field(name="Anilist ID", value=media["id"], inline=True)
        embed.add_field(name="Checked at", value=discord_time, inline=False)
        return embed
    except:
        embed = discord.Embed(title = "Sorry, an error has occurred while loading this page.", description="For troubleshooting, please note your exact search query and the page you are seeing this error on, and open an issue on the Github page for this bot, accessible by clicking the link in the title of this embed.", url="https://github.com/wattyven/discord-anime-bot", color=discord.Color.red())
        return embed
    
def yt_thumb(ytid):
    '''get the thumbnail for a youtube video'''
    url = "https://img.youtube.com/vi/" + ytid + "/maxresdefault.jpg"
    return url
    
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
    embed.add_field(name="$rec", value="Gets recommendations for an anime by title search using the Anilist GraphQL APIv2", inline=False)
    embed.add_field(name="$recid", value="Gets recommendations for an anime by Anilist ID using the Anilist GraphQL APIv2", inline=False)
    await ctx.send(embed=embed)

@client.command()
async def searchid(ctx, *, message):
    '''anime search by Anilist ID using the Anilist GraphQL APIv2'''
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
        response = lookup(id_query, variables)
        unix_time = int(time.time())
        discord_time = "<t:" + str(unix_time) + ":F>"
        try:
            media = response["data"]["Media"]
            embed = detailed_embed(media, discord_time)
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
   
    num, search_terms = get_terms(message)
    
    variables = {
        'search': search_terms,
        'page': 1,
        'perPage': num
    }

    response = lookup(big_query, variables)
    unix_time = int(time.time())
    discord_time = "<t:" + str(unix_time) + ":F>"
    embeds = []
    try:
        for i in response["data"]["Page"]["media"]:
            embed = detailed_embed(i, discord_time)
            embeds.append(embed)
        paginator = pages.Paginator(pages=embeds, timeout=600.0) # Creates a paginator object.
        await paginator.send(ctx) # Sends the paginator object to the user.
        
    except TypeError:
        embed = discord.Embed(title = "Error", description="Sorry, no results found.", color=discord.Color.red())
        await ctx.send(embed = embed)
        return
    
@client.command()
async def recid(ctx, *, message):
    '''recommendation engine, given an Anilist media ID, passed through the graphQL API
    usage: $search [num=XX] [media ID]'''
    
    num, search_id = get_terms(message)

    try:
        id = int(search_id.replace(" ", ""))
    except:
        embed = discord.Embed(title = "Error", description="Sorry, you need to enter a valid numerical ID.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    if type(id) == int:
        variables = {
            'id': id,
            'page': 1,
            'perPage': num
        }
        response = lookup(rec_query, variables)
        rec_list = [i["id"] for i in response["data"]["Page"]["recommendations"]]
        discord_time = "<t:" + str(int(time.time())) + ":F>"
        embeds = []
        try:
            for i in rec_list:
                variables = {
                    'id': i
                }
                response = lookup(rec_media_query, variables)
                rec_info = response["data"]["Recommendation"]["mediaRecommendation"]
                embed = detailed_embed(rec_info, discord_time)
                embeds.append(embed)
            paginator = pages.Paginator(pages=embeds, timeout=600.0) # Creates a paginator object.
            await paginator.send(ctx) # Sends the paginator object to the user.
            
        except TypeError:
            embed = discord.Embed(title = "Error", description="Sorry, no results found.", color=discord.Color.red())
            await ctx.send(embed = embed)
            return
            
        
@client.command()
async def rec(ctx, *, message):
    '''recommendation engine, given a search string, passed through the graphQL API
    usage: $search [num=XX] [search terms]'''
    num, search_terms = get_terms(message)
    variables = {
        'search': search_terms,
        'page': 1,
        'perPage': num
    }
    response = lookup(big_query, variables)
    # extract only the IDs from the response
    id_list = [i["id"] for i in response["data"]["Page"]["media"]]
    # get the recommendations for each ID
    rec_list = []
    for id in id_list:
        variables = {
            'id': id,
            'page': 1,
            'perPage': num
        }
        response = lookup(rec_query, variables)
        # extract only the IDs from the response
        rec_list += [i["id"] for i in response["data"]["Page"]["recommendations"]]
        
    # remove duplicates
    rec_list = list(set(rec_list))
    # get the media for each ID
    media_list = []
    for id in rec_list:
        variables = {
            'id': id
        }
        response = lookup(rec_media_query, variables)
        media_list.append(response["data"]["Recommendation"]["mediaRecommendation"])
    embeds = []
    discord_time = "<t:" + str(int(time.time())) + ":F>"
    try:
        for media in media_list:
            embed = detailed_embed(media, discord_time)
            embeds.append(embed)
        paginator = pages.Paginator(pages=embeds, timeout=600.0)
        await paginator.send(ctx) # Sends the paginator object to the user.
            
    except TypeError:
        embed = discord.Embed(title = "Error", description="Sorry, no results found.", color=discord.Color.red())
        await ctx.send(embed = embed)
        return
    
@client.command()
async def live(ctx):
    # Get live streams from Holodex API
    url = "https://holodex.net/api/v2/live"
    yt = "https://www.youtube.com/watch?v="
    headers = {
        "Accept": "application/json",
        "X-APIKEY": holodexKey
    }
    querystring = {"org":"Hololive"}
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    # discord_time = "<t:" + str(int(time.time())) + ":F>" 
    # not currently used

    # For each live stream, create an embed
    embeds = []
    for stream in data:
        if stream['status'] == "live" and stream['type'] == "stream" and stream['live_viewers'] > 0:
            embed = discord.Embed(title=stream['title'], url = yt + stream['id'], description='**' + stream['channel']['name'] + '**')
            embed.set_image(url=yt_thumb(stream['id']))
            timeavailable = datetime.datetime.strptime(stream["available_at"][:-5], "%Y-%m-%dT%H:%M:%S")
            timeavailable = timeavailable - datetime.timedelta(hours=7)
            timeavailable = "<t:" + str(int(time.mktime(timeavailable.timetuple()))) + ":F>"
            embed.add_field(name='Live Since', value=timeavailable)
            embed.add_field(name='Viewers', value=stream['live_viewers'], inline=True)
            # this next line is a bit of a hack, because footers can't have markdown
            # and because my AWS instance is set to UTC, we might as well just use that
            embed.set_footer(text="Checked at " + datetime.datetime.now().strftime("%I:%M %p") + " UTC")
            embeds.append(embed)
        elif stream['type'] == "stream" and stream['status'] == "upcoming":
            embed = discord.Embed(title=stream['title'], url = yt + stream['id'], description='**' + stream['channel']['name'] + '**')
            embed.set_image(url=yt_thumb(stream['id']))
            timeavailable = datetime.datetime.strptime(stream["start_scheduled"][:-5], "%Y-%m-%dT%H:%M:%S")
            timeavailable = timeavailable - datetime.timedelta(hours=7)
            timeavailable = "<t:" + str(int(time.mktime(timeavailable.timetuple()))) + ":F>"
            embed.add_field(name='Start Time', value=timeavailable)
            # same shit as above
            embed.set_footer(text="Checked at " + datetime.datetime.now().strftime("%I:%M %p") + " UTC")
            embeds.append(embed)

    # Create a Paginator instance and send it
    paginator = pages.Paginator(pages=embeds, timeout=600.0)
    await paginator.send(ctx)

client.run(Token)
