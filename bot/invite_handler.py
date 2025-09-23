from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy import select, update
from db import AsyncSessionLocal
from models import AdminInvite, User
from roles import Role

router = Router()


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
        
        # Создаем пользователя-админа факультета
        admin_user = User(
            username=f"admin_{message.from_user.id}",
            password_hash="",  # Пароль не нужен для бота
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
        
        await message.answer(
            f"✅ Добро пожаловать! Вы назначены администратором факультета.\n"
            f"Ваш ID: {admin_user.id}\n"
            f"Используйте /whoami для проверки роли."
        )
