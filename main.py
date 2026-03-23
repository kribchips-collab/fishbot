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

# База инициализируется как обычно, чтобы ничего не сломать при запуске
with db.connection:
    db.cursor.execute("CREATE TABLE IF NOT EXISTS clans (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, owner_id INTEGER)")
    try:
        db.cursor.execute("ALTER TABLE users ADD COLUMN clan_id INTEGER")
    except:
        pass
    try:
        db.cursor.execute("ALTER TABLE users ADD COLUMN infection INTEGER DEFAULT 0")
    except:
        pass
    try:
        db.cursor.execute("ALTER TABLE users ADD COLUMN bath_mute TEXT")
    except:
        pass

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")

# ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ КРАБОВ
CRABS_END_TIME = None

# --- МЕРТВАЯ КЛАВИАТУРА ИВЕНТА ---
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🎣 Рыбалка заблокирована", callback_data="dead_throw"), 
           types.InlineKeyboardButton(text="🎒 У вас нихера нет", callback_data="dead_inv"))
    kb.row(types.InlineKeyboardButton(text="🗺 Океан иссох", callback_data="dead_loc"), 
           types.InlineKeyboardButton(text="🧪 Рыба сдохла наживки бесполезны", callback_data="dead_bait"))
    kb.row(types.InlineKeyboardButton(text="📖 Альманах утонул", callback_data="dead_almanac"), 
           types.InlineKeyboardButton(text="🦀 Крабы тоже умерли", callback_data="dead_crabs"))
    kb.row(types.InlineKeyboardButton(text="🛁 Ванна сломалась", callback_data="dead_bath"), 
           types.InlineKeyboardButton(text="🏆 Топа не будет", callback_data="dead_top"))
    kb.row(types.InlineKeyboardButton(text="📦 Ящики разграбили", callback_data="dead_boxes"), 
           types.InlineKeyboardButton(text="💰 0.000", callback_data="dead_stats"))
    return kb.as_markup()

# --- ОСНОВНЫЕ КОМАНДЫ (СЛОМАННЫЕ) ---
@dp.message(Command("start"))
@dp.message(F.text.lower().in_(["меню", "рыбменю", "старт"]))
async def start(msg: types.Message):
    # Регистрируем пользователя, чтобы база не падала, но баланс показываем лорный
    db.register_user(msg.from_user.id, msg.from_user.first_name)
    await msg.answer("Мир МС огромен... Баланс: <b>-10000</b> 💰", reply_markup=main_menu())

@dp.message(F.text.lower().in_(["фиш", "fish", "закинуть"]))
async def qol_throw(msg: types.Message):
    await msg.answer("ВЫ🫵🫵 ЗАКИДЫВАЕТЕ УДОЧКУ... НО ВОДЫ НЕТ... 🏜️🏜️🏜️ КРЮЧОК ВАШЕЙ УДОЧКИ 🪝 ПАДАЕТ НА ДНО ОСУШЕННОЙ БЕЗДНЫ 🕳️ И ЛИШЬ ЕЛЕ ВОЛОЧИТСЯ ПО ПЕСКУ... ⏳⏳ ГНЕВ БЕЗДНЫ 👺 ИСУШИЛ ВСЁ... 🦴🦴 РЫБЫ БОЛЬШЕ НЕТ 💀")

@dp.message(F.text.lower().in_(["инв", "inv", "инвентарь"]))
async def qol_inv(msg: types.Message):
    await msg.answer("🎒 Инвентарь пуст... Твои карманы полны лишь горячего песка и отчаяния 🏜️💀")

@dp.message(F.text.lower().in_(["сетка", "net", "сетку", "секта"]))
async def use_grid(msg: types.Message):
    await msg.answer("🕸️ Твои сети истлели на палящем солнце. Духи Бездны отвернулись от тебя, ловить больше некого... 🦴")

# --- СИСТЕМА КЛАНОВ (СЛОМАННАЯ) ---
@dp.message(F.text.lower().startswith("создать "))
async def create_clan(msg: types.Message):
    await msg.answer("🛡️ Какие кланы? Люди разбежались в панике, прячась от палящего солнца... 🏜️")

@dp.message(F.text.lower() == "пригласить")
async def invite_clan(msg: types.Message):
    await msg.answer("🤝 Некого приглашать. Вы остались одни в этой пустоши... 🕳️")

@dp.message(F.text.lower() == "выгнать")
async def kick_clan(msg: types.Message):
    await msg.answer("🥾 Выгонять бессмысленно, смерть сама заберет всех... 💀")

# --- СОЦИАЛЬНЫЕ КОМАНДЫ / КАЗИНО (СЛОМАННЫЕ) ---
@dp.message(F.text.lower().startswith("депнуть"))
async def casino_deposit(msg: types.Message):
    await msg.answer("🎰 Автоматы забились песком и больше не работают. Лудомания мертва, как и этот океан... ⏳")
        
@dp.message(F.text.lower().startswith("добавить"))
async def add_to_collection_cmd(msg: types.Message):
    await msg.answer("📦 Твоя коллекция рассыпалась в прах... Сохранять больше нечего. 🏺")

@dp.message(F.text.lower().startswith("убрать"))
async def remove_from_collection_cmd(msg: types.Message):
    await msg.answer("🎒 Забирать нечего. Там только пыль... 💨")

@dp.message(F.text.lower().startswith("переброс"))
async def reroll_cmd(msg: types.Message):
    await msg.answer("🎲 Кубик-фугу сдулся и высох... Магия мертва. 🐡🦴")
        
@dp.message(F.text.lower().startswith("передать"))
async def transfer_money(msg: types.Message):
    await msg.answer("💸 Деньги обесценились. Кому нужны монеты на дне высохшей бездны? 🪙🕳️")

@dp.message(F.text.lower().startswith("отдать"))
async def give_fish(msg: types.Message):
    await msg.answer("🎁 Твоя рыба давно протухла и превратилась в скелет. Никто это не возьмет... 🐟🦴")

@dp.message(Command("testfish"))
async def test_fish(msg: types.Message):
    await msg.answer("🧪 <b>ТЕСТ ПРОВАЛЕН</b>\nОкеана больше нет. Система рухнула. ⚠️")

# --- ОБРАБОТКА МЕРТВЫХ КНОПОК ---
@dp.callback_query()
async def handle_callbacks(call: types.CallbackQuery):
    
    if call.data == "dead_throw":
        meme_text = "ВЫ🫵🫵 ЗАКИДЫВАЕТЕ УДОЧКУ... НО ВОДЫ НЕТ... 🏜️🏜️🏜️ КРЮЧОК ВАШЕЙ УДОЧКИ 🪝 ПАДАЕТ НА ДНО ОСУШЕННОЙ БЕЗДНЫ 🕳️ И ЛИШЬ ЕЛЕ ВОЛОЧИТСЯ ПО ПЕСКУ... ⏳⏳ ГНЕВ БЕЗДНЫ 👺 ИСУШИЛ ВСЁ... 🦴🦴 РЫБЫ БОЛЬШЕ НЕТ 💀"
        return await call.answer(meme_text, show_alert=True)
        
    elif call.data == "dead_inv":
        return await call.answer("Пустота... Моль съела остатки твоих надежд 🎒💨", show_alert=True)
        
    elif call.data == "dead_loc":
        return await call.answer("Куда бы ты ни пошел, везде только мертвая пустошь... 🗺️🏜️", show_alert=True)
        
    elif call.data == "dead_bait":
        return await call.answer("Черви высохли, хлеб окаменел. Рыбы всё равно нет... 🧪🦴", show_alert=True)
        
    elif call.data == "dead_almanac":
        return await call.answer("Страницы рассыпались в пепел от жары... Знания утеряны 📖🔥", show_alert=True)
        
    elif call.data == "dead_crabs":
        return await call.answer("Даже крабы не выдержали этого гнева. На дне лишь пустые панцири... 🦀💀", show_alert=True)
        
    elif call.data == "dead_bath":
        return await call.answer("Трубы порвало. Воды нет. Мыться нечем... 🛁🩸", show_alert=True)
        
    elif call.data == "dead_top":
        return await call.answer("Победителей больше нет. Все равны перед Бездной... 🏆🕳️", show_alert=True)
        
    elif call.data == "dead_boxes":
        return await call.answer("Мародеры вскрыли все ящики до тебя... Там ничего не осталось 📦🪓", show_alert=True)

    elif call.data == "dead_stats":
        return await call.answer("Твой истинный баланс — ноль. Как и смысл всего происходящего... 💰🕳️", show_alert=True)

    # Заглушка на случай, если кто-то нажмет старую кнопку (которая зависла в старых сообщениях)
    return await call.answer("Старый мир разрушен. Обнови меню командой /start... 🏜️", show_alert=True)

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
