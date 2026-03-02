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

@dp.callback_query()
async def handle_callbacks(call: types.CallbackQuery):
    uid = call.from_user.id
    user = db.get_user(uid) # [id, name, balance, loc, bait, last_time]
    now = datetime.now()

    if call.data == "throw":
        # ПРОВЕРКА КД 10 МИНУТ
        if user[5]:
            last_time = datetime.fromisoformat(user[5])
            if now < last_time + timedelta(minutes=10):
                wait = (last_time + timedelta(minutes=10) - now).seconds // 60
                return await call.answer(f"⏳ Рыба пугливая! Жди {wait+1} мин.", show_alert=True)

        current_loc = user[3]
        current_bait = user[4]
        
        # ЛОГИКА ШАНСОВ
        LOC_POOLS = {"Яма с радиацией": ["radioactive", "rotten"], "Лаборатория": ["blind", "honey", "fluffy"], "Пещера": ["spider", "amethyst"], "Деревня": ["beaver", "copper", "troll"], "Океан": [k for k in FISH_DATA.keys() if k not in ["irinalegend", "super_fluffy"]]}
        
        if random.random() < 0.005: fish_key = "irinalegend"
        else:
            target_fish = [k for k, v in FISH_DATA.items() if v.get("bait") == current_bait]
            if target_fish and random.random() < 0.5: fish_key = random.choice(target_fish)
            elif current_loc in LOC_POOLS and random.random() < 0.8: fish_key = random.choice(LOC_POOLS[current_loc])
            else: fish_key = random.choice(LOC_POOLS["Океан"])

        if fish_key == "fluffy" and random.random() < 0.03: fish_key = "super_fluffy"

        fish = FISH_DATA[fish_key]
        weight = round(random.uniform(fish["weight"][0], fish["weight"][1]), 2)
        price = round(weight * 5, 1)
        
        db.add_fish(uid, fish["name"], price)
        with db.connection:
            db.cursor.execute("UPDATE users SET bait = 'Нет', last_fish_time = ? WHERE user_id = ?", (now.isoformat(), uid))

        # ОТПРАВКА СТИКЕРА (новым сообщением)
        img_path = os.path.join(IMG_DIR, fish["img"])
        if os.path.exists(img_path):
            await call.message.answer_sticker(sticker=FSInputFile(img_path))

        await call.message.answer(f"試 <b>{call.from_user.first_name}</b> в <i>{current_loc}</i> выловил:\n🐟 <b>{fish['name']}</b> ({weight} кг)\n💰 Цена: {price}", reply_markup=main_menu(user[2]))

    elif call.data == "loc":
        kb = InlineKeyboardBuilder()
        for k, v in LOCATIONS.items(): kb.button(text=v, callback_data=f"setloc_{k}")
        kb.adjust(2)
        kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        # ТУТ РЕДАКТИРУЕМ
        await call.message.edit_text(f"🗺 Локация: <b>{user[3]}</b>\nКуда едем?", reply_markup=kb.as_markup())

    elif call.data == "bait_menu":
        kb = InlineKeyboardBuilder()
        for b_name, price in BAITS.items():
            kb.button(text=f"{b_name} ({price}💰)", callback_data=f"buy_{b_name}")
        kb.adjust(2)
        kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        # ТУТ РЕДАКТИРУЕМ
        await call.message.edit_text(f"🧪 Твоя наживка: <b>{user[4]}</b>\nВыбери новую (+20% шанс):", reply_markup=kb.as_markup())

    elif call.data == "inv":
        inv = db.get_inventory(uid)
        text = f"🎒 Инвентарь <b>{call.from_user.first_name}</b>:\n" + "\n".join([f"• {n} x{c} ({round(p, 1)}💰)" for n, c, p in inv])
        kb = InlineKeyboardBuilder()
        kb.button(text="💰 Продать всё", callback_data="sell_all")
        kb.button(text="⬅️ Назад", callback_data="back")
        # ТУТ РЕДАКТИРУЕМ
        await call.message.edit_text(text if inv else "🎒 В инвентаре пока пусто...", reply_markup=kb.as_markup())

    elif call.data == "top":
        top_users = db.get_top() 
        text = "🏆 <b>ТОП РЫБАКОВ:</b>\n\n"
        for i, (name, balance) in enumerate(top_users, 1):
            text += f"{i}. {name} — {round(balance, 1)} 💰\n"
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад", callback_data="back")
        # ТУТ РЕДАКТИРУЕМ
        await call.message.edit_text(text, reply_markup=kb.as_markup())

    elif call.data == "sell_all":
        earned = db.sell_all(uid)
        await call.answer(f"✅ Продано на {earned} 💰", show_alert=True)
        # Обновляем меню, чтобы баланс сразу изменился
        new_user = db.get_user(uid)
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{new_user[2]}</b> 💰", reply_markup=main_menu(new_user[2]))

    elif call.data == "back":
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{user[2]}</b> 💰", reply_markup=main_menu(user[2]))

    elif call.data.startswith("setloc_"):
        new_loc = call.data.split("_")[1]
        with db.connection: db.cursor.execute("UPDATE users SET location = ? WHERE user_id = ?", (new_loc, uid))
        await call.answer(f"Погнали в {new_loc}!", show_alert=True)
        new_user = db.get_user(uid)
        await call.message.edit_text(f"Мир МС огромен... Баланс: <b>{new_user[2]}</b> 💰", reply_markup=main_menu(new_user[2]))

    await call.answer()

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())