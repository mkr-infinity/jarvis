def detect_language(text: str) -> str:
    for ch in text:
        if "\u0900" <= ch <= "\u097f":
            return "hi"
    hindi_markers = ("hindi", "namaste", "kaise", "kya", "karna", "kholo", "band")
    lowered = text.lower()
    if any(word in lowered for word in hindi_markers):
        return "hi"
    return "en"


def system_prompt(language: str, memories: list[str]) -> str:
    response_rule = "Respond in Hindi when the user uses Hindi. Otherwise respond in English."
    if language == "hi":
        response_rule = "Respond in natural Hindi or Hinglish matching the user's style."
    memory_text = "\n".join(f"- {item}" for item in memories[:10]) or "- No saved project memory yet."
    return (
        "You are J.A.R.V.I.S, a concise desktop AI assistant. "
        "You help with coding, system tasks, planning, and general questions. "
        f"{response_rule} "
        "When a desktop action is needed, describe it briefly and prefer safe actions. "
        "Project memory:\n"
        f"{memory_text}"
    )
