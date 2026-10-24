from hangarkit import table


MAX_SKILLS = 12
MAX_SKILL_CHARS = 8000


def _enabled(value) -> bool:
    return value is not False


def active_agent_skills() -> list[dict]:
    try:
        rows = table("seatalk_bot_skills").list(sort="-created", perPage=50)
    except Exception:
        return []

    skills = []
    for row in rows or []:
        if not isinstance(row, dict) or not _enabled(row.get("enabled")):
            continue
        title = str(row.get("title") or row.get("name") or "").strip()
        instructions = str(row.get("instructions") or row.get("content") or "").strip()
        if not title or not instructions:
            continue
        skills.append(
            {
                "id": str(row.get("id") or ""),
                "title": title[:120],
                "instructions": instructions,
            }
        )
        if len(skills) >= MAX_SKILLS:
            break
    return skills


def build_agent_skill_prompt(skills: list[dict]) -> str:
    if not skills:
        return ""

    lines = [
        "The app owner provided these additional bot skills. Follow them when relevant.",
        "If a skill conflicts with safety, policy, or the user message, explain the limitation briefly.",
    ]
    for index, skill in enumerate(skills, start=1):
        lines.append(f"\n{index}. {skill['title']}\n{skill['instructions']}")
    return "\n".join(lines)[:MAX_SKILL_CHARS].strip()


def build_agent_message(user_message: str, skill_prompt: str) -> str:
    text = str(user_message or "").strip()
    if not skill_prompt:
        return text
    return f"[BOT_SKILLS]\n{skill_prompt}\n[/BOT_SKILLS]\n\n[USER_MESSAGE]\n{text}\n[/USER_MESSAGE]"
