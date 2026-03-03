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

TOKEN = "8697429668:AAFt0n_JXHLaTdTKlc8GTef4ljRugakth0U"
db = Database("fishing.db")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Модификаторы редкости (победители голосования)
RARITY = [
    {"p": "⚪️ [Обыч.]", "m": 1.0, "w": 50},
    {"p": "🟢 [Вялый]", "m": 0.6, "w": 15},
    {"p": "🔵 [Бодрый]", "m": 1.3, "w": 20},
    {"p": "🟣 [ЭПИК]", "m": 1.8, "w": 10},
    {"p": "🟡 [ЗОЛОТОЙ]", "m": 2.5, "w": 5}
]

# Логика мутаций (Стадия 1, 2, 3)
EVO_LOGIC = {
    "radioactive": ["Радиоактивная рыба", "Теневая рыба", "Рыба Абсолютного Излучения"], # Арт Эмки на 3-ю стадию!
}

FISH_DATA = {
    "radioactive": {"name": "Радиоактивная", "weight": (0.5, 2.0), "loc": "Яма с радиацией", "bait": "Радиоактивный червь", "img": "rad_fish.png"},
    "rotten": {"name": "Гнилой Чёрт", "weight": (1.0, 2.3), "loc": "Яма с радиацией", "bait": "Гниль", "img": "flash.fish.png"},
    "blind": {"name": "Слепая Рыба", "weight": (0.7, 3.0), "loc": "Лаборатория", "bait": "Линза", "img": "blind_fish.png"},
    "spider": {"name": "Рыба-Паук", "weight": (0.2, 0.8), "loc": "Пещера", "bait": "Мясо монстра", "img": "spider_fish.png"},
    "beaver": {"name": "Бобрыба", "weight": (2.0, 4.2), "loc": "Деревня", "bait": "Кусок дерева", "img": "bober.png"},
    "copper": {"name": "Медная рыба", "weight": (3.0, 4.0), "loc": "Деревня", "bait": "Медный кусочек", "img": "copper_fish.png"},
    "honey": {"name": "Медовая рыба", "weight": (1.3, 2.2), "loc": "Лаборатория", "bait": "Баночка мёда", "img": "honey_fish.png"},
    "fluffy": {"name": "Пушистая рыба", "weight": (1.0, 2.0), "loc": "Лаборатория", "bait": "Кошачий корм", "img": "fluffy_fish.png"},
    "amethyst": {"name": "Аметистовый карп", "weight": (2.0, 2.5), "loc": "Пещера", "bait": "Осколок трезубца", "img": "amethyst_fish.png"},
    "troll": {"name": "Рыба-тролль", "weight": (0.1, 8.0), "loc": "Деревня", "bait": "Кусок дерева", "img": "troll_fish.png"},
    "super_fluffy": {"name": "СВЕРХ-ПУШИСТАЯ РЫБА", "weight": (3.0, 5.0), "loc": "Спец", "bait": None, "img": "super_fluffy.png"},
    "irinalegend": {"name": "🪼 МЕДУЗА ИРИНА", "weight": (20.0, 30.0), "loc": "Везде", "bait": None, "img": "irina.png"}
}

LOCATIONS = {"Яма с радиацией": "☢️ Яма", "Лаборатория": "🧪 Лаборатория", "Пещера": "🕸 Пещера", "Деревня": "🏘 Деревня", "Океан": "🌊 Океан"}
BAITS = {"Гниль": 10, "Мясо монстра": 10, "Радиоактивный червь": 10, "Кусок дерева": 10, "Баночка мёда": 10, "Кошачий корм": 10, "Осколок трезубца": 10, "Медный кусочек": 10, "Линза": 10}

def main_menu(uid):
    user = db.get_user(uid)
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🎣 Закинуть", callback_data="throw"), types.InlineKeyboardButton(text="🎒 Инвент", callback_data="inv"))
    kb.row(types.InlineKeyboardButton(text="🕸 Сетка (5ч)", callback_data="net"), types.InlineKeyboardButton(text="🖼 Колл.", callback_data="show_col"))
    kb.row(types.InlineKeyboardButton(text="🗺️ Локации", callback_data="loc"), types.InlineKeyboardButton(text="🧪 Магазин", callback_data="bait_menu"))
    kb.row(types.InlineKeyboardButton(text="🏆 Топ", callback_data="top"), types.InlineKeyboardButton(text="📖 Альманах", callback_data="almanac"))
    return kb.as_markup()

@dp.message(Command("start"))
async def start(msg: types.Message):
    db.register_user(msg.from_user.id, msg.from_user.first_name)
    user = db.get_user(msg.from_user.id)
    await msg.answer(f"📦 <b>{msg.from_user.first_name}</b>, добро пожаловать!\n💰 Баланс: <b>{round(user[2], 1)}</b>\n🗺 Локация: {user[3]}", reply_markup=main_menu(msg.from_user.id))

# --- ПЕРЕДАЧА ДЕНЕГ И РЫБ ---
@dp.message(F.text.lower().startswith("передать"))
async def transfer_money(msg: types.Message):
    if not msg.reply_to_message: return await msg.answer("⚠️ Ответь на сообщение друга!")
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return await msg.answer("Пиши: передать 100")
    amount = int(parts[1])
    if db.get_user(msg.from_user.id)[2] < amount: return await msg.answer("❌ Мало денег!")
    with db.connection:
        db.cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, msg.from_user.id))
        db.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, msg.reply_to_message.from_user.id))
    await msg.answer(f"✅ {msg.from_user.first_name} передал {amount} 💰")

@dp.message(F.text.lower().startswith("отдать"))
async def transfer_fish_cmd(msg: types.Message):
    if not msg.reply_to_message: return await msg.answer("⚠️ Ответь на сообщение друга!")
    fish_name = msg.text[7:].strip()
    inv = db.cursor.execute("SELECT id FROM inventory WHERE user_id = ? AND fish_name LIKE ?", (msg.from_user.id, f"%{fish_name}%")).fetchone()
    if inv and db.transfer_fish(msg.from_user.id, msg.reply_to_message.from_user.id, inv[0]):
        await msg.answer(f"🎁 Рыба <b>{fish_name}</b> передана!")
    else: await msg.answer("❌ Рыба не найдена")

# --- ОБРАБОТКА КНОПОК ---
@dp.callback_query()
async def handle_callbacks(call: types.CallbackQuery):
    uid = call.from_user.id
    user = db.get_user(uid)
    now = datetime.now()

    if call.data == "throw":
        if user[5] and now < datetime.fromisoformat(user[5]) + timedelta(minutes=10):
            wait = (datetime.fromisoformat(user[5]) + timedelta(minutes=10) - now).seconds // 60
            return await call.answer(f"⏳ Жди {wait+1} мин. или купи подкормку!", show_alert=True)

        # Логика мутаций и редкости
        loc = user[3]
        pool = [k for k, v in FISH_DATA.items() if v["loc"] == loc or v["loc"] == "Везде"]
        if not pool: pool = ["radioactive"]
        
        f_key = random.choice(pool)
        
        # 3 стадии эволюции
        if f_key in EVO_LOGIC:
            stage_roll = random.random()
            if stage_roll < 0.05: f_name = EVO_LOGIC[f_key][2] # Абсолют
            elif stage_roll < 0.25: f_name = EVO_LOGIC[f_key][1] # Тень
            else: f_name = EVO_LOGIC[f_key][0]
        else: f_name = FISH_DATA[f_key]["name"]

        # Модификатор (⚪️, 🔵, 🟡)
        mod = random.choices(RARITY, weights=[m["w"] for m in RARITY])[0]
        f_name = f"{mod['p']} {f_name}"
        
        weight = round(random.uniform(FISH_DATA[f_key]["weight"][0], FISH_DATA[f_key]["weight"][1]) * mod["m"], 2)
        price = round(weight * 5, 1)

        db.add_fish(uid, f_name, weight, price)
        with db.connection:
            db.cursor.execute("UPDATE users SET bait = 'Нет', last_fish_time = ? WHERE user_id = ?", (now.isoformat(), uid))
        
        await call.message.answer(f"🎣 <b>{f_name}</b> ({weight} кг)\n💰 Цена: {price}")
        await call.message.edit_text(f"💰 Баланс: <b>{round(user[2], 1)}</b>", reply_markup=main_menu(uid))

    elif call.data == "net": # СЕТКА
        if user[6] and now < datetime.fromisoformat(user[6]) + timedelta(hours=5):
            rem = datetime.fromisoformat(user[6]) + timedelta(hours=5) - now
            return await call.answer(f"🕸 Сетка сохнет! Еще {rem.seconds//3600}ч.", show_alert=True)
        
        for _ in range(15):
            db.add_fish(uid, "🕸 Рыба из сетки", round(random.uniform(0.5, 2.0), 1), 5.0)
        
        with db.connection: db.cursor.execute("UPDATE users SET last_net_time = ? WHERE user_id = ?", (now.isoformat(), uid))
        await call.answer("🕸 Сетка принесла 15 рыб!", show_alert=True)

    elif call.data == "inv":
        inv = db.get_inventory(uid)
        text = f"🎒 <b>Инвентарь:</b>\n"
        kb = InlineKeyboardBuilder()
        for fid, name, w, p in inv[:10]:
            text += f"• {name} ({w}кг)\n"
            kb.button(text=f"📦 В колл. {name[:10]}", callback_data=f"to_col_{fid}")
        kb.adjust(1)
        kb.row(types.InlineKeyboardButton(text="💰 Продать всё", callback_data="sell_all"), types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text(text if inv else "🎒 Пусто", reply_markup=kb.as_markup())

    elif call.data.startswith("to_col_"):
        fid = int(call.data.split("_")[2])
        if db.add_to_collection(uid, fid): await call.answer("🖼 В коллекции!")
        else: await call.answer("❌ Ошибка")
        await handle_callbacks(call.__class__(**{**call.__dict__, 'data': 'inv'}))

    elif call.data == "show_col":
        col = db.get_collection(uid)
        text = "🖼 <b>ТВОЯ КОЛЛЕКЦИЯ:</b>\n" + "\n".join([f"• {n} ({w}кг)" for n, w in col])
        await call.message.edit_text(text if col else "🖼 Пусто", reply_markup=InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="back").as_markup())

    elif call.data == "top":
        top = db.get_top()
        text = "🏆 <b>ТОП (Капитал + Коллекция):</b>\n"
        for i, (name, total) in enumerate(top, 1): text += f"{i}. {name} — {total} 💰\n"
        await call.message.edit_text(text, reply_markup=InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="back").as_markup())

    elif call.data == "bait_menu":
        kb = InlineKeyboardBuilder()
        for b, p in BAITS.items(): kb.button(text=f"{b} ({p}💰)", callback_data=f"buy_{b}")
        kb.button(text="🧪 Подкормка (5💰)", callback_data="feed") # СРЕЗ КД
        kb.adjust(2)
        kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text(f"🧪 Магазин. Твой баланс: {round(user[2], 1)}", reply_markup=kb.as_markup())

    elif call.data == "feed":
        if user[2] < 5: return await call.answer("Мало монет!", show_alert=True)
        if not user[5]: return await call.answer("КД нет", show_alert=True)
        last_t = datetime.fromisoformat(user[5])
        new_t = (now - (timedelta(minutes=10) - (last_t + timedelta(minutes=10) - now) / 2))
        with db.connection: db.cursor.execute("UPDATE users SET balance = balance - 5, last_fish_time = ? WHERE user_id = ?", (new_last.isoformat(), uid))
        await call.answer("🚀 КД срезано вдвое!", show_alert=True)

    elif call.data == "almanac":
        await call.message.edit_text("📔 <b>АЛЬМАНАХ</b>\n☢️ Яма: Радиоактивная -> Теневая -> Абсолют\n🧪 Лаб: Медовая, Пушистая\n...и другие мемы!", reply_markup=InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="back").as_markup())

    elif call.data == "back":
        await call.message.edit_text(f"💰 Баланс: <b>{round(user[2], 1)}</b>", reply_markup=main_menu(uid))

    elif call.data == "sell_all":
        earned = db.sell_all(uid)
        await call.answer(f"✅ +{earned} 💰")
        await handle_callbacks(call.__class__(**{**call.__dict__, 'data': 'back'}))

    elif call.data.startswith("setloc_"):
        new_loc = call.data.split("_")[1]
        with db.connection: db.cursor.execute("UPDATE users SET location = ? WHERE user_id = ?", (new_loc, uid))
        await call.answer(f"Едем в {new_loc}!")
        await handle_callbacks(call.__class__(**{**call.__dict__, 'data': 'back'}))

    elif call.data == "loc":
        kb = InlineKeyboardBuilder()
        for k, v in LOCATIONS.items(): kb.button(text=v, callback_data=f"setloc_{k}")
        kb.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text("🗺 Куда едем?", reply_markup=kb.as_markup())

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
