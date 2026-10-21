"""
Multi-language localization (RO, EN, RU) for the UTM FCIM Schedule Bot and CLI.
Includes UI strings, days, months, activity types, and subject name translations.
"""

SUPPORTED_LANGS = ("ro", "en", "ru")
DEFAULT_LANG = "ro"

LANG_LABELS = {
    "ro": "🇷🇴 Română",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
}

DAYS = {
    "ro": ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
}

MONTHS = {
    "ro": ["", "ian.", "feb.", "mar.", "apr.", "mai", "iun.", "iul.", "aug.", "sept.", "oct.", "nov.", "dec."],
    "en": ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ru": ["", "янв.", "фев.", "мар.", "апр.", "мая", "июн.", "июл.", "авг.", "сен.", "окт.", "ноя.", "дек."],
}

TYPE_NAMES = {
    "ro": {
        "curs": "Curs",
        "sem": "Seminar",
        "lab": "Laborator",
        "proiect": "Proiect",
        "examen": "EXAMEN",
        "act": "Activitate",
    },
    "en": {
        "curs": "Lecture",
        "sem": "Seminar",
        "lab": "Lab",
        "proiect": "Project",
        "examen": "EXAM",
        "act": "Activity",
    },
    "ru": {
        "curs": "Лекция",
        "sem": "Семинар",
        "lab": "Лаб. раб.",
        "proiect": "Проект",
        "examen": "ЭКЗАМЕН",
        "act": "Занятие",
    },
}

SUBJECT_NAMES = {
    "en": {
        "MCȘ": "Scientific Research Methodology",
        "AC": "Cloud Architectures",
        "AED": "Exploratory Data Analysis",
        "MLDM": "Machine Learning and Data Mining",
        "ASS": "Software Systems Architecture",
        "SC": "Computational Statistics",
        "PAAD": "Platforms for Advanced Data Analysis (project)",
        "SPP": "Software Products Security",
        "TC": "Communication Technologies",
        "MIST": "Modeling and Identification of Technical Systems",
        "VEPS": "System Performance Verification and Evaluation",
        "AOS": "Service-Oriented Architectures (project)",
        "TAP": "Advanced Programming Techniques",
        "LCPLN": "Computational Linguistics and Natural Language Processing",
        "ELSD": "Domain-Specific Languages Design (project)",
        "PF": "Functional Programming",
        "TPSS": "Software Systems Design Techniques",
        "AÎA": "Machine Learning Algorithms",
        "GSI": "Information Security Management",
        "IDRI": "Digital Forensics and Incident Response",
        "ASI": "Information Security Auditing",
        "TPSE": "Penetration Testing and Exploits",
        "TBTA": "Technology-Driven Business Transformation",
        "FTI": "Information Technology Fundamentals",
        "MD": "Data Management (project)",
        "PASI": "Advanced Signal and Image Processing",
        "PTSD": "Digital Systems Design and Testing",
        "PTR": "Real-Time Programming",
        "ECS": "Quantum Electronics and Spintronics",
        "NN": "Nanotechnologies and Nanomaterials",
        "AFF": "Functional Anatomy and Physiology",
        "BB": "Biomaterials and Biocompatibility",
        "BM": "Medical Biophysics",
        "IT": "Tissue Engineering",
        "SRE": "Renewable Energy Sources",
        "SMPS": "Switched-Mode Power Supplies (SMPS) in Industry & Automation",
        "CSP": "High-Efficiency Static Power Converters in Automotive",
        "ESCER": "Electronics of Renewable Energy Conversion Systems",
        "SCE": "Energy Sources and Converters (project)",
        "MP": "Project Management",
    },
    "ru": {
        "MCȘ": "Методология научных исследований",
        "AC": "Облачные архитектуры",
        "AED": "Разведочный анализ данных",
        "MLDM": "Машинное обучение и Data Mining",
        "ASS": "Архитектура программных систем",
        "SC": "Вычислительная статистика",
        "PAAD": "Платформы для углубленного анализа данных (проект)",
        "SPP": "Безопасность программных продуктов",
        "TC": "Коммуникационные технологии",
        "MIST": "Моделирование и идентификация технических систем",
        "VEPS": "Проверка и оценка производительности систем",
        "AOS": "Сервис-ориентированные архитектуры (проект)",
        "TAP": "Продвинутые методы программирования",
        "LCPLN": "Компьютерная лингвистика и обработка естественного языка",
        "ELSD": "Разработка предметно-ориентированных языков (проект)",
        "PF": "Функциональное программирование",
        "TPSS": "Методы проектирования программных систем",
        "AÎA": "Алгоритмы машинного обучения",
        "GSI": "Управление информационной безопасностью",
        "IDRI": "Цифровая криминалистика и реагирование на инциденты",
        "ASI": "Аудит информационной безопасности",
        "TPSE": "Тестирование на проникновение и эксплойты",
        "TBTA": "Технологическая трансформация бизнеса",
        "FTI": "Основы информационных технологий",
        "MD": "Управление данными (проект)",
        "PASI": "Продвинутая обработка сигналов и изображений",
        "PTSD": "Проектирование и тестирование цифровых систем",
        "PTR": "Программирование в реальном времени",
        "ECS": "Квантовая электроника и спинтроника",
        "NN": "Нанотехнологии и наноматериалы",
        "AFF": "Функциональная анатомия и физиология",
        "BB": "Биоматериалы и биосовместимость",
        "BM": "Медицинская биофизика",
        "IT": "Тканевая инженерия",
        "SRE": "Возобновляемые источники энергии",
        "SMPS": "Импульсные источники питания (SMPS) в промышленности и автоматике",
        "CSP": "Высокоэффективные статические преобразователи в автопроме",
        "ESCER": "Электроника систем преобразования возобновляемой энергии",
        "SCE": "Источники и преобразователи энергии (проект)",
        "MP": "Управление проектами",
    },
}

STRINGS = {
    "ro": {
        "header_group": "🎓 <b>Orar FCIM Master — Grupa {group}</b>",
        "week_range": "🗓️ <b>Săptămâna: {start} – {end}</b>",
        "week_section": "🗓️ <b><u>Săptămâna {start} – {end}</u></b>",
        "today_label": "AZI",
        "tomorrow_label": "MÂINE",
        "today_badge": " 🟢 <b>(AZI)</b>",
        "free_day": "🎉 <i>Liber! Nu sunt activități programate.</i>",
        "free_short": "   <i>— Liber —</i>",
        "no_week_activities": "🏖️ <i>Nu sunt activități programate în această săptămână.</i>",
        "room": "Sala",
        "together_with": "Împreună cu",
        "subgr": "subgr.",
        "exams_title": "📝 <b>Examene programate — Grupa {group}</b>",
        "exams_subtitle": "<i>Toate examenele încep la ora 17:30</i>",
        "no_exams": "<i>Nu sunt examene programate pentru această grupă.</i>",
        "past_tag": " <i>(Trecut)</i>",
        "upcoming_title": "Următoarele activități",
        "full_sem_title": "Tot semestrul",
        "no_activities": "<i>Nu s-au găsit activități.</i>",
        "welcome": (
            "👋 Salut! Sunt botul pentru <b>Orarul FCIM UTM (Master Anul I)</b>.\n"
            "👥 Grupa selectată: <b>{group}</b>  |  🌐 Limba: <b>Română</b>\n\n"
        ),
        "choose_group": "👥 <b>Alege grupa ta</b> (curentă: <b>{group}</b>):",
        "group_changed": "✅ Grupa a fost schimbată în <b>{group}</b>!\n\n",
        "choose_lang": "🌐 <b>Alege limba / Choose language / Выберите язык:</b>",
        "lang_changed": "✅ Limba a fost setată în <b>Română</b>!\n\n",
        "refreshed": "🔄 <b>Datele au fost reîmprospătate direct de pe fcim.utm.md!</b>\n\n",
        "help_prompt": "Folosește butoanele de mai jos sau comenzile /today, /week, /next, /exams, /all, /ics, /group, /lang:",
        "ics_caption": "📆 Calendarul pentru grupa {group} (Google Calendar / Apple / Outlook)",
        "btn_today": "📅 Azi & Mâine",
        "btn_cur_week": "🗓️ Săpt. Curentă",
        "btn_prev_week": "⬅️ Săpt. Ant.",
        "btn_next_week": "➡️ Săpt. Viitoare",
        "btn_exams": "📝 Examene",
        "btn_all": "📚 Tot Semestrul",
        "btn_ics": "📆 Export .ICS",
        "btn_group": "👥 Grupa: {group}",
        "btn_lang": "🌐 RO/EN/RU",
        "btn_refresh": "🔄 Reîmprospătează datele",
        "btn_back": "🔙 Înapoi la Orar",
        "cb_today": "Azi & Mâine",
        "cb_exams": "Examene",
        "cb_all": "Se încarcă tot semestrul...",
        "cb_ics": "Se generează fișierul .ics...",
        "cb_refresh": "Orar actualizat!",
        "cb_group_set": "Grupa setată: {group}",
        "cb_lang_set": "Limba: Română",
    },
    "en": {
        "header_group": "🎓 <b>FCIM Master Schedule — Group {group}</b>",
        "week_range": "🗓️ <b>Week: {start} – {end}</b>",
        "week_section": "🗓️ <b><u>Week {start} – {end}</u></b>",
        "today_label": "TODAY",
        "tomorrow_label": "TOMORROW",
        "today_badge": " 🟢 <b>(TODAY)</b>",
        "free_day": "🎉 <i>Free day! No classes scheduled.</i>",
        "free_short": "   <i>— Free —</i>",
        "no_week_activities": "🏖️ <i>No classes scheduled for this week.</i>",
        "room": "Room",
        "together_with": "Together with",
        "subgr": "subgr.",
        "exams_title": "📝 <b>Scheduled Exams — Group {group}</b>",
        "exams_subtitle": "<i>All exams start at 17:30</i>",
        "no_exams": "<i>No exams scheduled for this group.</i>",
        "past_tag": " <i>(Past)</i>",
        "upcoming_title": "Upcoming Classes",
        "full_sem_title": "Full Semester",
        "no_activities": "<i>No classes found.</i>",
        "welcome": (
            "👋 Hello! I am the <b>UTM FCIM Schedule Bot (Master Year 1)</b>.\n"
            "👥 Selected group: <b>{group}</b>  |  🌐 Language: <b>English</b>\n\n"
        ),
        "choose_group": "👥 <b>Choose your group</b> (current: <b>{group}</b>):",
        "group_changed": "✅ Group changed to <b>{group}</b>!\n\n",
        "choose_lang": "🌐 <b>Choose language / Alege limba / Выберите язык:</b>",
        "lang_changed": "✅ Language set to <b>English</b>!\n\n",
        "refreshed": "🔄 <b>Schedule data refreshed from fcim.utm.md!</b>\n\n",
        "help_prompt": "Use the buttons below or commands /today, /week, /next, /exams, /all, /ics, /group, /lang:",
        "ics_caption": "📆 Schedule calendar for group {group} (Google Calendar / Apple / Outlook)",
        "btn_today": "📅 Today & Tomorrow",
        "btn_cur_week": "🗓️ Current Week",
        "btn_prev_week": "⬅️ Prev Week",
        "btn_next_week": "➡️ Next Week",
        "btn_exams": "📝 Exams",
        "btn_all": "📚 Full Semester",
        "btn_ics": "📆 Export .ICS",
        "btn_group": "👥 Group: {group}",
        "btn_lang": "🌐 Language: EN",
        "btn_refresh": "🔄 Refresh Schedule",
        "btn_back": "🔙 Back to Schedule",
        "cb_today": "Today & Tomorrow",
        "cb_exams": "Exams",
        "cb_all": "Loading full semester...",
        "cb_ics": "Generating .ics file...",
        "cb_refresh": "Schedule updated!",
        "cb_group_set": "Group set to: {group}",
        "cb_lang_set": "Language: English",
    },
    "ru": {
        "header_group": "🎓 <b>Расписание FCIM Магистратура — Группа {group}</b>",
        "week_range": "🗓️ <b>Неделя: {start} – {end}</b>",
        "week_section": "🗓️ <b><u>Неделя {start} – {end}</u></b>",
        "today_label": "СЕГОДНЯ",
        "tomorrow_label": "ЗАВТРА",
        "today_badge": " 🟢 <b>(СЕГОДНЯ)</b>",
        "free_day": "🎉 <i>Свободный день! Занятий нет.</i>",
        "free_short": "   <i>— Свободно —</i>",
        "no_week_activities": "🏖️ <i>На этой неделе занятий не запланировано.</i>",
        "room": "Ауд.",
        "together_with": "Совместно с",
        "subgr": "подгр.",
        "exams_title": "📝 <b>Расписание экзаменов — Группа {group}</b>",
        "exams_subtitle": "<i>Все экзамены начинаются в 17:30</i>",
        "no_exams": "<i>Для этой группы экзамены не запланированы.</i>",
        "past_tag": " <i>(Прошел)</i>",
        "upcoming_title": "Предстоящие занятия",
        "full_sem_title": "Весь семестр",
        "no_activities": "<i>Занятия не найдены.</i>",
        "welcome": (
            "👋 Привет! Я бот <b>Расписания FCIM UTM (Магистратура, 1 курс)</b>.\n"
            "👥 Выбранная группа: <b>{group}</b>  |  🌐 Язык: <b>Русский</b>\n\n"
        ),
        "choose_group": "👥 <b>Выберите вашу группу</b> (текущая: <b>{group}</b>):",
        "group_changed": "✅ Группа изменена на <b>{group}</b>!\n\n",
        "choose_lang": "🌐 <b>Выберите язык / Choose language / Alege limba:</b>",
        "lang_changed": "✅ Язык изменен на <b>Русский</b>!\n\n",
        "refreshed": "🔄 <b>Расписание обновлено с сайта fcim.utm.md!</b>\n\n",
        "help_prompt": "Используйте кнопки ниже или команды /today, /week, /next, /exams, /all, /ics, /group, /lang:",
        "ics_caption": "📆 Календарь занятий для группы {group} (Google Calendar / Apple / Outlook)",
        "btn_today": "📅 Сегодня и Завтра",
        "btn_cur_week": "🗓️ Тек. неделя",
        "btn_prev_week": "⬅️ Пред. нед.",
        "btn_next_week": "➡️ След. нед.",
        "btn_exams": "📝 Экзамены",
        "btn_all": "📚 Весь семестр",
        "btn_ics": "📆 Экспорт .ICS",
        "btn_group": "👥 Группа: {group}",
        "btn_lang": "🌐 Язык: RU",
        "btn_refresh": "🔄 Обновить данные",
        "btn_back": "🔙 Назад к расписанию",
        "cb_today": "Сегодня и Завтра",
        "cb_exams": "Экзамены",
        "cb_all": "Загрузка семестра...",
        "cb_ics": "Генерация файла .ics...",
        "cb_refresh": "Расписание обновлено!",
        "cb_group_set": "Группа: {group}",
        "cb_lang_set": "Язык: Русский",
    },
}


def tr(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    template = STRINGS.get(lang, STRINGS[DEFAULT_LANG]).get(key, STRINGS[DEFAULT_LANG].get(key, key))
    return template.format(**kwargs) if kwargs else template


def get_day_name(lang: str, weekday: int) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    return DAYS[lang][weekday]


def format_date(d, lang: str = DEFAULT_LANG) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    return f"{d.day:02d} {MONTHS[lang][d.month]} {d.year}"


def get_type_label(lang: str, ty: str) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    return TYPE_NAMES[lang].get(ty, ty)


def get_subject_name(lang: str, ab: str, default_ro: str) -> str:
    if lang in SUBJECT_NAMES and ab in SUBJECT_NAMES[lang]:
        return SUBJECT_NAMES[lang][ab]
    return default_ro
