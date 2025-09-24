import secrets
import string
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy import select, update
from passlib.hash import bcrypt
from db import AsyncSessionLocal
from models import AdminInvite, User, Faculty
from roles import Role

router = Router()


def generate_credentials():
    """Генерирует логин и пароль для админа"""
    login = f"admin_{secrets.randbelow(10000):04d}"
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    return login, password


@router.message(CommandStart())
async def handle_start_with_invite(message: Message):
    """Обработка команды /start с кодом приглашения"""
    if not message.text or not message.from_user:
        return
    
    # Парсим аргументы команды /start
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Добро пожаловать! Обратитесь к администратору для получения доступа.")
        return
    
    invite_code = args[1]
    
    # Проверяем, что это приглашение для админа
    if not invite_code.startswith("admin_"):
        await message.answer("Неверный код приглашения!")
        return
    
    invite_code = invite_code[6:]  # Убираем префикс "admin_"
    
    async with AsyncSessionLocal() as session:
        # Ищем активное приглашение
        result = await session.execute(
            select(AdminInvite).where(
                AdminInvite.invite_code == invite_code,
                AdminInvite.is_used == False
            )
        )
        invite = result.scalar_one_or_none()
        
        if not invite:
            await message.answer("❌ Приглашение не найдено или уже использовано!")
            return
        
        # Проверяем, не зарегистрирован ли уже пользователь
        user_result = await session.execute(
            select(User).where(User.tg_id == str(message.from_user.id))
        )
        existing_user = user_result.scalar_one_or_none()
        
        if existing_user:
            await message.answer("❌ Вы уже зарегистрированы в системе!")
            return
        
        # Получаем информацию о факультете
        faculty_result = await session.execute(
            select(Faculty).where(Faculty.id == invite.faculty_id)
        )
        faculty = faculty_result.scalar_one_or_none()
        
        if not faculty:
            await message.answer("❌ Факультет не найден!")
            return
        
        # Генерируем логин и пароль для сайта
        login, password = generate_credentials()
        password_hash = bcrypt.hash(password)
        
        # Создаем пользователя-админа факультета
        admin_user = User(
            username=login,
            password_hash=password_hash,
            full_name=f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
            tg_id=str(message.from_user.id),
            faculty_id=invite.faculty_id,
            role=Role.ADMIN.value,
            is_active=True
        )
        
        session.add(admin_user)
        
        # Отмечаем приглашение как использованное
        await session.execute(
            update(AdminInvite)
            .where(AdminInvite.id == invite.id)
            .values(is_used=True)
        )
        
        await session.commit()
        await session.refresh(admin_user)
        
        await message.answer(
            f"🎉 Добро пожаловать!\n\n"
            f"📋 Вы назначены администратором факультета: **{faculty.name}**\n\n"
            f"🌐 Данные для входа на сайт:\n"
            f"👤 Логин: `{login}`\n"
            f"🔑 Пароль: `{password}`\n\n"
            f"💡 Сохраните эти данные! Они понадобятся для входа на сайт.",
            parse_mode="Markdown"
        )
