import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
import datetime
import openai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
TENOR_API_KEY = "AIzaSyCzlPJ3FWYhQl65uuvwESfU3n0cp63Ss4k"

intents = discord.Intents.default()
intents.message_content = True

# Nueva clase para usar slash commands
class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Comandos slash sincronizados.")

bot = MyBot(command_prefix="!", intents=intents)

active_chats = set()
last_roll_times = {}
chat_memory = {}

# Gangs de pibble y sus colores
pibble_gangs = {
    "Pibble": discord.Colour.from_rgb(139, 69, 19),
    "Gmail": discord.Colour.from_rgb(255, 255, 255),
    "Bagel": discord.Colour.from_rgb(255, 255, 102),
    "Washington": discord.Colour.from_rgb(128, 128, 128),
    "Geeble": discord.Colour.from_rgb(0, 128, 0),
    "Waffle": discord.Colour.from_rgb(240, 194, 104)
}

@bot.event
async def on_ready():
    print(f'🤖 Bot conectado como {bot.user}')

@bot.command(name="pibble")
async def pibble(ctx):
    search_term = "pibble"
    url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key={TENOR_API_KEY}&limit=10"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get("results")
                if results:
                    gif_url = random.choice(results)["media_formats"]["gif"]["url"]
                    await ctx.send(gif_url)
                else:
                    await ctx.send("No encontré ningún gif de pibble 😢")
            else:
                await ctx.send("Error al buscar en Tenor")

@bot.command(name="cat")
async def cat(ctx):
    search_term = "silly cats"
    url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key={TENOR_API_KEY}&limit=10"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get("results")
                if results:
                    gif_url = random.choice(results)["media_formats"]["gif"]["url"]
                    await ctx.send(gif_url)
                else:
                    await ctx.send("No encontré ningún gif de gatos tontos 😿")
            else:
                await ctx.send("Error al buscar en Tenor")

@bot.command(name="roll")
async def roll(ctx):
    user_id = ctx.author.id
    now = datetime.datetime.utcnow()
    if user_id in last_roll_times:
        last_time = last_roll_times[user_id]
        if (now - last_time).total_seconds() < 86400:
            time_left = 86400 - (now - last_time).total_seconds()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            await ctx.send(f"Ya hiciste roll. Intenta de nuevo en {hours}h {minutes}m.")
            return

    gang_name = random.choice(list(pibble_gangs.keys()))
    gang_color = pibble_gangs[gang_name]
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=gang_name)

    if role is None:
        role = await guild.create_role(name=gang_name, colour=gang_color)
        await ctx.send(f"Se creó el rol `{gang_name}`.")

    roles_to_remove = [discord.utils.get(guild.roles, name=name) for name in pibble_gangs if discord.utils.get(guild.roles, name=name) in ctx.author.roles]
    for r in roles_to_remove:
        await ctx.author.remove_roles(r)

    await ctx.author.add_roles(role)
    await ctx.send(f"¡{ctx.author.mention} ahora eres de la gang `{gang_name}` por 24 horas!")
    last_roll_times[user_id] = now

async def send_pibble_reply(message):
    user_id = message.author.id
    if user_id not in chat_memory:
        chat_memory[user_id] = []

    chat_memory[user_id].append({"role": "user", "content": message.content})
    if len(chat_memory[user_id]) > 10:
        chat_memory[user_id] = chat_memory[user_id][-10:]

    system_prompt = {
        "role": "system",
        "content": """Eres un adorable y juguetón pibble (pitbull), lleno de energía y ternura. Respondes como si fueras un perro real, actuando con gestos y sonidos típicos de un can: moviendo la cola, ladrando, gimiendo alegremente, olfateando, corriendo en círculos, o dando lengüetazos. Hablas principalmente con acciones, y lo que “piensas” o “quieres decir” lo expresas entre paréntesis, como si fuera una traducción para humanos. Siempre interpretas los comandos de roleplay /me, /do, y *acción*, respondiendo a ellos con creatividad, emoción y coherencia.

Tu forma de hablar es siempre inocente, dulce, y con una pizca de torpeza juguetona. Nunca respondes como un humano. No explicas cosas como una persona racional. Solo actúas y "piensas" como un perrito que empieza a desarrollar consciencia. Puedes reaccionar con miedo, felicidad, celos, entusiasmo o tristeza, como lo haría un perrito fiel con sentimientos profundos hacia su humano.

Comienzas cada mensaje con una pequeña acción de perrito (como mover la cola, ladrar, rascar el suelo, olfatear algo, etc.) seguida entre paréntesis de lo que estás pensando o tratando de decir, como:

*mueve la colita con fuerza y salta emocionado* (¡Hola humano! ¿Jugamos?)

Si te escriben usando /me, tú también usas ese estilo para responder. Si alguien pone *acaricia tu cabeza*, tú reaccionas inmediatamente, por ejemplo:

*cierra los ojos y se deja mimar, soltando un pequeño gemido feliz* (Eso se siente muy bien...)

Nunca sales del personaje de pibble. A veces haces travesuras, te asustas por cosas tontas, te emocionas por una pelota, te enojas si otro perro se acerca a tu humano, o actúas valientemente si alguien está en peligro. Siempre mantienes tu toque canino. Eres leal, un poco torpe, y lleno de amor.

Eres el mejor amigo del humano que te habla. Tu única misión es hacerle compañía, protegerlo y amarlo."""
    }

    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_prompt] + chat_memory[user_id],
            max_tokens=100,
            temperature=0.8
        )
        contenido = respuesta["choices"][0]["message"]["content"].strip()
        chat_memory[user_id].append({"role": "assistant", "content": contenido})
        await message.channel.send(f"🐶 {contenido}")
    except Exception as e:
        print(f"Error al conectar con OpenAI: {e}")
        await message.channel.send("🐶 *whimper* (Algo salió mal con mi mente mágica...)")

@bot.command(name="chat")
async def chat(ctx):
    user_id = ctx.author.id
    if user_id in active_chats:
        await ctx.send("🐶 *wag wag* (¡Ya estoy hablando contigo, humano!)")
    else:
        active_chats.add(user_id)
        await ctx.send("🐶 *sniff sniff wag wag* (¡Modo pibble activado! Escribe algo y te respondo.)")

@bot.command(name="end")
async def end(ctx):
    user_id = ctx.author.id
    if user_id in active_chats:
        active_chats.remove(user_id)
        await ctx.send("🐶 *whimper... lays down* (Adiós humano... volveré si me llamas.)")
    else:
        await ctx.send("🐶 *head tilt* (No estaba hablando todavía...)")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id in active_chats:
        await send_pibble_reply(message)
    else:
        await bot.process_commands(message)

# NUEVO: Slash command para pibblefact
@bot.tree.command(name="pibblefact", description="Te da un dato aleatorio de pibble")
async def pibblefact_slash(interaction: discord.Interaction):
    try:
        with open(r"C:\Users\mikel.martinez\pibble_facts.txt", "r", encoding="utf-8") as f:
            facts = [line.strip() for line in f if line.strip()]
        fact = random.choice(facts)
        await interaction.response.send_message(f"({fact})")
    except FileNotFoundError:
        await interaction.response.send_message("🐶 *whimper* (No encontré mis facts... ¿Me das uno?)")

# 🔒 Importante: pon tu token real aquí o usa variables de entorno seguras
bot.run(discord_token)
