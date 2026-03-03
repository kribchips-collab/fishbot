import asyncio
import random
import time
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

# Пути для стикеров
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")

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
    "super_fluffy": {"name": "СВЕРХ-ПУШИСТАЯ РЫБА", "weight": (3.0, 5.0), "loc": "Спец", "bait": None, "img": "super_fluffy.png"},
    "irinalegend": {"name": "🪼 МЕДУЗА ИРИНА", "weight": (20.0, 30.0), "loc": "Везде", "bait": None, "img": "irina.png"}
}

LOCATIONS = {"Яма с радиацией": "☢️ Яма", "Лаборатория": "🧪 Лаборатория", "Пещера": "🕸 Пещера", "Деревня": "🏘 Деревня", "Океан": "🌊 Океан"}
BAITS = {"Гниль": 10, "Мясо монстра": 10, "Радиоактивный червь": 10, "Кусок дерева": 10, "Баночка мёда": 10, "Кошачий корм": 10, "Осколок трезубца": 10, "Медный кусочек": 10, "Линза": 10}

FISH_MODS = [
    {"p": "🐢 Вялый", "m": 0.5, "w": 15},
    {"p": "🤢 Гнилой", "m": 0.7, "w": 15},
    {"p": "", "m": 1.0, "w": 40},
    {"p": "🔹 Бодрый", "m": 1.3, "w": 15},
    {"p": "🔸 Сильный", "m": 1.8, "w": 10},
    {"p": "👑 Золотой", "m": 2.5, "w": 5}
]

def main_menu(balance=0):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🎣 Закинуть", callback_data="throw"), types.InlineKeyboardButton(text="🎒 Инвент", callback_data="inv"))
    kb.row(types.InlineKeyboardButton(text="🗺️ Локации", callback_data="loc"), types.InlineKeyboardButton(text="🧪 Наживка", callback_data="bait_menu"))
    kb.row(types.InlineKeyboardButton(text="🏆 Топ", callback_data="top"), types.InlineKeyboardButton(text=f"💰 {balance}", callback_data="stats"))
    return kb.as_markup()

@dp.message(Command("start"))
async def start(msg: types.Message):
    db.register_user(msg.from_user.id, msg.from_user.first_name)
    user = db.get_user(msg.from_user.id)
    await msg.answer(f"Мир МС огромен... Твой баланс: <b>{user[2]}</b> 💰", reply_markup=main_menu(user[2]))

@dp.message(F.text.lower().in_(["фиш", "fish", "закинуть"]))
async def qol_throw(msg: types.Message):
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
    user = db.get_user(msg.from_user.id)
    inv = db.get_inventory(msg.from_user.id)
    text = f"🎒 Инвентарь <b>{msg.from_user.first_name}</b>:\n" + "\n".join([f"• {n} x{c} ({round(p, 1)}💰)" for n, c, p in inv])
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Продать всё", callback_data="sell_all")
    await msg.answer(text if inv else "🎒 В инвентаре пусто...", reply_markup=kb.as_markup())

@dp.callback_query()
async def handle_callbacks(call: types.CallbackQuery):
    uid = call.from_user.id
    user = db.get_user(uid)
    now = datetime.now()

    if call.data == "throw":
        if user[5]:
            last_time = datetime.fromisoformat(user[5])
            if now < last_time + timedelta(minutes=10):
                wait = (last_time + timedelta(minutes=10) - now).seconds // 60
                return await call.answer(f"⏳ Рыба пугливая! Жди {wait+1} мин.", show_alert=True)

        current_loc = user[3]
        current_bait = user[4]
        LOC_POOLS = {
            "Яма с радиацией": ["radioactive", "rotten"], 
            "Лаборатория": ["blind", "honey", "fluffy"], 
            "Пещера": ["spider", "amethyst"], 
            "Деревня": ["beaver", "copper", "troll"], 
            "Океан": [k for k in FISH_DATA.keys() if k not in ["irinalegend", "super_fluffy"]]
        }
        
        if random.random() < 0.005: 
            fish_key = "irinalegend"
        else:
            target_fish = [k for k, v in FISH_DATA.items() if v.get("bait") == current_bait]
            if target_fish and random.random() < 0.5: fish_key = random.choice(target_fish)
            elif current_loc in LOC_POOLS and random.random() < 0.8: fish_key = random.choice(LOC_POOLS[current_loc])
            else: fish_key = random.choice(LOC_POOLS["Океан"])

        if fish_key == "fluffy" and random.random() < 0.03: fish_key = "super_fluffy"
        fish = FISH_DATA[fish_key]

        mod = random.choices(FISH_MODS, weights=[m["w"] for m in FISH_MODS])[0]
        prefix = mod['p'] + " " if mod['p'] else ""
        final_name = f"{prefix}{fish['name']}"
        weight = round(random.uniform(fish["weight"][0], fish["weight"][1]) * mod['m'], 2)
        price = round(weight * 5, 1)

        db.add_fish(uid, final_name, price)
        with db.connection:
            db.cursor.execute("UPDATE users SET bait = 'Нет', last_fish_time = ? WHERE user_id = ?", (now.isoformat(), uid))

        img_path = os.path.join(IMG_DIR, fish["img"])
        if os.path.exists(img_path):
            await call.message.answer_sticker(sticker=FSInputFile(img_path))
        
        await call.message.answer(
            f"🎣 <b>{call.from_user.first_name}</b> в <i>{current_loc}</i> выловил:\n"
            f"🐟 <b>{final_name}</b> ({weight} кг)\n💰 Цена: {price}", 
            reply_markup=main_menu(user[2])
        )

    elif call.data == "bait_menu":
        kb = InlineKeyboardBuilder()
        for b_name, p in BAITS.items():
            kb.button(text=f"{b_name} ({p}💰)", callback_data=f"buy_{b_name}")
        kb.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text(f"🧪 Твоя наживка: <b>{user[4]}</b>\nВыбери за 10💰:", reply_markup=kb.as_markup())

    elif call.data.startswith("buy_"):
        b_name = call.data.split("_")[1]
        p = BAITS.get(b_name, 10)
        if user[2] >= p:
            with db.connection:
                db.cursor.execute("UPDATE users SET balance = balance - ?, bait = ? WHERE user_id = ?", (p, b_name, uid))
            await call.answer(f"✅ Куплено: {b_name}", show_alert=True)
            new_u = db.get_user(uid)
            await call.message.edit_text(f"🧪 Твоя наживка: <b>{new_u[4]}</b>\nВыбери новую:", reply_markup=call.message.reply_markup)
        else:
            await call.answer("❌ Нет денег!", show_alert=True)

    elif call.data == "inv":
        inv = db.get_inventory(uid)
        text = f"🎒 Инвентарь <b>{call.from_user.first_name}</b>:\n" + "\n".join([f"• {n} x{c} ({round(p, 1)}💰)" for n, c, p in inv])
        kb = InlineKeyboardBuilder()
        kb.button(text="💰 Продать всё", callback_data="sell_all")
        kb.button(text="⬅️ Назад", callback_data="back")
        await call.message.edit_text(text if inv else "🎒 Пусто", reply_markup=kb.as_markup())

    elif call.data == "top":
        top = db.get_top()
        text = "🏆 <b>ТОП:</b>\n\n" + "\n".join([f"{i}. {n} — {round(b, 1)}💰" for i, (n, b) in enumerate(top, 1)])
        kb = InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="back")
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    elif call.data == "back":
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{user[2]}</b> 💰", reply_markup=main_menu(user[2]))

    elif call.data == "loc":
        kb = InlineKeyboardBuilder()
        for k, v in LOCATIONS.items(): kb.button(text=v, callback_data=f"setloc_{k}")
        kb.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await call.message.edit_text(f"🗺 Локация: <b>{user[3]}</b>", reply_markup=kb.as_markup())

    elif call.data.startswith("setloc_"):
        new_l = call.data.split("_")[1]
        with db.connection: db.cursor.execute("UPDATE users SET location = ? WHERE user_id = ?", (new_l, uid))
        await call.answer(f"В {new_l}!", show_alert=True)
        new_u = db.get_user(uid)
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{new_u[2]}</b> 💰", reply_markup=main_menu(new_u[2]))

    elif call.data == "sell_all":
        e = db.sell_all(uid)
        await call.answer(f"✅ +{e} 💰", show_alert=True)
        new_u = db.get_user(uid)
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{new_u[2]}</b> 💰", reply_markup=main_menu(new_u[2]))
    await call.answer()
@dp.message(Command("testfish"))
async def test_fish(msg: types.Message):
    # Берем данные игрока, чтобы знать его локацию и наживку
    user = db.get_user(msg.from_user.id)
    current_loc = user[3]
    current_bait = user[4]

    # 1. Логика бассейнов (копия основной)
    LOC_POOLS = {
        "Яма с радиацией": ["radioactive", "rotten"], 
        "Лаборатория": ["blind", "honey", "fluffy"], 
        "Пещера": ["spider", "amethyst"], 
        "Деревня": ["beaver", "copper", "troll"], 
        "Океан": [k for k in FISH_DATA.keys() if k not in ["irinalegend", "super_fluffy"]]
    }

    # 2. Выбор рыбы
    if random.random() < 0.005: 
        f_key = "irinalegend"
    else:
        target = [k for k, v in FISH_DATA.items() if v.get("bait") == current_bait]
        if target and random.random() < 0.5: f_key = random.choice(target)
        elif current_loc in LOC_POOLS and random.random() < 0.8: f_key = random.choice(LOC_POOLS[current_loc])
        else: f_key = random.choice(LOC_POOLS["Океан"])

    if f_key == "fluffy" and random.random() < 0.03: f_key = "super_fluffy"
    fish = FISH_DATA[f_key]

    # 3. Модификаторы
    mod = random.choices(FISH_MODS, weights=[m["w"] for m in FISH_MODS])[0]
    prefix = mod['p'] + " " if mod['p'] else ""
    final_name = f"{prefix}{fish['name']}"
    
    # Расчет веса и цены для инфы
    w = round(random.uniform(fish["weight"][0], fish["weight"][1]) * mod['m'], 2)
    p = round(w * 5, 1)

    # 4. Вывод (БЕЗ db.add_fish)
    await msg.answer(
        f"🧪 <b>ТЕСТОВЫЙ ЗАБРОС</b>\n"
        f"Локация: {current_loc}\n"
        f"Наживка: {current_bait}\n"
        f"━━━━━━━━━━━━\n"
        f"🐟 Выпало: <b>{final_name}</b> ({w} кг)\n"
        f"💰 Цена была бы: {p}\n"
        f"⚠️ <i>В инвентарь не добавлено</i>"
    )
async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())

