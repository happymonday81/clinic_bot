from typing import Dict

# ========== ПЕРЕВОДЫ ==========
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ========== КНОПКИ МЕНЮ ==========
    'btn_appointment': {
        'ru': '📝 Записаться на приём',
        'en': '📝 Book appointment',
        'zh': '📝 预约就诊'
    },
    'btn_my_appointments': {
        'ru': '📋 Мои записи',
        'en': '📋 My appointments',
        'zh': '📋 我的预约'
    },
    'btn_about': {
        'ru': 'ℹ️ О клинике',
        'en': 'ℹ️ About clinic',
        'zh': 'ℹ️ 关于诊所'
    },
    'btn_contacts': {
        'ru': '📞 Контакты',
        'en': '📞 Contacts',
        'zh': '📞 联系方式'
    },
    'btn_back_to_menu': {
        'ru': '🏠 Вернуться в главное меню',
        'en': '🏠 Back to main menu',
        'zh': '🏠 返回主菜单'
    },
    'btn_back': {
        'ru': '🔙 Назад',
        'en': '🔙 Back',
        'zh': '🔙 返回'
    },
    
    # ========== ПРИВЕТСТВИЯ ==========
    'welcome': {
        'ru': 'Добро пожаловать в нашу клинику!\n\nВыберите действие в меню:',
        'en': 'Welcome to our clinic!\n\nSelect an action from the menu:',
        'zh': '欢迎来到我们的诊所！\n\n请从菜单中选择操作：'
    },
    
    # ========== ЗАПИСЬ ==========
    'select_doctor': {
        'ru': 'Выберите врача:',
        'en': 'Select a doctor:',
        'zh': '选择医生：'
    },
    'select_date': {
        'ru': 'Выберите дату:',
        'en': 'Select a date:',
        'zh': '选择日期：'
    },
    'select_time': {
        'ru': 'Выберите время:',
        'en': 'Select a time:',
        'zh': '选择时间：'
    },
    'enter_name': {
        'ru': 'Введите ваше имя:',
        'en': 'Enter your name:',
        'zh': '输入您的姓名：'
    },
    'enter_phone': {
        'ru': 'Введите ваш телефон:',
        'en': 'Enter your phone:',
        'zh': '输入您的电话：'
    },
    'you_selected_doctor': {
        'ru': 'Вы выбрали врача: {doctor}',
        'en': 'You selected doctor: {doctor}',
        'zh': '您选择的医生：{doctor}'
    },
    'you_selected_date': {
        'ru': 'Вы выбрали дату: {date}',
        'en': 'You selected date: {date}',
        'zh': '您选择的日期：{date}'
    },
    'you_selected_time': {
        'ru': 'Вы выбрали время: {time}',
        'en': 'You selected time: {time}',
        'zh': '您选择的时间：{time}'
    },
    'appointment_success': {
        'ru': '✅ Запись успешно создана!',
        'en': '✅ Appointment created successfully!',
        'zh': '✅ 预约成功创建！'
    },
    'appointment_error': {
        'ru': 'Произошла ошибка при создании записи',
        'en': 'Error creating appointment',
        'zh': '创建预约时出错'
    },
    'thanks': {
        'ru': 'Спасибо! Ждём вас в клинике.',
        'en': 'Thank you! We look forward to seeing you.',
        'zh': '谢谢！我们期待您的到来。'
    },
    
    # ========== МОИ ЗАПИСИ ==========
    'my_appointments': {
        'ru': '📋 Ваши записи:',
        'en': '📋 Your appointments:',
        'zh': '📋 您的预约：'
    },
    'no_appointments': {
        'ru': 'У вас пока нет записей',
        'en': 'You have no appointments yet',
        'zh': '您还没有预约'
    },
    
    # ========== О КЛИНИКЕ ==========
    'about': {
        'ru': '🏥 Наша клиника работает с 2010 года.\n\n👨‍⚕️ Квалифицированные врачи\n🔬 Современное оборудование\n⏰ Работаем ежедневно 9:00-20:00',
        'en': '🏥 Our clinic has been operating since 2010.\n\n👨‍⚕️ Qualified doctors\n🔬 Modern equipment\n⏰ Open daily 9:00-20:00',
        'zh': '🏥 我们的诊所自 2010 年开始运营。\n\n👨‍⚕️ 合格的医生\n🔬 现代化设备\n⏰ 每天开放 9:00-20:00'
    },
    
    # ========== КОНТАКТЫ ==========
    'contacts': {
        'ru': '📞 Телефон: +7 (999) 123-45-67\n📍 Адрес: ул. Примерная, д. 1\n🌐 Сайт: www.clinic.example.com',
        'en': '📞 Phone: +7 (999) 123-45-67\n📍 Address: Example St., 1\n🌐 Website: www.clinic.example.com',
        'zh': '📞 电话：+7 (999) 123-45-67\n📍 地址：Example St., 1\n🌐 网站：www.clinic.example.com'
    },
    
    # ========== ОШИБКИ ==========
    'error_title': {
        'ru': '❌ Ошибка',
        'en': '❌ Error',
        'zh': '❌ 错误'
    },
    'name_error': {
        'ru': 'Пожалуйста, введите ваше имя (только буквы, 2-50 символов)',
        'en': 'Please enter your name (letters only, 2-50 characters)',
        'zh': '请输入您的姓名（仅字母，2-50 个字符）'
    },
    'phone_error': {
        'ru': 'Неверный формат телефона. Введите номер в формате +7XXXXXXXXXX',
        'en': 'Invalid phone format. Enter number as +7XXXXXXXXXX',
        'zh': '电话号码格式不正确。请输入 +7XXXXXXXXXX'
    },
    'session_expired': {
        'ru': '⏰ Сессия истекла. Пожалуйста, начните заново',
        'en': '⏰ Session expired. Please start over',
        'zh': '⏰ 会话已过期。请重新开始'
    },
    'database_error': {
        'ru': 'Произошла ошибка при сохранении записи. Пожалуйста, попробуйте ещё раз',
        'en': 'Error saving appointment. Please try again',
        'zh': '保存预约时出错。请重试'
    },
    'time_conflict': {
        'ru': 'Это время уже занято. Пожалуйста, выберите другое',
        'en': 'This time slot is already booked. Please choose another',
        'zh': '该时间段已被预订。请选择其他时间'
    },
    
    # ========== ВРАЧИ ==========
    'therapist': {
        'ru': 'Терапевт',
        'en': 'Therapist',
        'zh': '治疗师'
    },
    'dentist': {
        'ru': 'Стоматолог',
        'en': 'Dentist',
        'zh': '牙医'
    },
    
    # ========== ПОЛЯ ==========
    'patient': {
        'ru': 'Пациент',
        'en': 'Patient',
        'zh': '患者'
    },
    'phone': {
        'ru': 'Телефон',
        'en': 'Phone',
        'zh': '电话'
    },
    'doctor': {
        'ru': 'Врач',
        'en': 'Doctor',
        'zh': '医生'
    },
    'date': {
        'ru': 'Дата',
        'en': 'Date',
        'zh': '日期'
    },
    'time': {
        'ru': 'Время',
        'en': 'Time',
        'zh': '时间'
    },
    
    # ========== КАЛЕНДАРЬ ==========
    'months': {
        'ru': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
        'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'zh': ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    },
    'week_days': {
        'ru': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
        'en': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'zh': ['一', '二', '三', '四', '五', '六', '日']
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """
    Получает текст перевода
    
    Args:
        lang: Код языка ('ru', 'en', 'zh')
        key: Ключ перевода
        **kwargs: Параметры для форматирования строки
    
    Returns:
        Текст перевода или ключ если не найдено
    """
    try:
        text = TRANSLATIONS.get(key, {}).get(lang, key)
        if kwargs:
            return text.format(**kwargs)
        return text
    except Exception as e:
        return key