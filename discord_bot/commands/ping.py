"""Ping Command Handler

Minimal command handler for system heartbeat.
"""

async def handle(message):
    """Send pong response to channel."""
    await message.channel.send("🏓 pong")
