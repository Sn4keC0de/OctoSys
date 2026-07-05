import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import aiohttp
import os

# Configuración

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1226791485161082922  # ID de tu servidor
TARGET_USER_ID = 638180469191475210  # ID del usuario a eliminar mensajes

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ---- Slash command para borrar mensajes de un usuario ----
@tree.command(name="borrar_mensajes", description="Borra mensajes recientes de un usuario en este canal.")
@app_commands.describe(usuario="Usuario cuyos mensajes se eliminarán", cantidad="Cantidad de mensajes a borrar")
async def borrar_mensajes(interaction: discord.Interaction, usuario: discord.User, cantidad: int):
    # Solo permiten admins/mods - verifica el permiso adecuado
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
        return
    deleted = 0
    try:
        await interaction.response.defer(ephemeral=True)
        async for msg in interaction.channel.history(limit=100):
            if msg.author == usuario:
                await msg.delete()
                deleted += 1
                if deleted >= cantidad:
                    break
                await asyncio.sleep(0.2)
        await interaction.followup.send(f"✅ Borrados {deleted} mensajes de {usuario.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ocurrió un error: {str(e)}", ephemeral=True)


# ---- Slash command para el minijuego del impostor ----
@tree.command(name="impostorvoz", description="Elige un impostor de los del canal de voz actual y da una palabra random de la RAE")
async def impostorvoz(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("Debes estar conectado a un canal de voz.", ephemeral=True)
        return

    canal = interaction.user.voice.channel
    usuarios = [m for m in canal.members if not m.bot]
    if len(usuarios) < 2:
        await interaction.response.send_message("Se requieren al menos dos personas en el canal de voz (sin contar bots).", ephemeral=True)
        return

    nombres = [u.display_name for u in usuarios]
    random.shuffle(nombres)
    impostor = random.choice(nombres)

    # Pedir palabra random a la RAE (usando la api de https://random-word-api.herokuapp.com/ o similar)
    word = await get_random_rae_word()
    mensaje = (
        f"Participantes: {', '.join(nombres)}\n"
        f"😈 El impostor es: **{impostor}**\n"
        f"Palabra random de la RAE: **{word}**"
    )
    await interaction.response.send_message(mensaje, ephemeral=True)


async def get_random_rae_word():
    # Descarga una palabra random de la RAE (usando la web como fuente externa)
    url = "https://random-word-api.herokuapp.com/word?lang=es"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data[0].capitalize() if data else "Sin palabra"
            return "Sin palabra"


# ---- Evento on_ready para confirmar conexión y sincronizar los comandos ----
@bot.event
async def on_ready():
    await tree.sync()
    print(f'Conectado como {bot.user}! Slash commands sincronizados.')


bot.run(TOKEN)
