#!/usr/bin/env python3
"""
Telegram Bot pentru Orarul FCIM UTM Master Anul I
Suportă Română (RO), Engleză (EN) și Rusă (RU).
Zero dependențe externe (folosește doar librăria standard Python + Telegram Bot API).
"""

import argparse
import datetime
import html
import http.server
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import i18n
import orar

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

_DEFAULT_STATE_DIR = Path("/tmp") if os.environ.get("VERCEL") else Path(__file__).parent
PREFS_FILE = _DEFAULT_STATE_DIR / ".bot_user_prefs.json"

TYPE_EMOJI = {
    "curs": "📘",
    "sem": "📙",
    "lab": "📗",
    "proiect": "📕",
    "act": "📕",
    "examen": "🚨",
}


def load_prefs() -> dict:
    if PREFS_FILE.exists():
        try:
            return json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_prefs(prefs: dict):
    try:
        PREFS_FILE.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_user_group(chat_id: int | str, prefs: dict) -> str:
    return prefs.get(str(chat_id), {}).get("group", orar.DEFAULT_GROUP)


def set_user_group(chat_id: int | str, group: str, prefs: dict):
    cid = str(chat_id)
    if cid not in prefs:
        prefs[cid] = {}
    prefs[cid]["group"] = group
    save_prefs(prefs)


def get_user_lang(chat_id: int | str, prefs: dict) -> str:
    lang = prefs.get(str(chat_id), {}).get("lang", i18n.DEFAULT_LANG)
    return lang if lang in i18n.SUPPORTED_LANGS else i18n.DEFAULT_LANG


def set_user_lang(chat_id: int | str, lang: str, prefs: dict):
    cid = str(chat_id)
    if cid not in prefs:
        prefs[cid] = {}
    prefs[cid]["lang"] = lang
    save_prefs(prefs)


# ─────────────────────── FORMATTERS (Telegram HTML) ───────────────────────

def format_card_html(card: dict, lang: str = "ro") -> str:
    t_start, t_end = card["time_range"]
    emoji = TYPE_EMOJI.get(card["type"], "📌")
    ty_label = html.escape(i18n.get_type_label(lang, card["type"]).upper())
    subgr_word = i18n.tr(lang, "subgr")
    sg_str = f" ({subgr_word} {html.escape(str(card['Subgroup']))})" if card["Subgroup"] else ""
    ab = html.escape(card["ab"])
    subj = html.escape(i18n.get_subject_name(lang, card["ab"], card["subject"]))
    room = html.escape(card["room"])
    room_word = i18n.tr(lang, "room")
    teachers = ", ".join(html.escape(t) for t in card["teacher_names"]) if card["teacher_names"] else "—"

    shared_str = ""
    if card["shared_groups"]:
        short_groups = ", ".join(html.escape(g.replace("-261M", "")) for g in card["shared_groups"])
        together_word = i18n.tr(lang, "together_with")
        shared_str = f"\n   👥 <i>{together_word}: {short_groups}</i>"

    return (
        f"🕒 <b>{t_start} – {t_end}</b> | {emoji} <b>[{ty_label}{sg_str}] {ab}</b>\n"
        f"   📖 {subj}\n"
        f"   📍 {room_word}: <b>{room}</b>  |  👤 {teachers}{shared_str}"
    )


def format_today_tomorrow_html(data: dict, cards: list[dict], group: str, lang: str = "ro") -> str:
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    parts = [i18n.tr(lang, "header_group", group=html.escape(group)) + "\n"]

    for target_date, label_key in [(today, "today_label"), (tomorrow, "tomorrow_label")]:
        label = i18n.tr(lang, label_key)
        day_name = i18n.get_day_name(lang, target_date.weekday())
        day_cards = [c for c in cards if c["date"] == target_date]
        parts.append(f"📅 <b>{label}: {day_name}, {i18n.format_date(target_date, lang)}</b>")
        parts.append("────────────────────────")
        if not day_cards:
            parts.append(i18n.tr(lang, "free_day") + "\n")
        else:
            for item in orar.merge_day_slots(data, day_cards):
                parts.append(format_card_html(item, lang))
            parts.append("")

    return "\n".join(parts).strip()


def format_week_html(data: dict, cards: list[dict], group: str, week_offset: int = 0, lang: str = "ro") -> str:
    today = datetime.date.today()
    target_monday = orar.get_monday(today) + datetime.timedelta(weeks=week_offset)
    target_saturday = target_monday + datetime.timedelta(days=5)
    num_days = 6 if target_saturday.isoformat() in data["dates"] else 5
    week_end = target_monday + datetime.timedelta(days=num_days - 1)

    lines = [
        i18n.tr(lang, "header_group", group=html.escape(group)),
        i18n.tr(
            lang,
            "week_range",
            start=i18n.format_date(target_monday, lang),
            end=i18n.format_date(week_end, lang),
        ),
        "════════════════════════",
    ]

    any_activity = False
    for i in range(num_days):
        d = target_monday + datetime.timedelta(days=i)
        day_name = i18n.get_day_name(lang, d.weekday())
        today_badge = i18n.tr(lang, "today_badge") if d == today else ""
        day_cards = [c for c in cards if c["date"] == d]

        lines.append(f"\n▸ <b>{day_name}, {i18n.format_date(d, lang)}</b>{today_badge}")
        if not day_cards:
            lines.append(i18n.tr(lang, "free_short"))
        else:
            any_activity = True
            for item in orar.merge_day_slots(data, day_cards):
                lines.append(format_card_html(item, lang))

    if not any_activity:
        lines.append("\n" + i18n.tr(lang, "no_week_activities"))

    return "\n".join(lines)


def format_exams_html(cards: list[dict], group: str, lang: str = "ro") -> str:
    today = datetime.date.today()
    exams = [c for c in cards if c["type"] == "examen"]
    seen = set()
    unique_exams = []
    for c in sorted(exams, key=lambda x: x["di"]):
        key = (c["di"], c["ab"])
        if key not in seen:
            seen.add(key)
            unique_exams.append(c)

    lines = [
        i18n.tr(lang, "exams_title", group=html.escape(group)),
        i18n.tr(lang, "exams_subtitle"),
        "────────────────────────",
    ]

    if not unique_exams:
        lines.append(i18n.tr(lang, "no_exams"))
    else:
        room_word = i18n.tr(lang, "room")
        for ex in unique_exams:
            d = ex["date"]
            past = d < today
            icon = "✅" if past else "🚨"
            status_tag = i18n.tr(lang, "past_tag") if past else ""
            teachers = ", ".join(html.escape(t) for t in ex["teacher_names"]) if ex["teacher_names"] else "—"
            subj = html.escape(i18n.get_subject_name(lang, ex["ab"], ex["subject"]))
            lines.append(
                f"{icon} <b>{i18n.get_day_name(lang, d.weekday())}, {i18n.format_date(d, lang)}</b>{status_tag}\n"
                f"   📕 <b>{html.escape(ex['ab'])}</b> — {subj}\n"
                f"   📍 {room_word}: <b>{html.escape(ex['room'])}</b>  |  👤 {teachers}\n"
            )

    return "\n".join(lines).strip()


def format_semester_html(data: dict, cards: list[dict], group: str, upcoming_only: bool = True, lang: str = "ro") -> list[str]:
    """Returns a list of HTML message chunks (respecting Telegram's 4096-char limit)."""
    today = datetime.date.today()
    filtered = [c for c in cards if c["type"] != "examen"]
    if upcoming_only:
        filtered = [c for c in filtered if c["date"] >= today]

    by_date: dict[datetime.date, list[dict]] = {}
    for c in filtered:
        by_date.setdefault(c["date"], []).append(c)

    sorted_dates = sorted(by_date.keys())
    title = i18n.tr(lang, "upcoming_title" if upcoming_only else "full_sem_title")
    header = f"{i18n.tr(lang, 'header_group', group=html.escape(group))} <b>({title})</b>\n════════════════════════\n"

    if not sorted_dates:
        return [header + i18n.tr(lang, "no_activities")]

    chunks = []
    current_chunk = header
    last_monday = None

    for d in sorted_dates:
        block_lines = []
        mon = orar.get_monday(d)
        if mon != last_monday:
            fri = mon + datetime.timedelta(days=4)
            block_lines.append(
                "\n" + i18n.tr(
                    lang,
                    "week_section",
                    start=i18n.format_date(mon, lang),
                    end=i18n.format_date(fri, lang),
                )
            )
            last_monday = mon

        today_badge = i18n.tr(lang, "today_badge") if d == today else ""
        block_lines.append(f"▸ <b>{i18n.get_day_name(lang, d.weekday())}, {i18n.format_date(d, lang)}</b>{today_badge}")
        for item in orar.merge_day_slots(data, by_date[d]):
            block_lines.append(format_card_html(item, lang))

        block_text = "\n".join(block_lines) + "\n"
        if len(current_chunk) + len(block_text) > 3800:
            chunks.append(current_chunk.strip())
            current_chunk = block_text
        else:
            current_chunk += block_text

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


# ─────────────────────── KEYBOARDS ───────────────────────

def build_state_cb(action: str, group: str, lang: str, extra: str = "") -> str:
    """Encode stateless user preferences (group & lang) into callback_data so Vercel serverless never loses them."""
    base = f"{action}|{group}|{lang}"
    return f"{base}|{extra}" if extra != "" else base


def parse_state_cb(cb_data: str, default_group: str, default_lang: str) -> tuple[str, str, str, str]:
    """Returns (action, group, lang, extra)."""
    parts = cb_data.split("|")
    if len(parts) >= 3:
        action, grp, lng = parts[0], parts[1], parts[2]
        extra = parts[3] if len(parts) > 3 else ""
        return action, grp, lng, extra
    # Backwards compatibility for old buttons
    if ":" in cb_data:
        a, e = cb_data.split(":", 1)
        return a, default_group, default_lang, e
    return cb_data, default_group, default_lang, ""


def main_menu_keyboard(group: str, week_offset: int = 0, lang: str = "ro") -> dict:
    prev_w = week_offset - 1
    next_w = week_offset + 1
    return {
        "inline_keyboard": [
            [
                {"text": i18n.tr(lang, "btn_today"), "callback_data": build_state_cb("today", group, lang)},
                {"text": i18n.tr(lang, "btn_cur_week"), "callback_data": build_state_cb("week", group, lang, "0")},
            ],
            [
                {"text": i18n.tr(lang, "btn_prev_week"), "callback_data": build_state_cb("week", group, lang, str(prev_w))},
                {"text": i18n.tr(lang, "btn_next_week"), "callback_data": build_state_cb("week", group, lang, str(next_w))},
            ],
            [
                {"text": i18n.tr(lang, "btn_exams"), "callback_data": build_state_cb("exams", group, lang)},
                {"text": i18n.tr(lang, "btn_all"), "callback_data": build_state_cb("all", group, lang)},
            ],
            [
                {"text": i18n.tr(lang, "btn_ics"), "callback_data": build_state_cb("ics", group, lang)},
                {"text": i18n.tr(lang, "btn_group", group=group), "callback_data": build_state_cb("groups", group, lang)},
            ],
            [
                {"text": i18n.tr(lang, "btn_lang"), "callback_data": build_state_cb("langs", group, lang)},
                {"text": i18n.tr(lang, "btn_refresh"), "callback_data": build_state_cb("refresh", group, lang)},
            ],
        ]
    }


def groups_keyboard(groups: list[str], current_group: str, lang: str = "ro") -> dict:
    rows = []
    row = []
    for g in groups:
        prefix = "✅ " if g == current_group else ""
        row.append({"text": f"{prefix}{g}", "callback_data": build_state_cb("setgroup", g, lang)})
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": i18n.tr(lang, "btn_back"), "callback_data": build_state_cb("week", current_group, lang, "0")}])
    return {"inline_keyboard": rows}


def langs_keyboard(current_group: str, current_lang: str) -> dict:
    row = []
    for code in i18n.SUPPORTED_LANGS:
        label = i18n.LANG_LABELS[code]
        prefix = "✅ " if code == current_lang else ""
        row.append({"text": f"{prefix}{label}", "callback_data": build_state_cb("setlang", current_group, code)})
    return {
        "inline_keyboard": [
            row,
            [{"text": i18n.tr(current_lang, "btn_back"), "callback_data": build_state_cb("week", current_group, current_lang, "0")}],
        ]
    }


# ─────────────────────── TELEGRAM BOT API CLIENT ───────────────────────

class TelegramBot:
    def __init__(self, token: str):
        self.token = token.strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.prefs = load_prefs()

    def api_call(self, method: str, payload: dict | None = None, timeout: int = 35) -> dict:
        url = f"{self.base_url}/{method}"
        data_bytes = None
        headers = {}
        if payload is not None:
            data_bytes = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data_bytes, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict | None = None,
    ):
        payload: dict = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.api_call("sendMessage", payload)

    def edit_message(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        reply_markup: dict | None = None,
    ):
        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            return self.api_call("editMessageText", payload)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="ignore")
            if "message is not modified" in err_body:
                return {}
            raise

    def answer_callback(self, callback_id: str, text: str = ""):
        payload: dict = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text
        try:
            self.api_call("answerCallbackQuery", payload, timeout=10)
        except Exception:
            pass

    def send_document(self, chat_id: int | str, file_path: Path, caption: str = ""):
        """Send a file using multipart/form-data."""
        boundary = f"----WebKitFormBoundary{int(time.time() * 1000)}"
        url = f"{self.base_url}/sendDocument"

        body = bytearray()

        def add_field(name: str, value: str):
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{value}\r\n".encode("utf-8"))

        add_field("chat_id", str(chat_id))
        if caption:
            add_field("caption", caption)

        filename = file_path.name
        file_bytes = file_path.read_bytes()
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'
            f"Content-Type: text/calendar\r\n\r\n".encode("utf-8")
        )
        body.extend(file_bytes)
        body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            url,
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def register_commands(self):
        commands = [
            {"command": "start", "description": "Main menu & current week schedule"},
            {"command": "today", "description": "Today & tomorrow schedule"},
            {"command": "week", "description": "Current week schedule"},
            {"command": "next", "description": "Next week schedule"},
            {"command": "exams", "description": "Scheduled exams"},
            {"command": "all", "description": "All upcoming semester classes"},
            {"command": "ics", "description": "Download calendar file (.ics)"},
            {"command": "group", "description": "Change group (e.g. /group SI-261M)"},
            {"command": "lang", "description": "Change language: RO / EN / RU"},
            {"command": "refresh", "description": "Refresh schedule from website"},
        ]
        try:
            self.api_call("setMyCommands", {"commands": commands}, timeout=10)
        except Exception:
            pass

    def send_ics_file(self, chat_id: int | str, data: dict, cards: list[dict], group: str, lang: str = "ro"):
        with tempfile.TemporaryDirectory() as tmpdir:
            ics_path = Path(tmpdir) / f"orar_{group}.ics"
            orar.export_ics(data, cards, group, ics_path)
            self.send_document(
                chat_id,
                ics_path,
                caption=i18n.tr(lang, "ics_caption", group=group),
            )

    def handle_message(self, msg: dict):
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        if not text:
            return

        parts = text.split(maxsplit=1)
        cmd = parts[0].lower().split("@")[0]
        arg = parts[1].strip() if len(parts) > 1 else ""

        group = get_user_group(chat_id, self.prefs)
        lang = get_user_lang(chat_id, self.prefs)
        data = orar.fetch_schedule_data(force_refresh=(cmd == "/refresh"))
        cards = orar.build_group_events(data, group)

        if cmd in ("/start", "/help", "/menu"):
            welcome = i18n.tr(lang, "welcome", group=html.escape(group))
            week_txt = format_week_html(data, cards, group, week_offset=0, lang=lang)
            self.send_message(chat_id, welcome + week_txt, reply_markup=main_menu_keyboard(group, 0, lang))

        elif cmd in ("/today", "/azi"):
            txt = format_today_tomorrow_html(data, cards, group, lang=lang)
            self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))

        elif cmd in ("/week", "/saptamana"):
            offset = 0
            if arg:
                try:
                    offset = int(arg)
                except ValueError:
                    pass
            txt = format_week_html(data, cards, group, week_offset=offset, lang=lang)
            self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(group, offset, lang))

        elif cmd in ("/next", "/viitoare"):
            txt = format_week_html(data, cards, group, week_offset=1, lang=lang)
            self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(group, 1, lang))

        elif cmd in ("/exams", "/examene"):
            txt = format_exams_html(cards, group, lang=lang)
            self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))

        elif cmd in ("/all", "/semestru"):
            chunks = format_semester_html(data, cards, group, upcoming_only=True, lang=lang)
            for i, ch in enumerate(chunks):
                kb = main_menu_keyboard(group, 0, lang) if i == len(chunks) - 1 else None
                self.send_message(chat_id, ch, reply_markup=kb)

        elif cmd == "/ics":
            self.send_ics_file(chat_id, data, cards, group, lang=lang)

        elif cmd in ("/group", "/grupa"):
            if arg and arg.upper() in data["groups"]:
                new_group = arg.upper()
                set_user_group(chat_id, new_group, self.prefs)
                new_cards = orar.build_group_events(data, new_group)
                txt = i18n.tr(lang, "group_changed", group=new_group) + format_week_html(data, new_cards, new_group, 0, lang=lang)
                self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(new_group, 0, lang))
            else:
                self.send_message(
                    chat_id,
                    i18n.tr(lang, "choose_group", group=html.escape(group)),
                    reply_markup=groups_keyboard(data["groups"], group, lang),
                )

        elif cmd in ("/lang", "/language", "/limba", "/ro", "/en", "/ru"):
            target_lang = cmd.lstrip("/") if cmd in ("/ro", "/en", "/ru") else arg.lower()
            if target_lang in i18n.SUPPORTED_LANGS:
                lang = target_lang
                set_user_lang(chat_id, lang, self.prefs)
                txt = i18n.tr(lang, "lang_changed") + format_week_html(data, cards, group, 0, lang=lang)
                self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))
            else:
                self.send_message(
                    chat_id,
                    i18n.tr(lang, "choose_lang"),
                    reply_markup=langs_keyboard(group, lang),
                )

        elif cmd == "/refresh":
            txt = i18n.tr(lang, "refreshed") + format_week_html(data, cards, group, 0, lang=lang)
            self.send_message(chat_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))

        else:
            self.send_message(
                chat_id,
                i18n.tr(lang, "help_prompt"),
                reply_markup=main_menu_keyboard(group, 0, lang),
            )

    def handle_callback(self, cb: dict):
        cb_id = cb["id"]
        msg = cb.get("message")
        if not msg:
            self.answer_callback(cb_id)
            return

        chat_id = msg["chat"]["id"]
        message_id = msg["message_id"]
        raw_data = cb.get("data", "")

        default_group = get_user_group(chat_id, self.prefs)
        default_lang = get_user_lang(chat_id, self.prefs)
        action, group, lang, extra = parse_state_cb(raw_data, default_group, default_lang)

        force_refresh = action == "refresh"
        data = orar.fetch_schedule_data(force_refresh=force_refresh)

        if group not in data["groups"]:
            group = orar.DEFAULT_GROUP
        if lang not in i18n.SUPPORTED_LANGS:
            lang = i18n.DEFAULT_LANG

        # Persist state
        set_user_group(chat_id, group, self.prefs)
        set_user_lang(chat_id, lang, self.prefs)

        if action == "setgroup":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_group_set", group=group))
            cards = orar.build_group_events(data, group)
            txt = format_week_html(data, cards, group, week_offset=0, lang=lang)
            self.edit_message(chat_id, message_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))
            return

        if action == "setlang":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_lang_set"))
            cards = orar.build_group_events(data, group)
            txt = i18n.tr(lang, "lang_changed") + format_week_html(data, cards, group, week_offset=0, lang=lang)
            self.edit_message(chat_id, message_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))
            return

        cards = orar.build_group_events(data, group)

        if action == "today":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_today"))
            txt = format_today_tomorrow_html(data, cards, group, lang=lang)
            self.edit_message(chat_id, message_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))

        elif action == "week":
            offset = int(extra) if extra else 0
            self.answer_callback(cb_id)
            txt = format_week_html(data, cards, group, week_offset=offset, lang=lang)
            self.edit_message(chat_id, message_id, txt, reply_markup=main_menu_keyboard(group, offset, lang))

        elif action == "exams":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_exams"))
            txt = format_exams_html(cards, group, lang=lang)
            self.edit_message(chat_id, message_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))

        elif action == "all":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_all"))
            chunks = format_semester_html(data, cards, group, upcoming_only=True, lang=lang)
            kb_first = main_menu_keyboard(group, 0, lang) if len(chunks) == 1 else None
            self.edit_message(chat_id, message_id, chunks[0], reply_markup=kb_first)
            for i, ch in enumerate(chunks[1:], start=1):
                kb = main_menu_keyboard(group, 0, lang) if i == len(chunks) - 1 else None
                self.send_message(chat_id, ch, reply_markup=kb)

        elif action == "ics":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_ics"))
            self.send_ics_file(chat_id, data, cards, group, lang=lang)

        elif action == "groups":
            self.answer_callback(cb_id)
            self.edit_message(
                chat_id,
                message_id,
                i18n.tr(lang, "choose_group", group=html.escape(group)),
                reply_markup=groups_keyboard(data["groups"], group, lang),
            )

        elif action == "langs":
            self.answer_callback(cb_id)
            self.edit_message(
                chat_id,
                message_id,
                i18n.tr(lang, "choose_lang"),
                reply_markup=langs_keyboard(group, lang),
            )

        elif action == "refresh":
            self.answer_callback(cb_id, i18n.tr(lang, "cb_refresh"))
            txt = format_week_html(data, cards, group, week_offset=0, lang=lang)
            self.edit_message(chat_id, message_id, txt, reply_markup=main_menu_keyboard(group, 0, lang))

        else:
            self.answer_callback(cb_id)

    def start_health_server(self):
        """Start a lightweight HTTP server if PORT is set (for Render / Koyeb / Cloud Run)."""
        port_str = os.environ.get("PORT")
        if not port_str:
            return
        port = int(port_str)

        class HealthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"OK - UTM FCIM Schedule Bot is running.")

            def log_message(self, format, *args):
                pass

        server = http.server.HTTPServer(("0.0.0.0", port), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"🌐 Health-check HTTP server pornit pe portul {port}")

    def run_polling(self):
        self.start_health_server()
        try:
            self.api_call("deleteWebhook", {"drop_pending_updates": False}, timeout=10)
        except Exception:
            pass

        me = self.api_call("getMe", timeout=10)
        bot_info = me.get("result", {})
        username = bot_info.get("username", "unknown_bot")
        print(f"🤖 Botul @{username} a pornit cu succes!")
        print(f"📌 Grupa implicită: {orar.DEFAULT_GROUP}")
        print("Apasă Ctrl+C pentru a opri botul.\n")

        self.register_commands()
        offset = 0

        while True:
            try:
                resp = self.api_call("getUpdates", {"offset": offset, "timeout": 25}, timeout=35)
                for upd in resp.get("result", []):
                    offset = upd["update_id"] + 1
                    try:
                        if "message" in upd:
                            self.handle_message(upd["message"])
                        elif "callback_query" in upd:
                            self.handle_callback(upd["callback_query"])
                    except Exception as err:
                        print(f"[!] Eroare la procesarea update-ului: {err}", file=sys.stderr)
            except KeyboardInterrupt:
                print("\n👋 Bot oprit.")
                break
            except Exception as exc:
                print(f"[!] Eroare conexiune polling: {exc}. Reîncercare în 5 secunde...", file=sys.stderr)
                time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Telegram Bot pentru Orarul FCIM UTM Master.")
    parser.add_argument(
        "-t", "--token",
        default=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        help="Token-ul botului de la @BotFather (sau variabila de mediu TELEGRAM_BOT_TOKEN)"
    )
    args = parser.parse_args()

    token = args.token.strip()
    if not token:
        token_file = Path(__file__).parent / ".bot_token"
        if token_file.exists():
            token = token_file.read_text(encoding="utf-8").strip()

    if not token:
        print("════════════════════════════════════════════════════════════════════")
        print("❗ Lipsește TELEGRAM_BOT_TOKEN!")
        print("1. Deschide Telegram și scrie la @BotFather -> /newbot")
        print("2. Copiază token-ul primit și rulează:")
        print("   python bot.py --token TOKENUL_TAU")
        print("   (sau salvează token-ul în fișierul .bot_token în acest folder)")
        print("════════════════════════════════════════════════════════════════════")
        sys.exit(1)

    bot = TelegramBot(token)
    bot.run_polling()


if __name__ == "__main__":
    main()
