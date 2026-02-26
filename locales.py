# locales.py
from typing import Dict, Any

# Словарь с переводами
TRANSLATIONS = {
    'ru': {
        # Приветствие
        'welcome': "🏥 Вас приветствует бот записи к врачам в клинике CMD!\n\n"
                   "📌 Что я умею:\n"
                   "• Записывать вас на приём к специалистам\n"
                   "• Показывать ваши активные записи\n"
                   "• Давать информацию о клинике",
        
        # Кнопки меню
        'btn_appointment': "📝 Записаться на приём",
        'btn_my_appointments': "📋 Мои записи",
        'btn_about': "ℹ️ О клинике",
        'btn_contacts': "📞 Контакты",
        'btn_back': "🔙 Назад",
        'btn_back_to_menu': "🔙 В меню",
        'btn_send_contact': "📱 Отправить контакт",
        
        # Выбор врача
        'select_doctor': "👨‍⚕️ Выберите специалиста:",
        'therapist': "Терапевт",
        'dentist': "Стоматолог",
        
        # Календарь
        'select_date': "📅 Выберите дату визита:",
        'you_selected_doctor': "👨‍⚕️ Вы выбрали врача: {doctor}",
        'you_selected_date': "📅 Вы выбрали дату: {date}",
        'today': "✅{day}",
        
        # Время
        'select_time': "🕐 Выберите удобное время:",
        'you_selected_time': "🕐 Вы выбрали время: {time}",
        
        # Имя и телефон
        'enter_name': "📝 Пожалуйста, введите ваши имя и фамилию:",
        'enter_phone': "📞 Пожалуйста, введите ваш номер телефона:\n(можно отправить контакт кнопкой ниже)",
        'name_error': "❌ Пожалуйста, введите ваше имя.",
        'phone_error': "❌ Пожалуйста, введите корректный номер телефона.",
        
        # Запись
        'saving': "⏳ Сохраняем вашу запись...",
        'appointment_success': "✅ Запись успешно создана!",
        'appointment_error': "❌ Произошла ошибка при сохранении записи.",
        
        # Мои записи
        'no_appointments': "📭 У вас пока нет активных записей.",
        'my_appointments': "📋 Ваши актуальные записи:",
        
        # О клинике
        'about': "🏥 Клиника CMD\n\n"
                 "Мы заботимся о вашем здоровье уже более 10 лет!\n\n"
                 "🕒 Часы работы:\n"
                 "Пн-Пт: 8:00 - 20:00\n"
                 "Сб: 9:00 - 18:00\n"
                 "Вс: 9:00 - 16:00\n\n"
                 "📍 Адрес:\n"
                 "г. Москва, ул. Примерная, д. 123",
        
        # Контакты
        'contacts': "📞 Контакты клиники CMD\n\n"
                    "☎️ Телефон: +7 (495) 123-45-67\n"
                    "📧 Email: info@cmd-clinic.ru\n"
                    "🌐 Сайт: www.cmd-clinic.ru\n\n"
                    "📱 Telegram: @cmd_clinic",
        
        # Месяцы
        'months': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
        
        # Дни недели
        'week_days': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
        
        # Выбор языка
        'select_language': "🌐 Please select your language / 请选择语言 / Выберите язык:",
        'language_selected': "✅ Язык выбран: {lang}\n\n",
        
        # Дополнительные тексты
        'patient': "Пациент:",
        'doctor': "Врач:",
        'date': "Дата:",
        'time': "Время:",
        'phone': "Телефон:",
        'thanks': "💚 Спасибо! Мы ждём вас в клинике CMD."
    },
    
    'en': {
        # Приветствие
        'welcome': "🏥 Welcome to CMD Clinic Appointment Bot!\n\n"
                   "📌 What I can do:\n"
                   "• Book appointments with specialists\n"
                   "• Show your active appointments\n"
                   "• Provide clinic information",
        
        # Кнопки меню
        'btn_appointment': "📝 Book appointment",
        'btn_my_appointments': "📋 My appointments",
        'btn_about': "ℹ️ About clinic",
        'btn_contacts': "📞 Contacts",
        'btn_back': "🔙 Back",
        'btn_back_to_menu': "🔙 To menu",
        'btn_send_contact': "📱 Send contact",
        
        # Выбор врача
        'select_doctor': "👨‍⚕️ Select specialist:",
        'therapist': "Therapist",
        'dentist': "Dentist",
        
        # Календарь
        'select_date': "📅 Select appointment date:",
        'you_selected_doctor': "👨‍⚕️ You selected: {doctor}",
        'you_selected_date': "📅 You selected: {date}",
        'today': "✅{day}",
        
        # Время
        'select_time': "🕐 Select time:",
        'you_selected_time': "🕐 You selected: {time}",
        
        # Имя и телефон
        'enter_name': "📝 Please enter your full name:",
        'enter_phone': "📞 Please enter your phone number:\n(you can send contact using button below)",
        'name_error': "❌ Please enter your name.",
        'phone_error': "❌ Please enter a valid phone number.",
        
        # Запись
        'saving': "⏳ Saving your appointment...",
        'appointment_success': "✅ Appointment created!",
        'appointment_error': "❌ Error saving appointment.",
        
        # Мои записи
        'no_appointments': "📭 You have no active appointments.",
        'my_appointments': "📋 Your active appointments:",
        
        # О клинике
        'about': "🏥 CMD Clinic\n\n"
                 "Taking care of your health for over 10 years!\n\n"
                 "🕒 Working hours:\n"
                 "Mon-Fri: 8:00 - 20:00\n"
                 "Sat: 9:00 - 18:00\n"
                 "Sun: 9:00 - 16:00\n\n"
                 "📍 Address:\n"
                 "123 Example St., Moscow",
        
        # Контакты
        'contacts': "📞 CMD Clinic Contacts\n\n"
                    "☎️ Phone: +7 (495) 123-45-67\n"
                    "📧 Email: info@cmd-clinic.ru\n"
                    "🌐 Website: www.cmd-clinic.ru\n\n"
                    "📱 Telegram: @cmd_clinic",
        
        # Месяцы
        'months': ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December'],
        
        # Дни недели
        'week_days': ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
        
        # Выбор языка
        'select_language': "🌐 Please select your language / 请选择语言 / Выберите язык:",
        'language_selected': "✅ Language selected: {lang}\n\n",
        
        # Дополнительные тексты
        'patient': "Patient:",
        'doctor': "Doctor:",
        'date': "Date:",
        'time': "Time:",
        'phone': "Phone:",
        'thanks': "💚 Thank you! We're waiting for you at CMD Clinic."
    },
    
    'zh': {
        # Приветствие
        'welcome': "🏥 欢迎使用CMD诊所预约机器人！\n\n"
                   "📌 功能：\n"
                   "• 预约专科医生\n"
                   "• 查看您的预约\n"
                   "• 提供诊所信息",
        
        # Кнопки меню
        'btn_appointment': "📝 预约",
        'btn_my_appointments': "📋 我的预约",
        'btn_about': "ℹ️ 关于诊所",
        'btn_contacts': "📞 联系方式",
        'btn_back': "🔙 返回",
        'btn_back_to_menu': "🔙 主菜单",
        'btn_send_contact': "📱 发送联系人",
        
        # Выбор врача
        'select_doctor': "👨‍⚕️ 选择医生：",
        'therapist': "治疗师",
        'dentist': "牙医",
        
        # Календарь
        'select_date': "📅 选择预约日期：",
        'you_selected_doctor': "👨‍⚕️ 您选择了：{doctor}",
        'you_selected_date': "📅 您选择了：{date}",
        'today': "✅{day}",
        
        # Время
        'select_time': "🕐 选择时间：",
        'you_selected_time': "🕐 您选择了：{time}",
        
        # Имя и телефон
        'enter_name': "📝 请输入您的姓名：",
        'enter_phone': "📞 请输入您的电话号码：\n(您可以使用下面的按钮发送联系人)",
        'name_error': "❌ 请输入您的姓名。",
        'phone_error': "❌ 请输入有效的电话号码。",
        
        # Запись
        'saving': "⏳ 正在保存预约...",
        'appointment_success': "✅ 预约成功！",
        'appointment_error': "❌ 保存预约时出错。",
        
        # Мои записи
        'no_appointments': "📭 您目前没有预约。",
        'my_appointments': "📋 您的当前预约：",
        
        # О клинике
        'about': "🏥 CMD诊所\n\n"
                 "我们致力于您的健康超过10年！\n\n"
                 "🕒 工作时间：\n"
                 "周一至周五：8:00 - 20:00\n"
                 "周六：9:00 - 18:00\n"
                 "周日：9:00 - 16:00\n\n"
                 "📍 地址：\n"
                 "莫斯科市模范街123号",
        
        # Контакты
        'contacts': "📞 CMD诊所联系方式\n\n"
                    "☎️ 电话：+7 (495) 123-45-67\n"
                    "📧 邮箱：info@cmd-clinic.ru\n"
                    "🌐 网站：www.cmd-clinic.ru\n\n"
                    "📱 电报：@cmd_clinic",
        
        # Месяцы
        'months': ['一月', '二月', '三月', '四月', '五月', '六月',
                   '七月', '八月', '九月', '十月', '十一月', '十二月'],
        
        # Дни недели
        'week_days': ['一', '二', '三', '四', '五', '六', '日'],
        
        # Выбор языка
        'select_language': "🌐 Please select your language / 请选择语言 / Выберите язык:",
        'language_selected': "✅ 已选择语言：{lang}\n\n",
        
        # Дополнительные тексты
        'patient': "患者：",
        'doctor': "医生：",
        'date': "日期：",
        'time': "时间：",
        'phone': "电话：",
        'thanks': "💚 谢谢！CMD诊所期待您的光临。"
    }
}

# Функция для получения текста на нужном языке
def get_text(lang: str, key: str, **kwargs) -> str:
    """Получает переведённый текст с подстановкой переменных"""
    if lang not in TRANSLATIONS:
        lang = 'ru'  # По умолчанию русский
    
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['ru'].get(key, key))
    
    # Подставляем переменные, если они есть
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text