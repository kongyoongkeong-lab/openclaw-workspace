"""Help Command Handler

Displays available commands and usage information.
"""

async def handle(message):
    """Show command list and usage."""
    await message.channel.send(
        "**Pentagon Bot Commands**\n\n"
        "**Core Commands:**\n"
        "- `!ping` → System heartbeat\n"
        "- `!status` → Show runtime status\n"
        "- `!help` → Show this help\n\n"
        "**Pentagon System** 🚀\n"
        "**🤖 Autonomous Entity**\n\n"
        "**Next:** Stage 3 → Webhook Integration"
    )
