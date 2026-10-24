from hangarkit.integrations import seatalk


MENTION_PREFIXES = ("@", "<at", "[@")


def parse_slash_command(text: str) -> dict | None:
    parts = (text or "").strip().split()
    while parts and parts[0].lower().startswith(MENTION_PREFIXES):
        parts = parts[1:]

    if not parts or not parts[0].startswith("/"):
        return None

    name = parts[0][1:].strip().lower()
    args = " ".join(parts[1:]).strip()
    return {
        "name": name,
        "args": args,
        "raw": " ".join(parts),
    }


async def handle_slash_command(event: seatalk.WebhookEvent) -> dict | None:
    command = parse_slash_command(event.text)
    if not command:
        return None

    # Placeholder: add command-specific actions here, e.g. /help or /status.
    return {
        "handled": True,
        "command": command,
    }
