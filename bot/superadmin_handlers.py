import secrets
import string
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, insert, update
from db import AsyncSessionLocal
from models import Faculty, AdminInvite, User
from roles import Role
from filters import HasRoleFilter
from gsheets import check_access

router = Router()


class FacultyStates(StatesGroup):
    waiting_faculty_name = State()


class SheetStates(StatesGroup):
    waiting_sheet_url = State()


def generate_invite_code() -> str:
    """Генерирует уникальный код приглашения"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))


# Убираем обработчик /start отсюда, он теперь в main.py


@router.callback_query(F.data == "faculties_menu", HasRoleFilter([Role.SUPERADMIN]))
async def faculties_menu(callback: CallbackQuery):
    """Меню факультетов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать факультет", callback_data="create_faculty")],
        [InlineKeyboardButton(text="📋 Список факультетов", callback_data="list_faculties")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("📋 Управление факультетами", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admins_menu", HasRoleFilter([Role.SUPERADMIN]))
async def admins_menu(callback: CallbackQuery):
    """Меню админов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Создать приглашение", callback_data="create_invite")],
        [InlineKeyboardButton(text="📋 Активные приглашения", callback_data="list_invites")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("👥 Управление админами", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "sheets_menu", HasRoleFilter([Role.SUPERADMIN]))
async def sheets_menu(callback: CallbackQuery):
    """Меню Google таблиц"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Привязать таблицу", callback_data="set_sheet")],
        [InlineKeyboardButton(text="✅ Проверить доступы", callback_data="check_sheets")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("📊 Управление Google таблицами", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "check_sheets", HasRoleFilter([Role.SUPERADMIN]))
async def check_all_sheets(callback: CallbackQuery):
    """Проверяем доступ ко всем привязанным таблицам"""
    # credentials.json должен лежать в /app/bot/credentials.json (смонтируй файл в контейнер)
    credentials_path = "/app/bot/credentials.json"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Faculty))
        faculties = result.scalars().all()

    if not faculties:
        await callback.message.edit_text("❌ Факультеты не найдены")
        await callback.answer()
        return

    lines = ["Проверка доступов к Google Sheets:\n"]
    for f in faculties:
        if not getattr(f, "google_sheet_url", None):
            lines.append(f"• {f.name}: ⚠️ ссылка не задана")
            continue
        ok, msg, title = check_access(credentials_path, f.google_sheet_url)
        status = "✅" if ok else "❌"
        suffix = f" (таблица: {title})" if ok and title else (f" — {msg[:80]}" if not ok else "")
        lines.append(f"• {f.name}: {status}{suffix}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="sheets_menu")]
    ])
    await callback.message.edit_text("\n".join(lines), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back_to_main", HasRoleFilter([Role.SUPERADMIN]))
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Факультеты", callback_data="faculties_menu")],
        [InlineKeyboardButton(text="👥 Админы", callback_data="admins_menu")],
        [InlineKeyboardButton(text="📊 Google таблицы", callback_data="sheets_menu")],
        [InlineKeyboardButton(text="ℹ️ Справка", callback_data="help")]
    ])
    await callback.message.edit_text("🔧 Панель суперадмина", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "create_faculty", HasRoleFilter([Role.SUPERADMIN]))
async def create_faculty_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания факультета"""
    await state.set_state(FacultyStates.waiting_faculty_name)
    await callback.message.edit_text(
        "📝 Введите название факультета:\n\n"
        "Пример: ФКН, ФИВТ, ФУПМ"
    )
    await callback.answer()


@router.message(FacultyStates.waiting_faculty_name, F.text.regexp(r'^[А-ЯЁ][А-ЯЁа-яё\s]+$'))
async def create_faculty_process(message: Message, state: FSMContext):
    """Обработка создания факультета"""
    faculty_name = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        # Проверяем, не существует ли уже такой факультет
        result = await session.execute(select(Faculty).where(Faculty.name == faculty_name))
        existing = result.scalar_one_or_none()
        
        if existing:
            await message.answer(f"❌ Факультет '{faculty_name}' уже существует!")
            return
        
        # Создаем новый факультет
        faculty = Faculty(name=faculty_name)
        session.add(faculty)
        await session.commit()
        await session.refresh(faculty)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ])
        await message.answer(
            f"✅ Факультет '{faculty_name}' создан!\nID: {faculty.id}",
            reply_markup=keyboard
        )
        await state.clear()


@router.callback_query(F.data == "list_faculties", HasRoleFilter([Role.SUPERADMIN]))
async def list_faculties(callback: CallbackQuery):
    """Список факультетов"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Faculty))
        faculties = result.scalars().all()
        
        if not faculties:
            await callback.message.edit_text("❌ Факультеты не найдены")
            await callback.answer()
            return
        
        text = "📋 Список факультетов:\n\n"
        for faculty in faculties:
            sheet_status = "📊" if faculty.google_sheet_url else "❌"
            text += f"{faculty.id}. {faculty.name} {sheet_status}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="faculties_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data == "create_invite", HasRoleFilter([Role.SUPERADMIN]))
async def create_invite_start(callback: CallbackQuery):
    """Начало создания приглашения"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Faculty))
        faculties = result.scalars().all()
        
        if not faculties:
            await callback.message.edit_text("❌ Сначала создайте факультет!")
            await callback.answer()
            return
        
        keyboard_buttons = []
        for faculty in faculties:
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"{faculty.name}",
                callback_data=f"invite_faculty_{faculty.id}"
            )])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admins_menu")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text("👥 Выберите факультет для создания приглашения:", reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data.startswith("invite_faculty_"), HasRoleFilter([Role.SUPERADMIN]))
async def create_invite_process(callback: CallbackQuery):
    """Создание приглашения для выбранного факультета"""
    faculty_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        # Получаем факультет
        result = await session.execute(select(Faculty).where(Faculty.id == faculty_id))
        faculty = result.scalar_one_or_none()
        
        if not faculty:
            await callback.message.edit_text("❌ Факультет не найден!")
            await callback.answer()
            return
        
        # Генерируем уникальный код приглашения
        invite_code = generate_invite_code()
        
        # Создаем запись приглашения
        invite = AdminInvite(
            faculty_id=faculty_id,
            invite_code=invite_code,
            created_at=datetime.now().isoformat()
        )
        session.add(invite)
        await session.commit()
        
        # Формируем ссылку
        invite_link = f"https://t.me/otbor_2025_bot?start=admin_{invite_code}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admins_menu")]
        ])
        
        await callback.message.edit_text(
            f"🔗 Ссылка-приглашение для админа факультета '{faculty.name}':\n\n"
            f"`{invite_link}`\n\n"
            f"Код: `{invite_code}`",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()


@router.callback_query(F.data == "list_invites", HasRoleFilter([Role.SUPERADMIN]))
async def list_invites(callback: CallbackQuery):
    """Список активных приглашений"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AdminInvite, Faculty)
            .join(Faculty, AdminInvite.faculty_id == Faculty.id)
            .where(AdminInvite.is_used == False)
        )
        invites = result.all()
        
        if not invites:
            await callback.message.edit_text("❌ Активных приглашений нет")
            await callback.answer()
            return
        
        text = "🔗 Активные приглашения:\n\n"
        for invite, faculty in invites:
            text += f"• {faculty.name} - код: `{invite.invite_code}`\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admins_menu")]
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data == "set_sheet", HasRoleFilter([Role.SUPERADMIN]))
async def set_sheet_start(callback: CallbackQuery):
    """Начало привязки Google таблицы"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Faculty))
        faculties = result.scalars().all()
        
        if not faculties:
            await callback.message.edit_text("❌ Сначала создайте факультет!")
            await callback.answer()
            return
        
        keyboard_buttons = []
        for faculty in faculties:
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"{faculty.name}",
                callback_data=f"sheet_faculty_{faculty.id}"
            )])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="sheets_menu")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text("📊 Выберите факультет для привязки Google таблицы:", reply_markup=keyboard)
        await callback.answer()


@router.callback_query(F.data.startswith("sheet_faculty_"), HasRoleFilter([Role.SUPERADMIN]))
async def set_sheet_process(callback: CallbackQuery, state: FSMContext):
    """Привязка Google таблицы к выбранному факультету"""
    faculty_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Faculty).where(Faculty.id == faculty_id))
        faculty = result.scalar_one_or_none()
        
        if not faculty:
            await callback.message.edit_text("❌ Факультет не найден!")
            await callback.answer()
            return
        
        await state.set_state(SheetStates.waiting_sheet_url)
        await state.update_data(faculty_id=faculty_id)
        await callback.message.edit_text(
            f"📊 Введите URL Google таблицы для факультета '{faculty.name}':\n\n"
            f"Пример: https://docs.google.com/spreadsheets/d/..."
        )
        await callback.answer()


@router.message(SheetStates.waiting_sheet_url, F.text.regexp(r'^https://docs\.google\.com/spreadsheets/'))
async def set_sheet_url(message: Message, state: FSMContext):
    """Обработка URL Google таблицы"""
    sheet_url = message.text.strip()
    data = await state.get_data()
    faculty_id = data.get('faculty_id')
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Faculty).where(Faculty.id == faculty_id))
        faculty = result.scalar_one_or_none()
        
        if not faculty:
            await message.answer("❌ Факультет не найден!")
            await state.clear()
            return
        
        # Обновляем URL таблицы
        await session.execute(
            update(Faculty)
            .where(Faculty.id == faculty_id)
            .values(google_sheet_url=sheet_url)
        )
        await session.commit()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ])
        await message.answer(
            f"✅ Google таблица привязана к факультету '{faculty.name}'",
            reply_markup=keyboard
        )
        await state.clear()


@router.callback_query(F.data == "help", HasRoleFilter([Role.SUPERADMIN]))
async def help_menu(callback: CallbackQuery):
    """Справка"""
    help_text = """
🔧 Панель суперадмина

📋 Факультеты:
• Создание новых факультетов
• Просмотр списка факультетов

👥 Админы:
• Создание ссылок-приглашений
• Просмотр активных приглашений

📊 Google таблицы:
• Привязка таблиц к факультетам

ℹ️ Все действия выполняются через кнопки меню
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(help_text, reply_markup=keyboard)
    await callback.answer()
