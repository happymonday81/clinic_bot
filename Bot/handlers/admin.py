import os
from datetime import datetime
from pathlib import Path

from aiogram import Router, types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_IDS
from db import get_all_appointments
from openpyxl import Workbook

router = Router()

@router.message(lambda m: m.text == "/admin")
async def admin_panel(message: types.Message):
    """Админ-панель"""
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ У вас нет доступа к админ-панели")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Экспорт Excel", callback_data="admin_export_excel")]
    ])
    await message.answer("🛠 Админ-панель:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "admin_export_excel")
async def export_excel(callback: types.CallbackQuery):
    """Экспорт записей в Excel"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён")
        return
    
    downloads_path = str(Path.home() / "Downloads")
    
    appointments = get_all_appointments()
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "User ID", "Username", "Full Name", "Phone", "Doctor", "Date", "Time", "Status", "Created At"])
    
    for apt in appointments:
        ws.append(list(apt))
    
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H.%M")
    filename = f"Записи через бот {date_str} {time_str}.xlsx"
    filepath = os.path.join(downloads_path, filename)
    
    wb.save(filepath)
    
    document = FSInputFile(filepath)
    await callback.message.answer_document(
        document,
        caption=f"📊 Выгрузка от {now.strftime('%d.%m.%Y %H:%M')}"
    )
    
    await callback.answer("✅ Файл сохранён в Загрузки")