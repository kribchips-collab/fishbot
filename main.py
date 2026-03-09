import asyncio
import random
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.types import FSInputFile
from database import Database

# --- НАСТРОЙКИ ---
TOKEN = "8697429668:AAFt0n_JXHLaTdTKlc8GTef4ljRugakth0U"
DB_PATH = "/app/data/fishing.db"

try:
    os.makedirs("/app/data", exist_ok=True)
except Exception:
    pass 

db = Database(DB_PATH)

# --- АВТО-ОБНОВЛЕНИЕ БАЗЫ ДЛЯ КЛАНОВ ---
# Это магия, чтобы не трогать твой database.py!
with db.connection:
    db.cursor.execute("CREATE TABLE IF NOT EXISTS clans (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, owner_id INTEGER)")
    try:
        db.cursor.execute("ALTER TABLE users ADD COLUMN clan_id INTEGER")
    except:
        pass # Если колонка уже есть, питон просто пойдет дальше

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")

# ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ КРАБОВ
CRABS_END_TIME = None

# --- ДАННЫЕ ---
FISH_DATA = {
    "radioactive": {"name": "Радиоактивная рыба", "weight": (0.5, 2.0), "loc": "Яма с радиацией", "bait": "Радиоактивный червь", "img": "rad_fish.png"},
    "rotten": {"name": "Гнилой Чёрт", "weight": (1.0, 2.3), "loc": "Яма с радиацией", "bait": "Гниль", "img": "flash.fish.png"},
    "blind": {"name": "Слепая Рыба", "weight": (0.7, 3.0), "loc": "Лаборатория", "bait": "Линза", "img": "blind_fish.png"},
    "spider": {"name": "Рыба-Паук", "weight": (0.2, 0.8), "loc": "Пещера", "bait": "Мясо монстра", "img": "spider_fish.png"},
    "beaver": {"name": "Бобрыба", "weight": (2.0, 4.2), "loc": "Деревня", "bait": "Кусок дерева", "img": "bober.png"},
    "copper": {"name": "Медная рыба", "weight": (3.0, 4.0), "loc": "Деревня", "bait": "Медный кусочек", "img": "copper_fish.png"},
    "honey": {"name": "Медовая рыба", "weight": (1.3, 2.2), "loc": "Лаборатория", "bait": "Баночка мёда", "img": "honey_fish.png"},
    "fluffy": {"name": "Пушистая рыба", "weight": (1.0, 2.0), "loc": "Лаборатория", "bait": "Кошачий корм", "img": "fluffy_fish.png"},
    "amethyst": {"name": "Аметистовый карп", "weight": (2.0, 2.5), "loc": "Пещера", "bait": "Осколок трезубца", "img": "amethyst_fish.png"},
    "troll": {"name": "Рыба-тролль", "weight": (0.1, 8.0), "loc": "Деревня", "bait": "Кусок дерева", "img": "troll_fish.png"},
    "shark": {"name": "Полная акула", "weight": (3.0, 5.0), "loc": "Океан", "bait": "Стандартная", "img": "shark.png"},
    "super_fluffy": {"name": "🐱СВЕРХ-ПУШИСТАЯ РЫБА", "weight": (3.0, 5.0), "loc": "Спец", "bait": None, "img": "super_fluffy.png"},
    "irinalegend": {"name": "🪼 МЕДУЗА ИРИНА", "weight": (20.0, 30.0), "loc": "Везде", "bait": None, "img": "irina.png"},
    "key_fish": {"name": "Рыба-ключ", "weight": (0.1, 0.1), "price": 1, "img": "key.png"},
    "magic_cube": {"name": "Кубик-фугу", "weight": (0.5, 0.5), "price": 1, "img": "cube.png"},
}

ALMANAC_TEXT = """
☢️1. Радиоактивная рыба (вес 0.5 - 2 кг)
🥩2. Гнилой Чёрт (вес 1 - 2.3 кг)
🦯3. Слепая Рыба (вес 0.7 - 3 кг)
🕷4. Рыба-Паук (вес 0.2 - 0.8 кг)
🦫5. Бобрыба (вес 2 - 4.2 кг)
🥉6. Медная рыба (вес 3 - 4 кг)
🍯7. Медовая рыба (вес 1.3 - 2.2 кг)
🐱8. Пушистая рыба (вес 1 - 2 кг)
💎9. Аметистовый карп (вес 2 - 2.5 кг)
🤡10. Рыба-тролль (вес 0.1 - 8 кг)
🦈11. Полная акула (вес 3 - 5 кг)

—-📌Локации:—-
Шанс 70% поймать профильную рыбу:
☢️Яма с радиацией: радиоактивная рыба, Гнилой Чёрт
🧪Лаборатория: медовая, пушистая, слепая рыба
⛏️Пещера: аметистовый карп, рыба-паук
🏘Деревня: бобрыба, рыба-тролль, медная рыба
🌊Океан: все виды рыб (абсолютный рандом)

—-🎣Наживки:—-
⭐️Стандартная (без эффектов, бесплатная)
Остальные наживки стоят по 10💰 и дают +50% шанс к поимке конкретной рыбы.
"""

LOCATIONS = {"Яма с радиацией": "☢️ Яма", "Лаборатория": "🧪 Лаборатория", "Пещера": "🕸 Пещера", "Деревня": "🏘 Деревня", "Океан": "🌊 Океан"}
BAITS = {"Гниль": 10, "Мясо монстра": 10, "Радиоактивный червь": 10, "Кусок дерева": 10, "Баночка мёда": 10, "Кошачий корм": 10, "Осколок трезубца": 10, "Медный кусочек": 10, "Линза": 10, "Магнит": 50}

FISH_MODS = [
    {"p": "🌶️ Перцеподобный", "m": 0.1, "w": 1},
    {"p": "🪵 Деревянный", "m": 1.5, "w": 12},
    {"p": "🐢 Вялый", "m": 0.5, "w": 15},
    {"p": "🤢 Гнилой", "m": 0.7, "w": 15},
    {"p": "", "m": 1.0, "w": 40},
    {"p": "🔹 Бодрый", "m": 1.3, "w": 15},
    {"p": "🔸 Сильный", "m": 1.8, "w": 10},
    {"p": "👑 Золотой", "m": 2.5, "w": 5}
]

# --- КЛАВИАТУРЫ ---
def main_menu(balance=0):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🎣 Закинуть", callback_data="throw"), types.InlineKeyboardButton(text="🎒 Инвент", callback_data="inv"))
    kb.row(types.InlineKeyboardButton(text="🗺️ Локации", callback_data="loc"), types.InlineKeyboardButton(text="🧪 Наживка", callback_data="bait_menu"))
    # Заменили Сетку на Крабов!
    kb.row(types.InlineKeyboardButton(text="📖 Альманах", callback_data="almanac"), types.InlineKeyboardButton(text="🦀 Крабы (100 💰)", callback_data="crabs_call"))
    kb.row(types.InlineKeyboardButton(text="🏆 Топ", callback_data="top"), types.InlineKeyboardButton(text=f"💰 {round(balance, 1)}", callback_data="stats"))
    kb.row(types.InlineKeyboardButton(text="📦 Ящики", callback_data="boxes_menu"))
    return kb.as_markup()

# --- ФУНКЦИЯ ДЛЯ ПРОВЕРКИ КРАБОВ ---
def check_crabs():
    global CRABS_END_TIME
    if CRABS_END_TIME and datetime.now() < CRABS_END_TIME:
        wait = CRABS_END_TIME - datetime.now()
        mins = wait.seconds // 60
        secs = wait.seconds % 60
        return f"Ваша ЛЕСКА🎣 словно 🦀ПРИКЛЕЕНА🦀🦀К🧶КАТУШКЕ🧶🧶\nосталось: {mins} мин. {secs} сек."
    return None

# --- ОСНОВНЫЕ КОМАНДЫ ---
@dp.message(Command("start"))
@dp.message(F.text.lower().in_(["меню", "рыбменю", "старт"]))
async def start(msg: types.Message):
    db.register_user(msg.from_user.id, msg.from_user.first_name)
    user = db.get_user(msg.from_user.id)
    bal = round(user[2], 1)
    await msg.answer(f"Мир МС огромен... Твой баланс: <b>{bal}</b> 💰", reply_markup=main_menu(bal))

@dp.message(F.text.lower().in_(["фиш", "fish", "закинуть"]))
async def qol_throw(msg: types.Message):
    crab_msg = check_crabs()
    if crab_msg:
        return await msg.answer(crab_msg)

    class FakeCall:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
            self.data = "throw"
        async def answer(self, text=None, show_alert=False):
            if text: await self.message.answer(text)
    await handle_callbacks(FakeCall(msg))

@dp.message(F.text.lower().in_(["инв", "inv", "инвентарь"]))
async def qol_inv(msg: types.Message):
    inv = db.get_inventory(msg.from_user.id)
    text = f"🎒 Инвентарь <b>{msg.from_user.first_name}</b>:\n" + "\n".join([f"• {n} x{c} ({round(p, 1)}💰)" for n, c, p in inv])
    kb = InlineKeyboardBuilder().button(text="💰 Продать всё", callback_data="sell_all")
    await msg.answer(text if inv else "🎒 В инвентаре пусто...", reply_markup=kb.as_markup())

@dp.message(F.text.lower().in_(["сетка", "net", "сетку", "секта"]))
async def use_grid(msg: types.Message):
    uid = msg.from_user.id
    user = db.get_user(uid) # Проверь, чтобы база возвращала данные
    if not user: return
    
    now = datetime.now()
    is_sect = msg.text.lower() == "секта"
    
    # Проверка КД (5 часов). Предполагаем, что время в базе в 7-м столбце (индекс 6)
    if len(user) > 6 and user[6]:
        last_grid = datetime.fromisoformat(user[6])
        if now < last_grid + timedelta(hours=5):
            wait = (last_grid + timedelta(hours=5) - now)
            h, m = wait.seconds // 3600, (wait.seconds // 60) % 60
            if is_sect:
                return await msg.answer(f"⌛ <b>Духи Бездны еще не восстановили силы.</b>\nПриходи через <b>{h}ч. {m}мин.</b>")
            else:
                return await msg.answer(f"⏳ Сетка запуталась! Приходи через <b>{h}ч. {m}мин.</b>")

    total_money, catch_lines = 0, []
    # Список ключей рыб без редких/квестовых
    possible_keys = [k for k in FISH_DATA.keys() if k not in ["irinalegend", "super_fluffy", "key_fish", "magic_cube"]]

    for _ in range(15):
        f_key = random.choice(possible_keys)
        fish = FISH_DATA[f_key]
        mod = random.choices(FISH_MODS, weights=[m["w"] for m in FISH_MODS])[0]
        final_name = f"{mod['p'] + ' ' if mod['p'] else ''}{fish['name']}".strip()
        # Считаем вес и цену (как в твоем тесте: вес * 5)
        w = round(random.uniform(fish["weight"][0], fish["weight"][1]) * mod['m'], 2)
        p = round(w * 5, 1)
        db.add_fish(uid, final_name, p)
        catch_lines.append(f"• {final_name} ({p} 💰)")
        total_money += p

    # Записываем время использования в базу
    with db.connection:
        db.cursor.execute("UPDATE users SET last_grid_time = ? WHERE user_id = ?", (now.isoformat(), uid))
        
    # Разделение вывода: лорная секта или обычная сетка
    if is_sect:
        ritual = await msg.answer("💠 <b>Обряд Секты начинается...</b>\n\n🏮 Вы зажигаете глубоководные свечи и взываете к Великому Ктулху...")
        await asyncio.sleep(3)
        
        await ritual.edit_text("🌀 <b>Мистические воды бурлят...</b>\n\n🌊 Сети наполняются эссенцией Бездны. Крабы в ужасе бегут с этого берега!")
        await asyncio.sleep(3)

        await ritual.edit_text(
            f"🔱 <b>Обряд завершен!</b> Бездна даровала <b>{msg.from_user.first_name}</b> щедрый дар:\n\n" 
            + "\n".join(catch_lines) + 
            f"\n\n<b>✨ Социальный профит: {round(total_money, 1)} 💰</b>"
        )
    else:
        await msg.answer(f"🕸️ <b>Сетка!</b> {msg.from_user.first_name} вытащил:\n\n" + "\n".join(catch_lines) + f"\n\n<b>ИТОГО: {round(total_money, 1)} 💰</b>")

# --- СИСТЕМА КЛАНОВ ---
@dp.message(F.text.lower().startswith("создать "))
async def create_clan(msg: types.Message):
    clan_name = msg.text[8:].strip()
    uid = msg.from_user.id
    user = db.get_user(uid)
    if user[2] < 150:
        return await msg.answer("❌ Нужно 150💰 для создания клана!")
    
    with db.connection:
        cur = db.cursor.execute("SELECT clan_id FROM users WHERE user_id = ?", (uid,)).fetchone()
        if cur and cur[0]:
            return await msg.answer("❌ Ты уже состоишь в клане!")
        
        exist = db.cursor.execute("SELECT id FROM clans WHERE name = ?", (clan_name,)).fetchone()
        if exist: return await msg.answer("❌ Такое название уже занято!")
        
        db.cursor.execute("UPDATE users SET balance = balance - 150 WHERE user_id = ?", (uid,))
        db.cursor.execute("INSERT INTO clans (name, owner_id) VALUES (?, ?)", (clan_name, uid))
        clan_id = db.cursor.lastrowid
        db.cursor.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan_id, uid))
        
    await msg.answer(f"🛡️ Клан <b>{clan_name}</b> успешно создан за 150💰!")

@dp.message(F.text.lower() == "пригласить")
async def invite_clan(msg: types.Message):
    if not msg.reply_to_message: return await msg.answer("⚠️ Ответь на сообщение того, кого хочешь пригласить!")
    uid = msg.from_user.id
    target_id = msg.reply_to_message.from_user.id
    
    with db.connection:
        clan = db.cursor.execute("SELECT id, name FROM clans WHERE owner_id = ?", (uid,)).fetchone()
        if not clan: return await msg.answer("❌ Ты не глава клана!")
        
        t_user = db.cursor.execute("SELECT clan_id FROM users WHERE user_id = ?", (target_id,)).fetchone()
        if t_user and t_user[0]: return await msg.answer("❌ Этот игрок уже состоит в клане!")
        
        db.cursor.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan[0], target_id))
        
    await msg.answer(f"🤝 <b>{msg.reply_to_message.from_user.first_name}</b> вступил в клан <b>{clan[1]}</b>!")

@dp.message(F.text.lower() == "выгнать")
async def kick_clan(msg: types.Message):
    if not msg.reply_to_message: return await msg.answer("⚠️ Ответь на сообщение игрока!")
    uid = msg.from_user.id
    target_id = msg.reply_to_message.from_user.id
    if uid == target_id: return await msg.answer("❌ Себя выгнать нельзя!")
    
    with db.connection:
        clan = db.cursor.execute("SELECT id FROM clans WHERE owner_id = ?", (uid,)).fetchone()
        if not clan: return await msg.answer("❌ Ты не глава клана!")
        
        t_user = db.cursor.execute("SELECT clan_id FROM users WHERE user_id = ?", (target_id,)).fetchone()
        if not t_user or t_user[0] != clan[0]: return await msg.answer("❌ Этот игрок не в твоем клане!")
        
        db.cursor.execute("UPDATE users SET clan_id = NULL WHERE user_id = ?", (target_id,))
        
    await msg.answer(f"🥾 Игрок <b>{msg.reply_to_message.from_user.first_name}</b> изгнан из клана!")

# --- СОЦИАЛЬНЫЕ КОМАНДЫ (ПЕРЕВОДЫ) ---
@dp.message(F.text.lower().startswith("добавить"))
async def add_to_collection_cmd(msg: types.Message):
    fish_name = msg.text[9:].strip() 
    if not fish_name: return await msg.answer("⚠️ Напиши: <b>добавить [название рыбы]</b>")
    
    if db.move_to_collection(msg.from_user.id, fish_name):
        await msg.answer(f"📦 Рыба <b>{fish_name}</b> убрана в коллекцию!")
    else:
        await msg.answer(f"❌ Не нашел «{fish_name}». Проверь название в инвентаре (копируй точно с эмодзи!).")

@dp.message(F.text.lower().startswith("убрать"))
async def remove_from_collection_cmd(msg: types.Message):
    fish_name = msg.text[7:].strip()
    if not fish_name: return await msg.answer("⚠️ Напиши: <b>убрать [название рыбы]</b>")
    
    if db.remove_from_collection(msg.from_user.id, fish_name):
        await msg.answer(f"🎒 Рыба <b>{fish_name}</b> вернулась в инвентарь.")
    else:
        await msg.answer(f"❌ В коллекции нет рыбы «{fish_name}»")

@dp.message(F.text.lower().startswith("переброс"))
async def reroll_cmd(msg: types.Message):
    uid = msg.from_user.id
    fish_name = msg.text[9:].strip()
    
    if not fish_name: 
        return await msg.answer("⚠️ Напиши: <b>переброс [название рыбы]</b>")

    inv = db.get_inventory(uid)
    has_cube = any(item[0] == "Кубик-фугу" for item in inv)
    has_fish = any(item[0].lower() == fish_name.lower() for item in inv)

    if not has_cube: return await msg.answer("❌ У тебя нет <b>Кубика-фугу</b>!")
    if not has_fish: return await msg.answer(f"❌ У тебя нет рыбы <b>{fish_name}</b>!")

    current_fish = next(item for item in inv if item[0].lower() == fish_name.lower())
    
    with db.connection:
        db.cursor.execute("UPDATE inventory SET count = count - 1 WHERE user_id = ? AND fish_name = 'Кубик-фугу'", (uid,))
        db.cursor.execute("DELETE FROM inventory WHERE count <= 0")
        db.cursor.execute("DELETE FROM inventory WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", (uid, fish_name))

    new_mod = random.choices(FISH_MODS, weights=[m["w"] for m in FISH_MODS])[0]
    
    pure_name = fish_name
    for m in FISH_MODS:
        if m['p'] and fish_name.startswith(m['p']):
            pure_name = fish_name.replace(m['p'], "").strip()
            break
            
    final_name = f"{new_mod['p']} {pure_name}".strip()
    new_price = round(current_fish[2] * new_mod['m'], 1)
    
    db.add_fish(uid, final_name, new_price)
    await msg.answer(f"🎲 <b>Кубик-фугу активирован!</b>\nТеперь у тебя: <b>{final_name}</b>")
        
@dp.message(F.text.lower().startswith("передать"))
async def transfer_money(msg: types.Message):
    if not msg.reply_to_message:
        return await msg.answer("⚠️ Ответь на сообщение того, кому хочешь передать деньги!")
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return await msg.answer("⚠️ Напиши: <b>передать [сумма]</b>")
    
    amount = int(parts[1])
    sid, rid = msg.from_user.id, msg.reply_to_message.from_user.id
    if sid == rid: return await msg.answer("🤔 Себе нельзя.")
    
    user = db.get_user(sid)
    if user[2] < amount: return await msg.answer("❌ Нет денег!")
    
    with db.connection:
        db.cursor.execute("UPDATE users SET balance = ROUND(balance - ?, 1) WHERE user_id = ?", (amount, sid))
        db.cursor.execute("UPDATE users SET balance = ROUND(balance + ?, 1) WHERE user_id = ?", (amount, rid))
    await msg.answer(f"💸 <b>{msg.from_user.first_name}</b> передал {amount} 💰 игроку {msg.reply_to_message.from_user.first_name}")

@dp.message(F.text.lower().startswith("отдать"))
async def give_fish(msg: types.Message):
    if not msg.reply_to_message: return await msg.answer("⚠️ Ответь на сообщение друга!")
    
    raw_text = msg.text[7:].strip()
    fish_name = raw_text.split(" x")[0].split(" (")[0].strip()
    sid, rid = msg.from_user.id, msg.reply_to_message.from_user.id

    with db.connection:
        res = db.cursor.execute("SELECT count, total_price FROM inventory WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", (sid, fish_name)).fetchone()
        if not res or res[0] <= 0: return await msg.answer(f"❌ У тебя нет рыбы «{fish_name}»")

        price_one = res[1] / res[0]
        if res[0] > 1:
            db.cursor.execute("UPDATE inventory SET count = count - 1, total_price = ROUND(total_price - ?, 1) WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", (price_one, sid, fish_name))
        else:
            db.cursor.execute("DELETE FROM inventory WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", (sid, fish_name))
        db.add_fish(rid, fish_name, price_one)
    await msg.answer(f"🎁 <b>{msg.from_user.first_name}</b> отдал 🐟 <b>{fish_name}</b> игроку {msg.reply_to_message.from_user.first_name}")

@dp.message(Command("testfish"))
async def test_fish(msg: types.Message):
    f_key = random.choice(list(FISH_DATA.keys()))
    fish = FISH_DATA[f_key]
    mod = random.choices(FISH_MODS, weights=[m["w"] for m in FISH_MODS])[0]
    final_name = f"{mod['p'] + ' ' if mod['p'] else ''}{fish['name']}"
    w = round(random.uniform(fish["weight"][0], fish["weight"][1]) * mod['m'], 2)
    p = round(w * 5, 1)
    await msg.answer(f"🧪 <b>ТЕСТ</b>\n🐟 {final_name} ({w} кг)\n💰 Цена: {p}\n⚠️ В инвент не идет.")

# --- ОБРАБОТКА КНОПОК ---
@dp.callback_query()
async def handle_callbacks(call: types.CallbackQuery):
    global CRABS_END_TIME
    uid = call.from_user.id
    user = db.get_user(uid)
    now = datetime.now()

    if call.data == "throw":
        crab_msg = check_crabs()
        if crab_msg:
            return await call.answer(crab_msg, show_alert=True)

        if user[5]:
            last_time = datetime.fromisoformat(user[5])
            if now < last_time + timedelta(minutes=10):
                wait = (last_time + timedelta(minutes=10) - now).seconds // 60
                return await call.answer(f"⏳ Жди {wait+1} мин.", show_alert=True)

        current_loc, current_bait = user[3], user[4]
        
        key_chance = 0.05
        if current_bait == "Магнит": key_chance += 0.15
        
        roll = random.random()
        
        if roll < key_chance:
            fish_key = "key_fish"
            mod = {"p": "", "m": 1.0}
        elif roll < key_chance + 0.02:
            fish_key = "magic_cube"
            mod = {"p": "", "m": 1.0}
        else:
            LOC_POOLS = {
                "Яма с радиацией": ["radioactive", "rotten"], 
                "Лаборатория": ["blind", "honey", "fluffy"], 
                "Пещера": ["spider", "amethyst"], 
                "Деревня": ["beaver", "copper", "troll"], 
                "Океан": [k for k in FISH_DATA.keys() if k not in ["irinalegend", "super_fluffy", "key_fish", "magic_cube"]]
            }
            
            if random.random() < 0.005: 
                fish_key = "irinalegend"
            else:
                target = [k for k, v in FISH_DATA.items() if v.get("bait") == current_bait]
                if target and random.random() < 0.5: 
                    fish_key = random.choice(target)
                elif current_loc in LOC_POOLS and random.random() < 0.8: 
                    fish_key = random.choice(LOC_POOLS[current_loc])
                else: 
                    fish_key = random.choice(LOC_POOLS["Океан"])

            if fish_key == "fluffy" and random.random() < 0.03: 
                fish_key = "super_fluffy"
            
            mod = random.choices(FISH_MODS, weights=[m["w"] for m in FISH_MODS])[0]

        fish = FISH_DATA[fish_key]
        final_name = f"{mod['p'] + ' ' if mod['p'] else ''}{fish['name']}".strip()
        weight = round(random.uniform(fish["weight"][0], fish["weight"][1]) * mod['m'], 2)
        
        price = round(weight * 5, 1) if "price" not in fish else fish["price"]

        db.add_fish(uid, final_name, price)
        with db.connection:
            db.cursor.execute("UPDATE users SET bait = 'Нет', last_fish_time = ? WHERE user_id = ?", (now.isoformat(), uid))

        img_path = os.path.join(IMG_DIR, fish["img"])
        if os.path.exists(img_path): 
            await call.message.answer_sticker(sticker=FSInputFile(img_path))
        
        await call.message.answer(f"🎣<b>{call.from_user.first_name}</b> вытащил <b>{final_name}</b> ({weight} кг)\n💰 Цена: {price}", reply_markup=main_menu(user[2]))

    elif call.data == "crabs_call":
        if user[2] < 100:
            return await call.answer("❌ У тебя нет 100 💰 для призыва крабов!", show_alert=True)
        
        with db.connection:
            db.cursor.execute("UPDATE users SET balance = balance - 100 WHERE user_id = ?", (uid,))
            
        CRABS_END_TIME = datetime.now() + timedelta(hours=1)
        meme_text = f"По воле <b>{call.from_user.first_name}</b> ЧАТ💬💬захватывают 🦀крабы🦀🦀... ваши🫵🫵 УДОЧКИ🎏🎏 сматываются🎣🎣🎣🫧🛀\nИз-за ВЛИ🦀ЯНИЯ 🦀🦀КРАБОВ🦀 🎣🎣рыбачить🎣🎣🎣 не будет 🌶️🌶️НИКТО🌶️на протяжении ⌚⌚ЧАСА⏰⏰⏰"
        await call.message.answer(meme_text)
        
        new_u = db.get_user(uid)
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{round(new_u[2], 1)}</b> 💰", reply_markup=main_menu(new_u[2]))

    elif call.data == "boxes_menu":
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="📦 Обычный (1 🔑)", callback_data="buychest_common"))
        kb.row(types.InlineKeyboardButton(text="🔹📦 Бодрый (3 🔑)", callback_data="buychest_cheerful"))
        kb.row(types.InlineKeyboardButton(text="🪵📦 Деревянный (5 🔑)", callback_data="buychest_wooden"))
        kb.row(types.InlineKeyboardButton(text="🔸📦 Сильный (7 🔑)", callback_data="buychest_strong"))
        kb.row(types.InlineKeyboardButton(text="👑📦 Золотой (15 🔑)", callback_data="buychest_gold"))
        kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text("🎁 <b>Магазин ящиков</b>\nОбменяй 🔑 на редкую рыбу!", reply_markup=kb.as_markup())
        
    elif call.data.startswith("buychest_"):
        chest_type = call.data.split("_")[1]
        
        costs = {
            "common": 1, 
            "cheerful": 3, 
            "wooden": 5,   
            "strong": 7, 
            "gold": 15
        }
        target_mods = {
            "common": "", 
            "cheerful": "🔹 Бодрый", 
            "wooden": "🪵 Деревянный", 
            "strong": "🔸 Сильный", 
            "gold": "👑 Золотой"
        }
        
        cost = costs[chest_type]
        inv = db.get_inventory(uid)
        
        key_count = 0
        for item in inv:
            if "Рыба-ключ" in item[0]:
                key_count = item[1]
                break

        if key_count < cost:
            return await call.answer(f"❌ Нужно {cost} ключей! У тебя: {key_count}", show_alert=True)

        with db.connection:
            db.cursor.execute(
                "UPDATE inventory SET count = count - ? WHERE user_id = ? AND fish_name = 'Рыба-ключ'", 
                (cost, uid)
            )
            db.cursor.execute("DELETE FROM inventory WHERE count <= 0")

        f_key = random.choice([k for k in FISH_DATA.keys() if k not in ["key_fish", "magic_cube", "irinalegend", "super_fluffy"]])
        fish = FISH_DATA[f_key]
        
        prefix = target_mods[chest_type]
        final_name = f"{prefix} {fish['name']}".strip()
        
        price = round(random.uniform(fish["weight"][0], fish["weight"][1]) * 10, 1) 
        
        db.add_fish(uid, final_name, price)
        await call.message.answer(f"🎊 Из ящика выпрыгнула: <b>{final_name}</b>!")

    elif call.data == "almanac":
        kb = InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="back")
        await call.message.edit_text(ALMANAC_TEXT, reply_markup=kb.as_markup())

    elif call.data == "bait_menu":
        kb = InlineKeyboardBuilder()
        for b_name, p in BAITS.items(): kb.button(text=f"{b_name} ({p}💰)", callback_data=f"buy_{b_name}")
        kb.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text(f"🧪 Наживка: <b>{user[4]}</b>", reply_markup=kb.as_markup())

    elif call.data.startswith("buy_"):
        b_name = call.data.split("_")[1]
        p = BAITS.get(b_name, 10)
        if user[2] >= p:
            with db.connection: db.cursor.execute("UPDATE users SET balance = ROUND(balance - ?, 1), bait = ? WHERE user_id = ?", (p, b_name, uid))
            await call.answer(f"✅ Куплено: {b_name}")
            new_u = db.get_user(uid)
            await call.message.edit_text(f"🧪 Наживка: <b>{new_u[4]}</b>", reply_markup=call.message.reply_markup)
        else: await call.answer("❌ Нет денег!", show_alert=True)

    elif call.data == "inv":
        inv = db.get_inventory(uid)
        text = f"🎒 <b>Инвентарь:</b>\n"
        if inv:
            text += "\n".join([f"• {n} x{c} ({round(p, 1)}💰)" for n, c, p in inv])
        else:
            text += "Пусто..."

        kb = InlineKeyboardBuilder()
        kb.button(text="💰 Продать всё", callback_data="sell_all")
        kb.button(text="🖼 Коллекция", callback_data="view_coll")
        kb.button(text="⬅️ Назад", callback_data="back")
        kb.adjust(2, 1)
        
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    elif call.data == "view_coll":
        coll = db.get_collection(uid)
        text = f"🖼 <b>Твоя коллекция рыб:</b>\n\n"
        if coll:
            text += "\n".join([f"• {n} x{c} ({round(p, 1)}💰)" for n, c, p in coll])
            text += "\n\n<i>Чтобы забрать рыбу, напиши: убрать [название]</i>"
        else:
            text += "Тут пока ничего нет. Используй команду <b>добавить [название]</b>, чтобы сохранить редкую рыбу!"

        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад в инвентарь", callback_data="inv")
        
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    elif call.data == "top":
        # Получаем данные из базы
        top_players = db.get_top_players()
        top_clans = db.get_top_clans()

        text = "🏆 <b>ТОП РЫБОЛОВОВ:</b>\n"
        if not top_players:
            text += "<i>Список пуст...</i>\n"
        else:
            for i, (name, balance, inv_val, coll_val) in enumerate(top_players, 1):
                liquid = round(balance + inv_val, 1)
                total = round(balance + inv_val + coll_val, 1)
                text += f"{i}. <b>{name}</b> — {liquid}💰 (всего: {total})\n"

        text += "\n🛡 <b>ТОП 10 КЛАНОВ:</b>\n"
        if not top_clans:
            text += "<i>Кланов пока нет...</i>"
        else:
            for i, (clan_name, wealth) in enumerate(top_clans, 1):
                text += f"{i}. <b>{clan_name}</b> — {round(wealth, 1)} 💰\n"

        kb = InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="back")
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    elif call.data == "loc":
        kb = InlineKeyboardBuilder()
        for k, v in LOCATIONS.items(): kb.button(text=v, callback_data=f"setloc_{k}")
        kb.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text(f"🗺 Локация: <b>{user[3]}</b>", reply_markup=kb.as_markup())

    elif call.data.startswith("setloc_"):
        new_l = call.data.split("_")[1]
        with db.connection: db.cursor.execute("UPDATE users SET location = ? WHERE user_id = ?", (new_l, uid))
        await call.answer(f"В {new_l}!")
        new_u = db.get_user(uid)
        await call.message.edit_text(f"Баланс: <b>{round(new_u[2], 1)}</b> 💰", reply_markup=main_menu(new_u[2]))

    elif call.data == "sell_all":
        e = db.sell_all(uid)
        await call.answer(f"✅ +{e} 💰")
        new_u = db.get_user(uid)
        await call.message.edit_text(f"Баланс: <b>{round(new_u[2], 1)}</b> 💰", reply_markup=main_menu(new_u[2]))

    elif call.data == "back":
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{round(user[2], 1)}</b> 💰", reply_markup=main_menu(user[2]))

    elif call.data == "stats":
        pass 

    await call.answer()

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")



