import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "JUA Müzik Aktif!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

kuyruk = {}

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="!yardım"))
    print(f'✅ JUA Müzik hazır: {bot.user}')

@bot.command()
async def cal(ctx, *, sarki: str):
    if not ctx.author.voice:
        await ctx.send("Bir ses kanalında olmalısın!")
        return
    
    kanal = ctx.author.voice.channel
    if ctx.voice_client is None:
        await kanal.connect()
    elif ctx.voice_client.channel != kanal:
        await ctx.voice_client.move_to(kanal)
    
    await ctx.send(f"🔍 {sarki} aranıyor...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{sarki}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            sarki_adi = info.get('title', sarki)
        
        if ctx.guild.id not in kuyruk:
            kuyruk[ctx.guild.id] = []
        kuyruk[ctx.guild.id].append((url, sarki_adi))
        
        if not ctx.voice_client.is_playing():
            await oynat(ctx)
        else:
            await ctx.send(f"✅ {sarki_adi} kuyruğa eklendi.")
            
    except Exception as e:
        await ctx.send(f"❌ Hata: {str(e)[:100]}")

async def oynat(ctx):
    if ctx.guild.id not in kuyruk or not kuyruk[ctx.guild.id]:
        return
    
    url, sarki_adi = kuyruk[ctx.guild.id].pop(0)
    
    try:
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(oynat(ctx), bot.loop)
        )
        await ctx.send(f"🎵 Şimdi çalıyor: {sarki_adi}")
    except Exception as e:
        await ctx.send(f"❌ Hata: {e}")

@bot.command()
async def dur(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Durduruldu.")

@bot.command()
async def devam(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Devam ediyor.")

@bot.command()
async def gec(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Geçiliyor...")
        await oynat(ctx)

@bot.command()
async def kuyruk(ctx):
    if ctx.guild.id in kuyruk and kuyruk[ctx.guild.id]:
        liste = "\n".join([f"{i+1}. {s[1]}" for i, s in enumerate(kuyruk[ctx.guild.id])])
        await ctx.send(f"📋 **Kuyruk:**\n{liste}")
    else:
        await ctx.send("📋 Kuyruk boş.")

@bot.command()
async def ses(ctx, seviye: int):
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = seviye / 100
        await ctx.send(f"🔊 Ses: {seviye}%")

@bot.command()
async def ayril(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        if ctx.guild.id in kuyruk:
            kuyruk[ctx.guild.id] = []
        await ctx.send("👋 Ayrıldı.")

@bot.command()
async def yardım(ctx):
    await ctx.send(
        "**🎵 JUA Müzik Komutları**\n\n"
        "!cal <şarkı> - Müzik çalar\n"
        "!dur - Durdurur\n"
        "!devam - Devam ettirir\n"
        "!gec - Sonraki şarkıya geçer\n"
        "!kuyruk - Kuyruğu gösterir\n"
        "!ses <0-100> - Ses ayarı\n"
        "!ayril - Bot ayrılır"
    )

if __name__ == "__main__":
    Thread(target=run_web).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ Token ayarlanmamış")