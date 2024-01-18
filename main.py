import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks

TOKEN = 'BOT TOKEN HERE'
TARGET_CHANNEL_ID = 'DISCORD CHANNEL ID HERE'


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents) # The prefix is not used, its just a requirement to have it.

# Event to run when the bot is ready
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name}')

tracked_urls = {}

def get_amazon_product_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extracting product information
    title_element = soup.find('span', {'id': 'productTitle'})
    title = title_element.get_text().strip() if title_element else "Title not found"

    price_element = soup.find('span', {'class': 'a-offscreen'})
    price = price_element.get_text().strip() if price_element else "Price not found"

    # Extracting discount information
    discount_element = soup.find('span', {'class': 'savingsPercentage'})
    discount = discount_element.get_text().strip() if discount_element else "No discount"

    return title, price, discount

@tasks.loop(seconds=60)
async def check_discount():
    for url, data in tracked_urls.items():
        channel_id, user_id = data
        title, price, discount = get_amazon_product_info(url)

        print(f"Title: {title}")
        print(f"Price: {price}")
        print(f"Discount: {discount}\n")

        if "No discount" not in discount:
            channel = bot.get_channel(int(channel_id))
            user = await bot.fetch_user(int(user_id))
            del tracked_urls[url]
            await channel.send(f"__**New Discount Alert!**__\n\n**Title:** {title}\n**Price: {price}**\n**Discount: {discount}**\n**Url:** <{url}>\n{user.mention}")
        else: pass

@bot.tree.command(name='start', description='Start tracking a URL')
async def start(interaction, url: str):
    print("Start Command Called")
    tracked_urls[url] = (TARGET_CHANNEL_ID, interaction.user.id)
    await interaction.response.send_message(f"Started tracking <{url}>")

    if not check_discount.is_running():
        check_discount.start()
        await interaction.response.send_message('Started tracking discounts.')

@bot.tree.command(name='stop', description='Stop tracking a URL')
async def stop(interaction, url: str):
    print("Stop Command Called.")
    if url in tracked_urls:
        del tracked_urls[url]
        await interaction.response.send_message(f"Stopped tracking <{url}>")

    if not tracked_urls and check_discount.is_running():
        check_discount.stop()
        await interaction.response.send_message('Stopped tracking discounts.')


bot.run(TOKEN)
