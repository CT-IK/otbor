import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.config import settings
from filters import HasRoleFilter
from roles import Role


bot = Bot(token=settings.bot_token)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот записи. Доступные команды: /whoami")


@dp.message(Command("whoami"), HasRoleFilter([Role.SUPERADMIN]))
async def whoami_super(message: Message):
    await message.answer("Ты — суперадмин")


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

