"""Message lint: flag words that read as off-platform contact or payment intent.

Fiverr's terms keep conversations and payments on the platform, and its inbox warns
on messages that look like an attempt to move off-platform. The word list below
comes from messages that were blocked or warned in real use. It is NOT Fiverr's
official list, which is not published. A clean result is not a guarantee.

Rewording is only legitimate when the sentence is ABOUT something else (an "email
list" you build for a client). If the sentence is meant to move a buyer off Fiverr,
no rewrite makes it acceptable: do not do it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

# (regex, label, safe rewrite or None, severity)
_RULES: list[tuple[str, str, str | None, str]] = [
    (r"\be-?mails?\b", "email", "subscriber list / mailing list (if about marketing) or 'message me here'", "high"),
    (r"\bgmail\b", "gmail", "message me here", "high"),
    (r"\bpay(?:ment|ments|ing|s|ed)?\b(?!\s+(?:attention|close|particular|special|heed|off|dividends))", "pay/payment", "my fee / the order total", "high"),
    (r"\bpaypal\b", "paypal", "the order total", "high"),
    (r"\b(?:venmo|zelle|cash ?app|transferwise|payoneer|crypto|bitcoin|usdt)\b", "payment app", "the order total", "high"),
    (r"\bbank(?: transfer| account)?\b", "bank", "the order total", "high"),
    (r"\bdiscord\b", "discord", "community group", "high"),
    (r"\bwhats ?app\b", "whatsapp", "message me here", "high"),
    (r"\btelegram\b", "telegram", "message me here", "high"),
    (r"\bskype\b", "skype", "message me here", "high"),
    (r"\bon signal\b|\bsignal app\b", "signal", "message me here", "medium"),
    (r"\b(?:zoom|google meet|teams call)\b", "video call tool", "chat here (or use Fiverr's own meeting option if offered)", "high"),
    (r"\b(?:phone number|mobile number|call me|phone call|video call|voice call|quick call|a call|calls? with)\b", "phone/call", "message me here", "medium"),
    (r"\bcontact me\b", "contact me", "message me here", "medium"),
    (r"\b(?:my|our) (?:site|website)\b", "my site", "my portfolio on Fiverr", "medium"),
    (r"\boutside (?:of )?fiverr\b|\boff[- ]?platform\b", "off-platform", None, "high"),
    (r"\b(?:dm|direct message) me\b", "dm me", "message me here", "medium"),
    (r"https?://\S+|\bwww\.\S+", "external URL", "describe it in words or attach the file in the order", "high"),
    (r"(?<!\w)@[A-Za-z0-9_.]{3,}", "@handle", "remove the handle", "high"),
    (r"\+?\d[\d\s().-]{8,}\d", "phone number", "remove the number", "high"),
]

# Obfuscation looks like evasion and is worse than the plain word.
_OBFUSCATED = [
    (r"\bp[\W_]{1,2}a[\W_]{1,2}y\b", "pay"),
    (r"\be[\W_]{1,2}m[\W_]{1,2}a[\W_]{1,2}i[\W_]{1,2}l\b", "email"),
    (r"\bw[\W_]h[\W_]?a[\W_]?t[\W_]?s[\W_]?a[\W_]?p[\W_]?p\b", "whatsapp"),
    (r"\b\w+\s*\[?\s*(?:at|dot)\s*\]?\s*\w+\s*\[?\s*dot\s*\]?\s*(?:com|net|org)\b", "email-like text"),
]

_EMAIL_ADDR = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


@dataclass
class Finding:
    label: str
    match: str
    start: int
    end: int
    severity: str
    suggestion: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def lint(text: str) -> list[Finding]:
    findings: list[Finding] = []
    taken: list[tuple[int, int]] = []

    def free(a: int, b: int) -> bool:
        return not any(a < y and x < b for x, y in taken)

    for m in _EMAIL_ADDR.finditer(text):
        findings.append(Finding("email address", m.group(), m.start(), m.end(), "high", "remove the address"))
        taken.append((m.start(), m.end()))
    for pat, label in _OBFUSCATED:
        for m in re.finditer(pat, text, re.I):
            if free(m.start(), m.end()):
                findings.append(
                    Finding(
                        f"obfuscated {label}",
                        m.group(),
                        m.start(),
                        m.end(),
                        "high",
                        "rewrite the sentence; disguised spellings look like evasion and are exactly what the filter watches for",
                    )
                )
                taken.append((m.start(), m.end()))
    for pat, label, sugg, sev in _RULES:
        for m in re.finditer(pat, text, re.I):
            if free(m.start(), m.end()):
                findings.append(Finding(label, m.group(), m.start(), m.end(), sev, sugg))
                taken.append((m.start(), m.end()))
    findings.sort(key=lambda f: f.start)
    return findings


_REPLACEMENTS = {
    "email": "subscriber list",
    "e-mail": "subscriber list",
    "gmail": "message me here",
    "pay": "my fee",
    "paying": "my fee",
    "payment": "the order total",
    "payments": "the order total",
    "paypal": "the order total",
    "discord": "community group",
    "whatsapp": "message me here",
    "telegram": "message me here",
    "skype": "message me here",
    "zoom": "chat here",
    "call": "message me here",
    "calls": "messages here",
    "phone": "message me here",
}


def summary(findings: list[Finding]) -> str:
    if not findings:
        return "clean: no known trigger words found (this is not a guarantee)"
    high = sum(1 for f in findings if f.severity == "high")
    return f"{len(findings)} issue(s), {high} high severity"
