import secrets
import string
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update
from passlib.hash import bcrypt
from db import AsyncSessionLocal
from models import AdminInvite, User, Faculty
from roles import Role


router = Router()


class ClaimAdminStates(StatesGroup):
    waiting_code = State()


def generate_credentials() -> tuple[str, str]:
    login = f"admin_{secrets.randbelow(10000):04d}"
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    return login, password


@router.message(Command("iamadmin"))
async def iamadmin_start(message: Message, state: FSMContext):
    await state.set_state(ClaimAdminStates.waiting_code)
    await message.answer("Введите код администратора факультета:")


@router.message(ClaimAdminStates.waiting_code)
async def iamadmin_process_code(message: Message, state: FSMContext):
    code = message.text.strip()
    if not code:
        await message.answer("Код пустой. Попробуйте снова или обратитесь к суперадмину.")
        return

    async with AsyncSessionLocal() as session:
        # Ищем активное приглашение по коду
        result = await session.execute(
            select(AdminInvite).where(AdminInvite.invite_code == code, AdminInvite.is_used == False)
        )
        invite = result.scalar_one_or_none()

        if not invite:
            await message.answer("❌ Неверный или уже использованный код. Проверьте и попробуйте снова.")
            return

        # Подтягиваем факультет
        fac_res = await session.execute(select(Faculty).where(Faculty.id == invite.faculty_id))
        faculty = fac_res.scalar_one_or_none()
        if not faculty:
            await message.answer("❌ Связанный факультет не найден. Обратитесь к суперадмину.")
            return

        # Проверяем пользователя по tg_id
        user_res = await session.execute(select(User).where(User.tg_id == str(message.from_user.id)))
        user = user_res.scalar_one_or_none()

        created_credentials_text = ""
        if user is None:
            login, password = generate_credentials()
            user = User(
                username=login,
                password_hash=bcrypt.hash(password),
                full_name=f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or None,
                tg_id=str(message.from_user.id),
                faculty_id=invite.faculty_id,
                role=Role.ADMIN.value,
                is_active=True,
            )
            session.add(user)
            created_credentials_text = f"\n\nВаши данные для входа на сайт:\n👤 Логин: `{login}`\n🔑 Пароль: `{password}`"
        else:
            # Обновляем роль и факультет существующего пользователя
            user.role = Role.ADMIN.value
            user.faculty_id = invite.faculty_id
            session.add(user)

        # Помечаем код как использованный
        await session.execute(
            update(AdminInvite).where(AdminInvite.id == invite.id).values(is_used=True)
        )

        await session.commit()

        await message.answer(
            f"✅ Вы назначены администратором факультета: {faculty.name}.{created_credentials_text}",
            parse_mode="Markdown"
        )
        await state.clear()

