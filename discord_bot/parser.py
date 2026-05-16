"""Command Parser Layer.

Extracts intent from Discord messages.
Normalizes input and extracts command + arguments.
"""

import re

# Common prefix patterns. Keep these escaped in the regex because some are
# regex metacharacters.
PREFIXES = ("!", ".", "/")
KNOWN_COMMANDS = {"ping", "status", "help"}

COMMAND_REGEX = re.compile(
    rf"^(?P<prefix>{'|'.join(re.escape(p) for p in PREFIXES)})?"
    r"\s*(?P<command>\S+)(?:\s+(?P<args>.*))?$"
)


def parse(message: str) -> tuple[str | None, str | None]:
    """Parse a Discord message into ``(command, args)``.

    Examples:
        "!ping" -> ("ping", None)
        ".help" -> ("help", None)
        "/status verbose" -> ("status", "verbose")
        "hello" -> (None, None)
    """
    text = " ".join(message.strip().split())
    if not text:
        return None, None

    match = COMMAND_REGEX.match(text)
    if not match:
        return None, None

    prefix = match.group("prefix") or ""
    command = match.group("command").lower()
    args = match.group("args") or None

    # Require either an explicit command prefix or a known bare command. This
    # prevents ordinary chat messages like "hello" from being routed as
    # unknown bot commands.
    if prefix or command in KNOWN_COMMANDS:
        return command, args

    return None, None


if __name__ == "__main__":
    test_cases = ["!ping", "!ping world", ".help", "/status", "ping", "hello", ""]
    for msg in test_cases:
        cmd, args = parse(msg)
        print(f"{msg!r:20} → cmd={cmd!r:10} args={args!r}")
