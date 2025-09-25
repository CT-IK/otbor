import asyncio
from models import User, Faculty, Candidate
from roles import Role
from passlib.hash import bcrypt
from sqlalchemy import select

import json
import gspread
from google.oauth2.service_account import Credentials
from typing import Tuple, Optional


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def open_sheet_by_url(credentials_path: str, sheet_url: str):
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(sheet_url)
    return sh


def check_access(credentials_path: str, sheet_url: str) -> Tuple[bool, str, Optional[str]]:
    try:
        sh = open_sheet_by_url(credentials_path, sheet_url)
        # простая проверка — читаем имена листов
        _ = [ws.title for ws in sh.worksheets()]
        return True, "ok", sh.title
    except Exception as e:
        return False, str(e), None


# Асинхронный импорт данных из Google-таблицы факультета
async def import_faculty_spreadsheet(sheet_url: str, session, credentials_path: str = "bot/credentials.json"):
    """
    Импортирует кандидатов и собесеров из Google-таблицы факультета в базу данных.
    Возвращает: (added_candidates, added_users)
    """
    loop = asyncio.get_event_loop()
    sh = await loop.run_in_executor(None, lambda: open_sheet_by_url(credentials_path, sheet_url))
    added_candidates = 0
    added_users = 0
    # Кандидаты
    try:
        ws_candidates = sh.worksheet("Кандидаты")
        rows = ws_candidates.get_all_values()[1:]
        for row in rows:
            if len(row) < 3:
                continue
            first_name, last_name, vk_id = row[:3]
            candidate_exists = await session.execute(select(Candidate).where(Candidate.vk_id == vk_id))
            if candidate_exists.scalar_one_or_none():
                continue
            # faculty_id определяем по таблице (ищем faculty по url)
            faculty_result = await session.execute(select(Faculty).where(Faculty.google_sheet_url == sheet_url))
            faculty = faculty_result.scalar_one_or_none()
            if not faculty:
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
        return (added_candidates, added_users, f"Ошибка чтения листа 'Кандидаты': {e}")
    # Собесеры
    for sheet_name, role in [("Опытные собесеры", Role.EXPERIENCED.value), ("Не опытные собесеры", Role.NEWBIE.value)]:
        try:
            ws = sh.worksheet(sheet_name)
            rows = ws.get_all_values()[1:]
            for row in rows:
                if len(row) < 2:
                    continue
                login, password = row[:2]
                login = login.strip()
                user_exists = await session.execute(select(User).where(User.username == login))
                if user_exists.scalar_one_or_none():
                    continue
                faculty_result = await session.execute(select(Faculty).where(Faculty.google_sheet_url == sheet_url))
                faculty = faculty_result.scalar_one_or_none()
                if not faculty:
                    continue
                user = User(
                    username=login,
                    password_hash=bcrypt.hash(password.strip()),
                    faculty_id=faculty.id,
                    role=role,
                    is_active=True
                )
                session.add(user)
                await session.flush()
                added_users += 1
        except Exception as e:
            return (added_candidates, added_users, f"Ошибка чтения листа '{sheet_name}': {e}")
    await session.commit()
    return (added_candidates, added_users, None)