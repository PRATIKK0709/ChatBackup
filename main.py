import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta
import asyncio
import os

intents = discord.Intents.all()
intents.messages = True 

bot = commands.Bot(command_prefix='!', intents=intents)


# Function to update progress message
async def update_progress(progress_message, progress):
    await progress_message.edit(content=f"Progress: {progress}%")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == 1227039653769773077:  # Replace YOUR_CHANNEL_ID with the ID of the channel where you want to listen for messages
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith('image'):
                    try:
                        # Delete the original message
                        await message.delete()

                        # Send the image using the bot
                        await message.channel.send(file=await attachment.to_file())
                    except discord.errors.Forbidden:
                        await message.channel.send("I don't have permission to delete messages.")
                    except Exception as e:
                        await message.channel.send(f"An error occurred: {e}")
                    break  # Stop processing further attachments if an image is found

    await bot.process_commands(message)

@bot.command()
async def cc(ctx, channel_id):
    try:
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            await ctx.send("Invalid channel ID.")
            return
        
        messages = []
        async for message in channel.history(limit=None):
            message_data = f"[{message.created_at.strftime('%d %B %Y')}] {message.author}: {message.content}"
            
            # Append information about attachments, if any
            if message.attachments:
                for attachment in message.attachments:
                    message_data += f"\nAttachment: {attachment.url}"
            
            messages.append(message_data)
        
        with open(f"{channel.name}.txt", "w", encoding="utf-8") as file:
            file.write("\n\n".join(messages))
        
        await ctx.send(f"Messages from channel <#{channel.id}> have been copied to a human-readable file.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def lf(ctx):
    try:
        files = [file for file in os.listdir() if file.endswith(".txt")]
        if not files:
            await ctx.send("No text files found.")
            return

        file_list = "\n".join([f"{index + 1}. {file}" for index, file in enumerate(files)])
        await ctx.send(f"List of text files:\n{file_list}")

        await ctx.send("Please enter the number of the file you want to send content from.")
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit() and 1 <= int(message.content) <= len(files)
        
        msg = await bot.wait_for("message", check=check, timeout=30)
        selected_file = files[int(msg.content) - 1]

        with open(selected_file, "r", encoding="utf-8") as file:
            file_content = file.read()
        
        if len(file_content) <= 2000:
            await ctx.send(f"Content of `{selected_file}`:\n{file_content}")
            await ctx.send("Please mention the channel where you want to send the content.")
            
            def check_channel(message):
                return message.author == ctx.author and message.channel == ctx.channel and message.channel_mentions
            
            channel_msg = await bot.wait_for("message", check=check_channel, timeout=30)
            destination_channel = channel_msg.channel_mentions[0]
            
            await destination_channel.send(f"Content of `{selected_file}`:\n{file_content}", allowed_mentions=discord.AllowedMentions.none())
            await ctx.send("Content has been sent to the specified channel.")
        else:
            await ctx.send("The content of the file exceeds the character limit. Splitting and sending in packets.")
            chunks = [file_content[i:i+2000] for i in range(0, len(file_content), 2000)]
            
            await ctx.send(f"Content of `{selected_file}`:")
            for chunk in chunks:
                await ctx.send(chunk)
            
            await ctx.send("Please mention the channel where you want to send the content.")
            
            def check_channel(message):
                return message.author == ctx.author and message.channel == ctx.channel and message.channel_mentions
            
            channel_msg = await bot.wait_for("message", check=check_channel, timeout=30)
            destination_channel = channel_msg.channel_mentions[0]
            
            await destination_channel.send(f"Content of `{selected_file}`:")
            for chunk in chunks:
                await destination_channel.send(chunk, allowed_mentions=discord.AllowedMentions.none())
            
            await ctx.send("Content has been sent to the specified channel.")
    except asyncio.TimeoutError:
        await ctx.send("Timed out. Please try again.")

bot.run("TOKEN")
