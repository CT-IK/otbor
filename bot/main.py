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
from admin_claim import router as claim_router


bot = Bot(token=settings.bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры
dp.include_router(invite_router)  # Сначала invite_router для обработки /start с аргументами
dp.include_router(claim_router)
dp.include_router(superadmin_router)


@dp.message(Command("start"), HasRoleFilter([Role.SUPERADMIN]))
async def cmd_start_superadmin(message: Message):
    """Обработка /start для суперадмина - показываем главное меню"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Факультеты", callback_data="faculties_menu")],
        [InlineKeyboardButton(text="👥 Админы", callback_data="admins_menu")],
        [InlineKeyboardButton(text="📊 Google таблицы", callback_data="sheets_menu")],
        [InlineKeyboardButton(text="ℹ️ Справка", callback_data="help")]
    ])
    await message.answer("🔧 Панель суперадмина", reply_markup=keyboard)


@dp.message(Command("start"), HasRoleFilter([Role.ADMIN]))
async def cmd_start_admin(message: Message):
    """Обработка /start для админа факультета"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Занести данные", callback_data="import_faculty_data")]
    ])
    await message.answer(
        "👋 Добро пожаловать! Вы админ факультета. Используйте /whoami для проверки роли.\n\n"
        "Для загрузки данных из Google-таблицы используйте кнопку ниже:",
        reply_markup=keyboard
    )


# Обработчик кнопки "Занести данные"
from aiogram import Router
from aiogram.types import CallbackQuery
from db import AsyncSessionLocal
from models import User, Faculty
from roles import Role
from passlib.hash import bcrypt
import gsheets
from sqlalchemy import select
from backend.app.models.candidate import Candidate

@dp.callback_query(F.data == "import_faculty_data", HasRoleFilter([Role.ADMIN]))
async def import_faculty_data_handler(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        # Получаем пользователя-админа
        result = await session.execute(select(User).where(User.tg_id == user_id))
        admin = result.scalar_one_or_none()
        if not admin or not admin.faculty_id:
            await callback.answer("Ошибка: не найден факультет.", show_alert=True)
            return
        # Получаем факультет и ссылку на таблицу
        faculty_result = await session.execute(select(Faculty).where(Faculty.id == admin.faculty_id))
        faculty = faculty_result.scalar_one_or_none()
        if not faculty or not faculty.google_sheet_url:
            await callback.answer("Ошибка: не найдена Google-таблица факультета.", show_alert=True)
            return
        # Открываем таблицу
        try:
            sh = gsheets.open_sheet_by_url("bot/credentials.json", faculty.google_sheet_url)
        except Exception as e:
            await callback.answer(f"Ошибка доступа к таблице: {e}", show_alert=True)
            return
        added_candidates = 0
        added_users = 0
        # Парсим лист "Кандидаты"
        try:
            ws_candidates = sh.worksheet("Кандидаты")
            rows = ws_candidates.get_all_values()[1:]  # пропускаем заголовок
            for row in rows:
                if len(row) < 3:
                    continue
                first_name, last_name, vk_id = row[:3]
                # Проверяем, есть ли уже такой кандидат
                candidate_exists = await session.execute(select(Candidate).where(Candidate.vk_id == vk_id))
                if candidate_exists.scalar_one_or_none():
                    continue
                candidate = Candidate(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    vk_id=vk_id.strip(),
                    faculty_id=faculty.id
                )
                session.add(candidate)
                added_candidates += 1
        except Exception as e:
            await callback.answer(f"Ошибка чтения листа 'Кандидаты': {e}", show_alert=True)
            return
        # Парсим листы "Опытные собесеры" и "Не опытные собесеры"
        for sheet_name, role in [("Опытные собесеры", Role.EXPERIENCED.value), ("Не опытные собесеры", Role.NEWBIE.value)]:
            try:
                ws = sh.worksheet(sheet_name)
                rows = ws.get_all_values()[1:]  # пропускаем заголовок
                for row in rows:
                    if len(row) < 2:
                        continue
                    login, password = row[:2]
                    # Проверяем, есть ли уже такой пользователь
                    user_exists = await session.execute(select(User).where(User.username == login))
                    if user_exists.scalar_one_or_none():
                        continue
                    user = User(
                        username=login.strip(),
                        password_hash=bcrypt.hash(password.strip()),
                        faculty_id=faculty.id,
                        role=role,
                        is_active=True
                    )
                    session.add(user)
                    added_users += 1
            except Exception as e:
                await callback.answer(f"Ошибка чтения листа '{sheet_name}': {e}", show_alert=True)
                return
        await session.commit()
        await callback.answer(f"✅ Импорт завершён! Кандидатов добавлено: {added_candidates}, пользователей: {added_users}", show_alert=True)


@dp.message(Command("start"))
async def cmd_start_default(message: Message):
    """Обработка /start для неавторизованных пользователей"""
    await message.answer("Добро пожаловать! Обратитесь к администратору для получения доступа.")


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

