"""Command Router Layer.

Central dispatch system for Discord bot commands.
Maps commands → handlers using static deterministic routing.
"""

from typing import Awaitable, Callable, Dict

try:  # package import
    from .parser import parse
except ImportError:  # direct script execution
    from parser import parse


Handler = Callable[[object], Awaitable[None]]
COMMANDS: Dict[str, Handler] = {}


def register_handler(command: str):
    """Register a command handler as a decorator."""

    def decorator(handler: Handler) -> Handler:
        COMMANDS[command] = handler
        return handler

    return decorator


@register_handler("ping")
async def handle_ping(message):
    await message.channel.send("🏓 pong")


@register_handler("status")
async def handle_status(message):
    await message.channel.send(
        "**Pentagon Bot Status**\n"
        "```\n"
        "Runtime: Production-Ready\n"
        "VRAM: 8.5GB / 9.5GB\n"
        "GPU: RTX 4070 Super\n"
        "Status: Online 🚀\n"
        "```\n"
        "**🤖 Pentagon Team: @intel | @ops | @comms | @sentinel**"
    )


@register_handler("help")
async def handle_help(message):
    await message.channel.send(
        "**Pentagon Bot Commands**\n\n"
        "- `!ping` → System heartbeat\n"
        "- `!status` → Show runtime status\n"
        "- `!help` → Show this help\n\n"
        "**Pentagon System** 🚀\n"
        "**🤖 Autonomous Entity**"
    )


async def route(message, *args):
    """Route a Discord message to a registered command handler."""
    cmd, _ = parse(message.content)

    if cmd in COMMANDS:
        await COMMANDS[cmd](message)
    elif cmd is not None:
        await message.channel.send(
            f"Unknown command: `{message.content}`\n"
            f"Available commands: `{' '.join(COMMANDS.keys())}`"
        )


def get_router() -> Dict[str, Handler]:
    """Get current handler registry."""
    return COMMANDS


if __name__ == "__main__":
    print("Registered commands:", list(COMMANDS.keys()))
