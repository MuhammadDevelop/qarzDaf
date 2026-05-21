import telebot
from telebot import types
import random
import time
import json
import os
from collections import defaultdict

# ==========================================
# BOT TOKEN - O'zingizning tokeningizni kiriting
# ==========================================
BOT_TOKEN = "8883773002:AAFghpw-SX5-Ph8nCRUYYLVbgbEgPYAMQm4"

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# O'YINCHILAR HOLATI (xotira)
# ==========================================
user_states = {}       # har bir foydalanuvchining joriy o'yin holati
user_scores = defaultdict(lambda: {
    "wins": 0, "losses": 0, "draws": 0, "total_games": 0
})

def get_state(uid):
    return user_states.get(uid, {})

def set_state(uid, state):
    user_states[uid] = state

def clear_state(uid):
    user_states.pop(uid, None)

# ==========================================
# ASOSIY MENYU
# ==========================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🎯 Taxmin qilish",       callback_data="game_guess"),
        types.InlineKeyboardButton("✊ Tosh-qaychi-qog'oz",  callback_data="game_rps"),
        types.InlineKeyboardButton("🧠 Viktorina",           callback_data="game_quiz"),
        types.InlineKeyboardButton("🔢 Matematik duel",      callback_data="game_math"),
        types.InlineKeyboardButton("🎰 Slot mashina",        callback_data="game_slot"),
        types.InlineKeyboardButton("🐍 Yashirin so'z",       callback_data="game_word"),
        types.InlineKeyboardButton("🎲 Zar o'yini",         callback_data="game_dice"),
        types.InlineKeyboardButton("🃏 Yuqori karta",        callback_data="game_card"),
        types.InlineKeyboardButton("🔤 Anagram",             callback_data="game_anagram"),
        types.InlineKeyboardButton("🎡 Omad g'ildiragi",     callback_data="game_wheel"),
        types.InlineKeyboardButton("📊 Mening natijalarim",  callback_data="stats"),
    ]
    markup.add(*buttons)
    return markup

# ==========================================
# /start va /help
# ==========================================
@bot.message_handler(commands=["start", "help"])
def start(message):
    clear_state(message.from_user.id)
    name = message.from_user.first_name or "O'yinchi"
    text = (
        f"👋 Salom, <b>{name}</b>!\n\n"
        "🎮 <b>O'yinlar Botiga Xush Kelibsiz!</b>\n\n"
        "Bu botda <b>10 ta qiziqarli o'yin</b> mavjud:\n\n"
        "🎯 Raqam taxmin qilish\n"
        "✊ Tosh-Qaychi-Qog'oz\n"
        "🧠 Viktorina (bilim testi)\n"
        "🔢 Matematik duel\n"
        "🎰 Slot mashina\n"
        "🐍 Yashirin so'z\n"
        "🎲 Zar o'yini\n"
        "🃏 Yuqori karta\n"
        "🔤 Anagram\n"
        "🎡 Omad g'ildiragi\n\n"
        "Qaysi o'yinni o'ynashni xohlaysiz? 👇"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=main_menu())

@bot.message_handler(commands=["menu"])
def menu_cmd(message):
    clear_state(message.from_user.id)
    bot.send_message(message.chat.id, "🎮 Asosiy menyu:", reply_markup=main_menu())

# ==========================================
# CALLBACK ROUTER
# ==========================================
@bot.callback_query_handler(func=lambda c: True)
def callback_router(call):
    uid = call.from_user.id
    data = call.data
    bot.answer_callback_query(call.id)

    # O'yin ishga tushiruvchilar
    game_launchers = {
        "game_guess":   start_guess,
        "game_rps":     start_rps,
        "game_quiz":    start_quiz,
        "game_math":    start_math,
        "game_slot":    start_slot,
        "game_word":    start_word,
        "game_dice":    start_dice,
        "game_card":    start_card,
        "game_anagram": start_anagram,
        "game_wheel":   start_wheel,
        "stats":        show_stats,
        "main_menu":    go_main_menu,
    }

    if data in game_launchers:
        game_launchers[data](call)
    elif data.startswith("rps_"):
        handle_rps(call)
    elif data.startswith("quiz_"):
        handle_quiz(call)
    elif data.startswith("dice_"):
        handle_dice(call)
    elif data.startswith("card_"):
        handle_card(call)
    elif data.startswith("word_hint"):
        handle_word_hint(call)
    elif data.startswith("wheel_spin"):
        handle_wheel_spin(call)

def go_main_menu(call):
    clear_state(call.from_user.id)
    bot.edit_message_text(
        "🎮 Asosiy menyu — o'yin tanlang:",
        call.message.chat.id, call.message.message_id,
        reply_markup=main_menu()
    )

def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    return markup

def record_result(uid, result):
    """result: 'win', 'loss', 'draw'"""
    user_scores[uid]["total_games"] += 1
    if result == "win":
        user_scores[uid]["wins"] += 1
    elif result == "loss":
        user_scores[uid]["losses"] += 1
    else:
        user_scores[uid]["draws"] += 1

# ==========================================
# O'YIN 1: RAQAM TAXMIN QILISH (1–100)
# ==========================================
def start_guess(call):
    uid = call.from_user.id
    secret = random.randint(1, 100)
    set_state(uid, {"game": "guess", "secret": secret, "attempts": 0, "max": 7})
    bot.edit_message_text(
        "🎯 <b>Raqam Taxmin Qilish</b>\n\n"
        "Men 1 dan 100 gacha raqam o'yladim.\n"
        "Sizda <b>7 ta urinish</b> bor.\n\n"
        "Raqamni yozing 👇",
        call.message.chat.id, call.message.message_id, parse_mode="HTML",
        reply_markup=back_button()
    )

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("game") == "guess")
def handle_guess(message):
    uid = message.from_user.id
    state = get_state(uid)
    try:
        guess = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Iltimos, faqat raqam yozing!")
        return

    state["attempts"] += 1
    secret = state["secret"]
    attempts_left = state["max"] - state["attempts"]

    if guess == secret:
        record_result(uid, "win")
        clear_state(uid)
        bot.send_message(
            message.chat.id,
            f"🎉 <b>To'g'ri!</b> Raqam <b>{secret}</b> edi.\n"
            f"Siz {state['attempts']} ta urinishda topdingiz! 🏆",
            parse_mode="HTML", reply_markup=back_button()
        )
    elif state["attempts"] >= state["max"]:
        record_result(uid, "loss")
        clear_state(uid)
        bot.send_message(
            message.chat.id,
            f"😞 Urinishlar tugadi! Raqam <b>{secret}</b> edi.",
            parse_mode="HTML", reply_markup=back_button()
        )
    elif guess < secret:
        bot.send_message(
            message.chat.id,
            f"⬆️ Kattaroq! ({attempts_left} ta urinish qoldi)"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"⬇️ Kichikroq! ({attempts_left} ta urinish qoldi)"
        )

# ==========================================
# O'YIN 2: TOSH-QAYCHI-QOG'OZ
# ==========================================
RPS_CHOICES = {"tosh": "🪨", "qaychi": "✂️", "qogoz": "📄"}
RPS_WIN = {"tosh": "qaychi", "qaychi": "qogoz", "qogoz": "tosh"}

def start_rps(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🪨 Tosh",   callback_data="rps_tosh"),
        types.InlineKeyboardButton("✂️ Qaychi", callback_data="rps_qaychi"),
        types.InlineKeyboardButton("📄 Qog'oz", callback_data="rps_qogoz"),
    )
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    bot.edit_message_text(
        "✊ <b>Tosh-Qaychi-Qog'oz</b>\n\nTanlang:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

def handle_rps(call):
    uid = call.from_user.id
    player = call.data.replace("rps_", "")
    bot_choice = random.choice(list(RPS_CHOICES.keys()))
    pe = RPS_CHOICES[player]
    be = RPS_CHOICES[bot_choice]

    if player == bot_choice:
        result = "draw"
        msg = f"{pe} vs {be}\n\n🤝 <b>Durrang!</b>"
    elif RPS_WIN[player] == bot_choice:
        result = "win"
        msg = f"{pe} vs {be}\n\n🎉 <b>Siz yutdingiz!</b>"
    else:
        result = "loss"
        msg = f"{pe} vs {be}\n\n😞 <b>Bot yutdi!</b>"

    record_result(uid, result)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 Qayta",      callback_data="game_rps"),
        types.InlineKeyboardButton("🏠 Menyu",      callback_data="main_menu"),
    )
    bot.edit_message_text(
        f"✊ <b>Tosh-Qaychi-Qog'oz</b>\n\nSiz: {pe}  |  Bot: {be}\n\n{msg}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

# ==========================================
# O'YIN 3: VIKTORINA
# ==========================================
QUIZ_QUESTIONS = [
    {"q": "O'zbekistonning poytaxti qaysi shahar?",
     "options": ["Samarqand", "Toshkent", "Buxoro", "Namangan"], "ans": 1},
    {"q": "Quyosh sistemasidagi eng katta sayyora qaysi?",
     "options": ["Saturn", "Neptun", "Yupiter", "Uran"], "ans": 2},
    {"q": "1+1 nechaga teng?",
     "options": ["1", "3", "4", "2"], "ans": 3},
    {"q": "Dunyo okeanlarining soni?",
     "options": ["3", "4", "5", "6"], "ans": 2},
    {"q": "Python kimdir tomonidan yaratilgan?",
     "options": ["Linus Torvalds", "Guido van Rossum", "James Gosling", "Bjarne Stroustrup"], "ans": 1},
    {"q": "Eng baland tog' qaysi?",
     "options": ["K2", "Kangchenjunga", "Everest", "Lhotse"], "ans": 2},
    {"q": "Suv necha darajada qaynaydi (dengiz sathida)?",
     "options": ["90°C", "95°C", "85°C", "100°C"], "ans": 3},
    {"q": "Inson tanasidagi eng katta organ?",
     "options": ["Jigar", "Miya", "Teri", "O'pka"], "ans": 2},
    {"q": "HTML nima uchun ishlatiladi?",
     "options": ["Ma'lumotlar bazasi", "Web sahifalar", "Animatsiya", "Ovoz"], "ans": 1},
    {"q": "Afrika qit'asidagi eng uzun daryo?",
     "options": ["Kongo", "Niger", "Nil", "Zambezi"], "ans": 2},
]

def start_quiz(call):
    uid = call.from_user.id
    q_index = random.randint(0, len(QUIZ_QUESTIONS) - 1)
    set_state(uid, {"game": "quiz", "q_index": q_index})
    send_quiz_question(call.message.chat.id, call.message.message_id, q_index, edit=True)

def send_quiz_question(chat_id, msg_id, q_index, edit=False):
    q = QUIZ_QUESTIONS[q_index]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(q["options"]):
        markup.add(types.InlineKeyboardButton(f"{i}. {opt}", callback_data=f"quiz_{q_index}_{i}"))
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    text = f"🧠 <b>Viktorina</b>\n\n<b>{q['q']}</b>"
    if edit:
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

def handle_quiz(call):
    uid = call.from_user.id
    _, q_index_str, ans_str = call.data.split("_")
    q_index = int(q_index_str)
    user_ans = int(ans_str)
    q = QUIZ_QUESTIONS[q_index]
    correct = q["ans"]

    if user_ans == correct:
        record_result(uid, "win")
        result_text = f"✅ <b>To'g'ri!</b>\nJavob: <b>{q['options'][correct]}</b>"
    else:
        record_result(uid, "loss")
        result_text = (
            f"❌ <b>Noto'g'ri!</b>\n"
            f"Siz: {q['options'][user_ans]}\n"
            f"To'g'ri javob: <b>{q['options'][correct]}</b>"
        )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 Yangi savol", callback_data="game_quiz"),
        types.InlineKeyboardButton("🏠 Menyu",       callback_data="main_menu"),
    )
    bot.edit_message_text(
        f"🧠 <b>Viktorina</b>\n\n{result_text}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

# ==========================================
# O'YIN 4: MATEMATIK DUEL
# ==========================================
def start_math(call):
    uid = call.from_user.id
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    op = random.choice(["+", "-", "*"])
    if op == "+":
        ans = a + b
    elif op == "-":
        ans = a - b
    else:
        ans = a * b
    set_state(uid, {"game": "math", "answer": ans})
    bot.edit_message_text(
        f"🔢 <b>Matematik Duel</b>\n\n"
        f"<code>{a} {op} {b} = ?</code>\n\n"
        "Javobni yozing 👇",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=back_button()
    )

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("game") == "math")
def handle_math(message):
    uid = message.from_user.id
    state = get_state(uid)
    try:
        user_ans = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Faqat raqam yozing!")
        return

    correct = state["answer"]
    clear_state(uid)
    if user_ans == correct:
        record_result(uid, "win")
        bot.send_message(
            message.chat.id, f"✅ <b>To'g'ri!</b> Javob: <b>{correct}</b> 🎉",
            parse_mode="HTML", reply_markup=back_button()
        )
    else:
        record_result(uid, "loss")
        bot.send_message(
            message.chat.id,
            f"❌ <b>Noto'g'ri!</b>\nSizning javobingiz: {user_ans}\nTo'g'ri javob: <b>{correct}</b>",
            parse_mode="HTML", reply_markup=back_button()
        )

# ==========================================
# O'YIN 5: SLOT MASHINA 🎰
# ==========================================
SLOT_SYMBOLS = ["🍒", "🍋", "🍇", "⭐", "💎", "7️⃣", "🍀"]

def start_slot(call):
    uid = call.from_user.id
    s1, s2, s3 = [random.choice(SLOT_SYMBOLS) for _ in range(3)]

    if s1 == s2 == s3:
        if s1 == "💎":
            msg = "💎💎💎 <b>JACKPOT!</b> Siz g'alaba qozondingiz! 🎊"
            result = "win"
        else:
            msg = f"{s1}{s2}{s3} <b>TRIO!</b> Ajoyib! 🎉"
            result = "win"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        msg = f"{s1}{s2}{s3} — Bir juft! Yaxshi, lekin yetarli emas 😐"
        result = "draw"
    else:
        msg = f"{s1}{s2}{s3} — Omad yo'q bu safar 😞"
        result = "loss"

    record_result(uid, result)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 Yana aylantir", callback_data="game_slot"),
        types.InlineKeyboardButton("🏠 Menyu",         callback_data="main_menu"),
    )
    bot.edit_message_text(
        f"🎰 <b>Slot Mashina</b>\n\n┌───────────┐\n│  {s1}  {s2}  {s3}  │\n└───────────┘\n\n{msg}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

# ==========================================
# O'YIN 6: YASHIRIN SO'Z
# ==========================================
HIDDEN_WORDS = [
    ("python", "🐍 Dasturlash tili"),
    ("robot",  "🤖 Avtomatlashtirilgan mashina"),
    ("kitob",  "📚 O'qish uchun narsa"),
    ("gulzor", "🌸 Ko'p gul bo'lgan joy"),
    ("dengiz", "🌊 Katta suv havzasi"),
    ("uchqun", "✨ Olovdan chiqqan narsa"),
    ("bahor",  "🌱 Yilning bir fasli"),
    ("shahar", "🏙️ Ko'p odamlar yashaydigan joy"),
    ("yulduz", "⭐ Kechasi ko'rinadigan nur"),
    ("ovqat",  "🍽️ Taom"),
]

def start_word(call):
    uid = call.from_user.id
    word, hint = random.choice(HIDDEN_WORDS)
    hidden = "_ " * len(word)
    set_state(uid, {
        "game": "word", "word": word, "hint": hint,
        "guessed": [], "wrong": 0, "max_wrong": 6
    })
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💡 Maslahat", callback_data="word_hint"),
        types.InlineKeyboardButton("🏠 Menyu",    callback_data="main_menu"),
    )
    bot.edit_message_text(
        f"🐍 <b>Yashirin So'z</b>\n\n"
        f"Izoh: <i>{hint}</i>\n\n"
        f"So'z: <code>{hidden.strip()}</code>\n\n"
        f"Xato: 0/{6}\n\n"
        "Bitta harf yozing 👇",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

def handle_word_hint(call):
    uid = call.from_user.id
    state = get_state(uid)
    if not state or state.get("game") != "word":
        return
    hint = state.get("hint", "")
    bot.answer_callback_query(call.id, f"💡 Maslahat: {hint}", show_alert=True)

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("game") == "word")
def handle_word(message):
    uid = message.from_user.id
    state = get_state(uid)
    letter = message.text.strip().lower()

    if len(letter) != 1 or not letter.isalpha():
        bot.send_message(message.chat.id, "⚠️ Faqat bitta harf yozing!")
        return

    word = state["word"]
    guessed = state["guessed"]
    wrong = state["wrong"]
    max_wrong = state["max_wrong"]

    if letter in guessed:
        bot.send_message(message.chat.id, f"⚠️ '{letter}' harfini allaqachon sinab ko'rdingiz!")
        return

    guessed.append(letter)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💡 Maslahat", callback_data="word_hint"),
        types.InlineKeyboardButton("🏠 Menyu",    callback_data="main_menu"),
    )

    if letter in word:
        display = " ".join(c if c in guessed else "_" for c in word)
        if "_" not in display:
            record_result(uid, "win")
            clear_state(uid)
            bot.send_message(
                message.chat.id,
                f"🎉 <b>To'g'ri topdingiz!</b>\nSo'z: <b>{word.upper()}</b>",
                parse_mode="HTML", reply_markup=back_button()
            )
            return
        bot.send_message(
            message.chat.id,
            f"✅ '{letter.upper()}' bor!\n\nSo'z: <code>{display}</code>\n"
            f"Xato: {wrong}/{max_wrong}\nHarflar: {' '.join(guessed).upper()}",
            parse_mode="HTML", reply_markup=markup
        )
    else:
        state["wrong"] += 1
        wrong = state["wrong"]
        if wrong >= max_wrong:
            record_result(uid, "loss")
            clear_state(uid)
            bot.send_message(
                message.chat.id,
                f"😞 <b>Yutqazdingiz!</b>\nSo'z: <b>{word.upper()}</b>",
                parse_mode="HTML", reply_markup=back_button()
            )
            return
        display = " ".join(c if c in guessed else "_" for c in word)
        hangman = ["😀", "🙁", "😰", "😨", "😱", "💀", "☠️"]
        bot.send_message(
            message.chat.id,
            f"❌ '{letter.upper()}' yo'q! {hangman[wrong]}\n\nSo'z: <code>{display}</code>\n"
            f"Xato: {wrong}/{max_wrong}\nHarflar: {' '.join(guessed).upper()}",
            parse_mode="HTML", reply_markup=markup
        )

# ==========================================
# O'YIN 7: ZAR O'YINI
# ==========================================
def start_dice(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("1️⃣", callback_data="dice_1"),
        types.InlineKeyboardButton("2️⃣", callback_data="dice_2"),
        types.InlineKeyboardButton("3️⃣", callback_data="dice_3"),
        types.InlineKeyboardButton("4️⃣", callback_data="dice_4"),
        types.InlineKeyboardButton("5️⃣", callback_data="dice_5"),
        types.InlineKeyboardButton("6️⃣", callback_data="dice_6"),
    )
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    bot.edit_message_text(
        "🎲 <b>Zar O'yini</b>\n\nQaysi raqam tushishini taxmin qiling:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

def handle_dice(call):
    uid = call.from_user.id
    user_pick = int(call.data.split("_")[1])
    dice_result = random.randint(1, 6)
    dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 Qayta",  callback_data="game_dice"),
        types.InlineKeyboardButton("🏠 Menyu",  callback_data="main_menu"),
    )

    if user_pick == dice_result:
        record_result(uid, "win")
        msg = f"🎉 <b>To'g'ri!</b> Siz {dice_result} ni topdingiz!"
    else:
        record_result(uid, "loss")
        msg = f"😞 <b>Noto'g'ri!</b> Tushgan: {dice_result}"

    bot.edit_message_text(
        f"🎲 <b>Zar O'yini</b>\n\n"
        f"Sizning taxminingiz: {dice_faces[user_pick]}\n"
        f"Tushgan zar: {dice_faces[dice_result]}\n\n{msg}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

# ==========================================
# O'YIN 8: YUQORI KARTA
# ==========================================
CARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
CARD_SUITS = ["♠️", "♥️", "♦️", "♣️"]

def random_card():
    return random.choice(CARD_RANKS), random.choice(CARD_SUITS)

def card_value(rank):
    return CARD_RANKS.index(rank)

def start_card(call):
    uid = call.from_user.id
    rank, suit = random_card()
    set_state(uid, {"game": "card", "rank": rank, "suit": suit})

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⬆️ Yuqoriroq", callback_data="card_high"),
        types.InlineKeyboardButton("⬇️ Pastroq",   callback_data="card_low"),
    )
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    bot.edit_message_text(
        f"🃏 <b>Yuqori Karta</b>\n\n"
        f"Sizning kartangiz: <b>{rank}{suit}</b>\n\n"
        "Keyingi karta yuqoriroq yoki pastroq bo'ladi?",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

def handle_card(call):
    uid = call.from_user.id
    state = get_state(uid)
    if not state or state.get("game") != "card":
        return

    old_rank = state["rank"]
    old_suit = state["suit"]
    new_rank, new_suit = random_card()
    prediction = call.data.split("_")[1]

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 Qayta", callback_data="game_card"),
        types.InlineKeyboardButton("🏠 Menyu", callback_data="main_menu"),
    )

    old_val = card_value(old_rank)
    new_val = card_value(new_rank)

    if new_val == old_val:
        record_result(uid, "draw")
        msg = f"🤝 <b>Durrang!</b> Ikkala karta ham {new_rank}"
    elif (prediction == "high" and new_val > old_val) or (prediction == "low" and new_val < old_val):
        record_result(uid, "win")
        msg = "🎉 <b>To'g'ri taxmin!</b>"
    else:
        record_result(uid, "loss")
        msg = "😞 <b>Noto'g'ri taxmin!</b>"

    clear_state(uid)
    bot.edit_message_text(
        f"🃏 <b>Yuqori Karta</b>\n\n"
        f"Avvalgi karta: {old_rank}{old_suit}\n"
        f"Yangi karta:   <b>{new_rank}{new_suit}</b>\n\n{msg}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

# ==========================================
# O'YIN 9: ANAGRAM
# ==========================================
ANAGRAM_WORDS = [
    "python", "robot", "kitob", "muzey", "bahor",
    "samolyot", "shahar", "maktab", "kompyuter", "telefon"
]

def shuffle_word(word):
    lst = list(word)
    shuffled = lst[:]
    while shuffled == lst:
        random.shuffle(shuffled)
    return "".join(shuffled)

def start_anagram(call):
    uid = call.from_user.id
    word = random.choice(ANAGRAM_WORDS)
    anagram = shuffle_word(word)
    set_state(uid, {"game": "anagram", "word": word, "anagram": anagram})
    bot.edit_message_text(
        f"🔤 <b>Anagram</b>\n\n"
        f"Quyidagi harflarni to'g'ri tartibga soling:\n\n"
        f"<code>{anagram.upper()}</code>\n\n"
        "Javobni yozing 👇",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=back_button()
    )

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("game") == "anagram")
def handle_anagram(message):
    uid = message.from_user.id
    state = get_state(uid)
    user_ans = message.text.strip().lower()
    word = state["word"]

    clear_state(uid)
    if user_ans == word:
        record_result(uid, "win")
        bot.send_message(
            message.chat.id,
            f"🎉 <b>To'g'ri!</b> So'z: <b>{word.upper()}</b>",
            parse_mode="HTML", reply_markup=back_button()
        )
    else:
        record_result(uid, "loss")
        bot.send_message(
            message.chat.id,
            f"❌ <b>Noto'g'ri!</b>\nTo'g'ri so'z: <b>{word.upper()}</b>",
            parse_mode="HTML", reply_markup=back_button()
        )

# ==========================================
# O'YIN 10: OMAD G'ILDIRAGI
# ==========================================
WHEEL_PRIZES = [
    ("🏆 Katta g'alaba!", "win"),
    ("💰 Yaxshi natija!", "win"),
    ("⭐ Baxtli yulduz!", "win"),
    ("😐 Durrang...",     "draw"),
    ("😞 Omad yo'q",     "loss"),
    ("💔 Yutqazdingiz",  "loss"),
]

def start_wheel(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎡 G'ildirakni aylantiir!", callback_data="wheel_spin"))
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    bot.edit_message_text(
        "🎡 <b>Omad G'ildiragi</b>\n\n"
        "G'ildirakni aylantirib baxtingizni sinab ko'ring!\n\n"
        "🏆 Katta g'alaba\n💰 Yaxshi natija\n⭐ Baxtli yulduz\n"
        "😐 Durrang\n😞 Omad yo'q\n💔 Yutqazish",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

def handle_wheel_spin(call):
    uid = call.from_user.id
    prize_text, result = random.choice(WHEEL_PRIZES)
    record_result(uid, result)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 Yana",   callback_data="game_wheel"),
        types.InlineKeyboardButton("🏠 Menyu",  callback_data="main_menu"),
    )
    bot.edit_message_text(
        f"🎡 <b>Omad G'ildiragi</b>\n\n"
        f"🎊 Natija: <b>{prize_text}</b>",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )

# ==========================================
# STATISTIKA
# ==========================================
def show_stats(call):
    uid = call.from_user.id
    s = user_scores[uid]
    total = s["total_games"]
    if total == 0:
        text = "📊 <b>Natijalaringiz</b>\n\nHali hech qanday o'yin o'ynamadingiz!"
    else:
        win_rate = round(s["wins"] / total * 100)
        text = (
            f"📊 <b>Sizning Natijalaringiz</b>\n\n"
            f"🎮 Jami o'yinlar: <b>{total}</b>\n"
            f"🏆 G'alabalar:    <b>{s['wins']}</b>\n"
            f"😞 Mag'lubiyat:   <b>{s['losses']}</b>\n"
            f"🤝 Durranglar:    <b>{s['draws']}</b>\n\n"
            f"📈 G'alaba foizi: <b>{win_rate}%</b>"
        )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="HTML", reply_markup=markup)

# ==========================================
# UMUMIY MATN XABARLARI (o'yin tanlanganda)
# ==========================================
@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("game") is None)
def unknown_message(message):
    bot.send_message(
        message.chat.id,
        "🎮 O'yin tanlash uchun /start yozing yoki tugmalardan foydalaning:",
        reply_markup=main_menu()
    )

# ==========================================
# BOTNI ISHGA TUSHIRISH
# ==========================================
if __name__ == "__main__":
    print("✅ O'yinlar boti ishga tushdi!")
    print("Botni to'xtatish uchun Ctrl+C bosing.")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
