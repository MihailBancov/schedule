#!/usr/bin/env python3
"""
UTM FCIM Master Schedule Scraper (Orar Master, Anul I)
Fetches the live schedule from https://fcim.utm.md/orar-master-1/
Default group: SI-261M
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

URL = "https://fcim.utm.md/orar-master-1/"
DEFAULT_GROUP = "SI-261M"
_DEFAULT_CACHE_DIR = Path("/tmp") if os.environ.get("VERCEL") else Path(__file__).parent
CACHE_FILE = _DEFAULT_CACHE_DIR / ".schedule_cache.json"
BUNDLED_DATA_FILE = Path(__file__).parent / "schedule_data.json"
CACHE_MAX_AGE_SECONDS = 6 * 3600  # 6 hours

DAYS_RO = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
MONTHS_RO = [
    "", "ian.", "feb.", "mar.", "apr.", "mai", "iun.",
    "iul.", "aug.", "sept.", "oct.", "nov.", "dec."
]
TYPE_NAMES = {
    "curs": "Curs",
    "sem": "Seminar",
    "lab": "Laborator",
    "proiect": "Proiect",
    "examen": "EXAMEN",
    "act": "Activitate",
}

# ANSI Colors
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    @classmethod
    def disable(cls):
        for attr in ["RESET", "BOLD", "DIM", "BLUE", "GREEN", "YELLOW", "MAGENTA", "RED", "CYAN", "WHITE"]:
            setattr(cls, attr, "")


TYPE_COLORS = {
    "curs": Color.BLUE,
    "sem": Color.YELLOW,
    "lab": Color.GREEN,
    "proiect": Color.MAGENTA,
    "act": Color.MAGENTA,
    "examen": Color.RED,
}


def fetch_schedule_data(force_refresh: bool = False) -> dict:
    """Fetch and parse schedule JSON data from FCIM website or local cache."""
    if not force_refresh and CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < CACHE_MAX_AGE_SECONDS:
            try:
                return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        if CACHE_FILE.exists():
            print(f"{Color.YELLOW}[!] Offline / Eroare rețea ({exc}). Se folosește copia locală din cache.{Color.RESET}")
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if BUNDLED_DATA_FILE.exists():
            return json.loads(BUNDLED_DATA_FILE.read_text(encoding="utf-8"))
        raise RuntimeError(f"Nu s-a putut accesa {URL}: {exc}") from exc

    # Extract var DATA = {...};
    match_data = re.search(r"var\s+DATA\s*=\s*(\{.*?\});\s*\r?\n", html, re.DOTALL)
    if not match_data:
        raise RuntimeError("Nu s-a găsit obiectul DATA în pagina FCIM.")
    data = json.loads(match_data.group(1))

    # Extract var TITLURI = {...};
    titles = {}
    match_titles = re.search(r"var\s+TITLURI\s*=\s*(\{.*?\});", html, re.DOTALL)
    if match_titles:
        try:
            titles = json.loads(match_titles.group(1))
        except Exception:
            pass
    data["titles"] = titles

    try:
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    return data


def parse_date(date_str: str) -> datetime.date:
    y, m, d = map(int, date_str.split("-"))
    return datetime.date(y, m, d)


def format_date_ro(d: datetime.date) -> str:
    return f"{d.day:02d} {MONTHS_RO[d.month]} {d.year}"


def get_monday(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())


def get_slot_times(data: dict, date_idx: int, slot: int) -> tuple[str, str]:
    special = data.get("special", {})
    date_str = data["dates"][date_idx]
    times = special.get(date_str, ["17:30", "19:00", "19:10", "20:40"])
    if slot == 1:
        return times[0], times[1]
    elif slot == 2:
        return times[2], times[3]
    else:  # Merged slot 1+2
        return times[0], times[3]


def format_teacher(data: dict, teacher_key: str) -> str:
    if not teacher_key:
        return "—"
    name = data["teachers"].get(teacher_key, teacher_key)
    title = data.get("titles", {}).get(name, "")
    return f"{title} {name}".strip()


def build_group_events(data: dict, group: str) -> list[dict]:
    """Build structured and merged cards for a given group."""
    raw_events = data["ev"]
    # Build shared index across groups: (di, slot, ab, ty, teacher, room) -> [groups]
    share_idx: dict[tuple, list[str]] = {}
    for ev in raw_events:
        di, slot, grp, ab, ty, sg, tk, room = ev
        key = (di, slot, ab, ty, tk, room)
        if grp not in share_idx.setdefault(key, []):
            share_idx[key].append(grp)

    # Filter for target group and merge multiple teachers for the same card
    group_ev = [e for e in raw_events if e[2] == group]
    cards_map: dict[tuple, dict] = {}
    cards_list: list[dict] = []

    for ev in group_ev:
        di, slot, grp, ab, ty, sg, tk, room = ev
        key = (di, slot, ab, ty, sg, room)
        if key not in cards_map:
            card = {
                "di": di,
                "date": parse_date(data["dates"][di]),
                "date_str": data["dates"][di],
                "slot": slot,
                "ab": ab,
                "subject": data["names"].get(ab, ab),
                "type": ty,
                "type_label": TYPE_NAMES.get(ty, ty),
                "Subgroup": sg,
                "room": room or "—",
                "teachers": [],
                "shared_groups": [],
            }
            cards_map[key] = card
            cards_list.append(card)
        if tk and tk not in cards_map[key]["teachers"]:
            cards_map[key]["teachers"].append(tk)

    # Populate shared groups and teacher names
    for card in cards_list:
        shared = []
        for tk in card["teachers"]:
            s_key = (card["di"], card["slot"], card["ab"], card["type"], tk, card["room"] if card["room"] != "—" else "")
            for g in share_idx.get(s_key, []):
                if g != group and g not in shared:
                    shared.append(g)
        card["shared_groups"] = shared
        card["teacher_names"] = [format_teacher(data, tk) for tk in card["teachers"]]

    return cards_list


def merge_day_slots(data: dict, day_cards: list[dict]) -> list[dict]:
    """Merge slot 1 and slot 2 if they have identical activities."""
    s1 = [c for c in day_cards if c["slot"] == 1]
    s2 = [c for c in day_cards if c["slot"] == 2]

    def sig(cards: list[dict]) -> str:
        items = [
            f"{c['ab']}|{c['type']}|{c['Subgroup']}|{c['room']}|{','.join(c['teachers'])}"
            for c in cards
        ]
        return "#".join(sorted(items))

    out = []
    if s1 and sig(s1) == sig(s2):
        for c in s1:
            merged = dict(c)
            merged["time_range"] = get_slot_times(data, c["di"], 0)
            merged["slots_label"] = "Perechea 1 + 2"
            out.append(merged)
    else:
        for c in s1:
            item = dict(c)
            item["time_range"] = get_slot_times(data, c["di"], 1)
            item["slots_label"] = "Perechea 1"
            out.append(item)
        for c in s2:
            item = dict(c)
            item["time_range"] = get_slot_times(data, c["di"], 2)
            item["slots_label"] = "Perechea 2"
            out.append(item)
    return out


def print_event_card(card: dict, indent: str = "  "):
    t_start, t_end = card["time_range"]
    ty_color = TYPE_COLORS.get(card["type"], Color.WHITE)
    ty_label = card["type_label"].upper()
    sg_str = f" (subgr. {card['Subgroup']})" if card["Subgroup"] else ""

    print(
        f"{indent}{Color.BOLD}{t_start} – {t_end}{Color.RESET}  "
        f"{ty_color}{Color.BOLD}[{ty_label}{sg_str}]{Color.RESET} "
        f"{Color.BOLD}{card['ab']}{Color.RESET} — {card['subject']}"
    )
    teachers_str = ", ".join(card["teacher_names"]) if card["teacher_names"] else "—"
    shared_str = ""
    if card["shared_groups"]:
        short_groups = ", ".join(g.replace("-261M", "") for g in card["shared_groups"])
        shared_str = f"  {Color.DIM}(împreună cu {short_groups}){Color.RESET}"

    print(
        f"{indent}              "
        f"📍 Sala: {Color.CYAN}{Color.BOLD}{card['room']}{Color.RESET}  |  "
        f"👤 {teachers_str}{shared_str}"
    )


def render_day_view(data: dict, cards: list[dict], target_date: datetime.date, title_label: str):
    today = datetime.date.today()
    day_cards = [c for c in cards if c["date"] == target_date]
    day_name = DAYS_RO[target_date.weekday()]
    is_today_tag = f" {Color.GREEN}(AZI){Color.RESET}" if target_date == today else ""

    print(f"\n{Color.BOLD}📅 {title_label}: {day_name}, {format_date_ro(target_date)}{is_today_tag}{Color.RESET}")
    print("─" * 72)
    if not day_cards:
        print(f"  {Color.DIM}🎉 Liber! Nu sunt activități programate în această zi.{Color.RESET}")
    else:
        for item in merge_day_slots(data, day_cards):
            print_event_card(item)
    print()


def render_week_view(data: dict, cards: list[dict], group: str, week_offset: int = 0):
    today = datetime.date.today()
    target_monday = get_monday(today) + datetime.timedelta(weeks=week_offset)
    target_saturday = target_monday + datetime.timedelta(days=5)

    # Check if Saturday has activities in dataset
    sat_iso = target_saturday.isoformat()
    num_days = 6 if sat_iso in data["dates"] else 5
    week_end = target_monday + datetime.timedelta(days=num_days - 1)

    print(
        f"\n{Color.BOLD}🎓 Orar FCIM Master — Grupa {Color.CYAN}{group}{Color.RESET}\n"
        f"{Color.BOLD}🗓️  Săptămâna: {format_date_ro(target_monday)} – {format_date_ro(week_end)}{Color.RESET}"
    )
    print("═" * 72)

    any_activity = False
    for i in range(num_days):
        d = target_monday + datetime.timedelta(days=i)
        day_name = DAYS_RO[d.weekday()]
        is_today = d == today
        today_badge = f" {Color.GREEN}◀ AZI{Color.RESET}" if is_today else ""
        header_color = Color.GREEN if is_today else Color.WHITE

        day_cards = [c for c in cards if c["date"] == d]
        print(f"\n{header_color}{Color.BOLD}▸ {day_name}, {format_date_ro(d)}{today_badge}{Color.RESET}")

        if not day_cards:
            print(f"  {Color.DIM}— Liber —{Color.RESET}")
        else:
            any_activity = True
            for item in merge_day_slots(data, day_cards):
                print_event_card(item)

    if not any_activity:
        print(f"\n{Color.YELLOW}Nu sunt activități programate în această săptămână (vacanță sau în afara semestrului).{Color.RESET}")
    print("\n" + "═" * 72)


def render_semester_view(data: dict, cards: list[dict], group: str, upcoming_only: bool = True):
    today = datetime.date.today()
    filtered = [c for c in cards if c["type"] != "examen"]
    if upcoming_only:
        filtered = [c for c in filtered if c["date"] >= today]

    by_date: dict[datetime.date, list[dict]] = {}
    for c in filtered:
        by_date.setdefault(c["date"], []).append(c)

    sorted_dates = sorted(by_date.keys())
    mode_str = "Următoarele activități" if upcoming_only else "Tot semestrul"
    print(f"\n{Color.BOLD}🎓 Orar FCIM Master — Grupa {Color.CYAN}{group}{Color.RESET} ({mode_str})")
    print("═" * 72)

    if not sorted_dates:
        print(f"  {Color.DIM}Nu s-au găsit activități.{Color.RESET}")
        return

    last_monday = None
    for d in sorted_dates:
        mon = get_monday(d)
        if mon != last_monday:
            fri = mon + datetime.timedelta(days=4)
            print(f"\n{Color.MAGENTA}{Color.BOLD}── Săptămâna {format_date_ro(mon)} – {format_date_ro(fri)} ──{Color.RESET}")
            last_monday = mon

        is_today = d == today
        today_badge = f" {Color.GREEN}◀ AZI{Color.RESET}" if is_today else ""
        print(f"{Color.BOLD}{DAYS_RO[d.weekday()]}, {format_date_ro(d)}{today_badge}{Color.RESET}")
        for item in merge_day_slots(data, by_date[d]):
            print_event_card(item)
    print("\n" + "═" * 72)


def render_exams_view(data: dict, cards: list[dict], group: str):
    today = datetime.date.today()
    exams = [c for c in cards if c["type"] == "examen"]
    # Deduplicate by (di, ab) since exam occupies slots 1 and 2
    seen = set()
    unique_exams = []
    for c in sorted(exams, key=lambda x: x["di"]):
        key = (c["di"], c["ab"])
        if key not in seen:
            seen.add(key)
            unique_exams.append(c)

    print(f"\n{Color.BOLD}📝 Examene programate — Grupa {Color.CYAN}{group}{Color.RESET} (încep la 17:30)")
    print("─" * 72)
    if not unique_exams:
        print(f"  {Color.DIM}Nu sunt examene programate.{Color.RESET}")
    else:
        for ex in unique_exams:
            d = ex["date"]
            past = d < today
            status = f"{Color.DIM}[TRECUT]{Color.RESET} " if past else f"{Color.RED}●{Color.RESET} "
            teachers_str = ", ".join(ex["teacher_names"]) if ex["teacher_names"] else "—"
            print(
                f"  {status}{Color.BOLD}{DAYS_RO[d.weekday()]}, {format_date_ro(d)}{Color.RESET}  |  "
                f"{Color.BOLD}{ex['ab']}{Color.RESET} ({ex['subject']})\n"
                f"      📍 Sala: {Color.CYAN}{Color.BOLD}{ex['room']}{Color.RESET}  |  👤 {teachers_str}"
            )
    print()


def export_ics(data: dict, cards: list[dict], group: str, out_path: Path):
    """Export schedule to iCalendar (.ics) format for Google/Apple/Outlook Calendar."""
    by_date: dict[datetime.date, list[dict]] = {}
    for c in cards:
        by_date.setdefault(c["date"], []).append(c)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//UTM FCIM Schedule Scraper//RO",
        f"X-WR-CALNAME:Orar UTM {group}",
        "X-WR-TIMEZONE:Europe/Chisinau",
    ]

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for d in sorted(by_date.keys()):
        merged = merge_day_slots(data, by_date[d])
        for idx, item in enumerate(merged):
            t_start, t_end = item["time_range"]
            h1, m1 = map(int, t_start.split(":"))
            h2, m2 = map(int, t_end.split(":"))
            dt_start = f"{d.strftime('%Y%m%d')}T{h1:02d}{m1:02d}00"
            dt_end = f"{d.strftime('%Y%m%d')}T{h2:02d}{m2:02d}00"

            ty_label = item["type_label"]
            sg_str = f" (subgr. {item['Subgroup']})" if item["Subgroup"] else ""
            summary = f"[{ty_label}] {item['ab']} — {item['subject']}{sg_str}"
            teachers_str = ", ".join(item["teacher_names"])
            desc = f"Profesor: {teachers_str}\\nDisciplina: {item['subject']} ({ty_label})"
            if item["shared_groups"]:
                desc += f"\\nÎmpreună cu: {', '.join(item['shared_groups'])}"

            uid = f"utm-fcim-{group}-{d.strftime('%Y%m%d')}-{item['slot']}-{idx}@fcim.utm.md"
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_utc}",
                f"DTSTART;TZID=Europe/Chisinau:{dt_start}",
                f"DTEND;TZID=Europe/Chisinau:{dt_end}",
                f"SUMMARY:{summary}",
                f"LOCATION:Sala {item['room']} (FCIM UTM)",
                f"DESCRIPTION:{desc}",
                "END:VEVENT",
            ])

    lines.append("END:VCALENDAR")
    out_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"{Color.GREEN}✔ Fișierul calendar a fost salvat în: {out_path.resolve()}{Color.RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Scraper pentru orarul FCIM UTM Master Anul I (implicit: SI-261M)."
    )
    parser.add_argument(
        "-g", "--group",
        default=DEFAULT_GROUP,
        help=f"Grupa (implicit: {DEFAULT_GROUP})"
    )
    parser.add_argument(
        "-t", "--today",
        action="store_true",
        help="Afișează doar orarul de azi și de mâine"
    )
    parser.add_argument(
        "-n", "--next",
        action="store_true",
        help="Afișează orarul pentru săptămâna viitoare"
    )
    parser.add_argument(
        "-w", "--week",
        type=int,
        default=0,
        help="Offset săptămână față de săptămâna curentă (ex: 1 = săptămâna viitoare, -1 = săptămâna trecută)"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Afișează toate activitățile rămase din semestru"
    )
    parser.add_argument(
        "--full-semester",
        action="store_true",
        help="Afișează absolut tot semestrul (inclusiv zilele trecute)"
    )
    parser.add_argument(
        "-e", "--exams",
        action="store_true",
        help="Afișează doar examenele"
    )
    parser.add_argument(
        "--ics",
        metavar="FILE",
         nargs="?",
        const="orar_SI-261M.ics",
        help="Exportă tot orarul în format .ics (pentru Google Calendar / telefon)"
    )
    parser.add_argument(
        "-r", "--refresh",
        action="store_true",
        help="Forțează descărcarea datelor proaspete de pe site (ignoră cache-ul)"
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="Afișează toate grupele disponibile"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Dezactivează culorile în terminal"
    )

    args = parser.parse_args()
    if args.no_color or not sys.stdout.isatty():
        Color.disable()

    data = fetch_schedule_data(force_refresh=args.refresh)

    if args.list_groups:
        print("Grupe disponibile:", ", ".join(data["groups"]))
        return

    group = args.group.upper()
    if group not in data["groups"]:
        print(f"{Color.RED}Eroare: Grupa '{group}' nu există.{Color.RESET}")
        print("Grupe disponibile:", ", ".join(data["groups"]))
        sys.exit(1)

    cards = build_group_events(data, group)

    if args.ics:
        export_ics(data, cards, group, Path(args.ics))
        return

    if args.today:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        render_day_view(data, cards, today, f"AZI ({group})")
        render_day_view(data, cards, tomorrow, f"MÂINE ({group})")
        return

    if args.exams:
        render_exams_view(data, cards, group)
        return

    if args.all or args.full_semester:
        render_semester_view(data, cards, group, upcoming_only=not args.full_semester)
        render_exams_view(data, cards, group)
        return

    week_offset = 1 if args.next else args.week
    render_week_view(data, cards, group, week_offset=week_offset)
    render_exams_view(data, cards, group)


if __name__ == "__main__":
    main()
