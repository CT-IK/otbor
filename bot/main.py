import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from filters import HasRoleFilter
from roles import Role
from superadmin_handlers import router as superadmin_router
from invite_handler import router as invite_router


bot = Bot(token=settings.bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры
dp.include_router(superadmin_router)
dp.include_router(invite_router)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка /start без аргументов - показываем главное меню суперадмина"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Факультеты", callback_data="faculties_menu")],
        [InlineKeyboardButton(text="👥 Админы", callback_data="admins_menu")],
        [InlineKeyboardButton(text="📊 Google таблицы", callback_data="sheets_menu")],
        [InlineKeyboardButton(text="ℹ️ Справка", callback_data="help")]
    ])
    await message.answer("🔧 Панель суперадмина", reply_markup=keyboard)


@dp.message(Command("whoami"), HasRoleFilter([Role.SUPERADMIN]))
async def whoami_super(message: Message):
    await message.answer("Ты — суперадмин. Используй /help_superadmin для списка команд.")


@dp.message(Command("whoami"), HasRoleFilter([Role.ADMIN]))
async def whoami_admin(message: Message):
    await message.answer("Ты — админ факультета")


@dp.message(Command("whoami"), HasRoleFilter([Role.EXPERIENCED]))
async def whoami_exp(message: Message):
    await message.answer("Ты — опытный собесер")


@dp.message(Command("whoami"), HasRoleFilter([Role.NEWBIE]))
async def whoami_new(message: Message):
    await message.answer("Ты — неопытный собесер")


@dp.message(Command("whoami"))
async def whoami_unknown(message: Message):
    await message.answer("Роль не найдена. Обратитесь к администратору.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

