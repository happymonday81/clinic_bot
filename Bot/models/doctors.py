"""
Конфигурация врачей по специализациям.
Централизованное хранилище для масштабируемости.

Формат:
'specialty_key': {
    'name': {  # Локализованные названия специализации
        'ru': 'Терапевт',
        'en': 'Therapist',
        'zh': '治疗师'
    },
    'doctors': [  # Список врачей этой специализации
        {
            'key': 'ivanov_aa',  # Уникальный ключ для callback_data
            'name': {  # Локализованные ФИО
                'ru': 'Иванов А.А.',
                'en': 'Ivanov A.A.',
                'zh': '伊万诺夫'
            },
            'description': {  # Опционально: описание/регалии
                'ru': 'Врач высшей категории, стаж 15 лет',
                'en': 'Top category doctor, 15 years experience',
                'zh': '最高类别医生，15年经验'
            }
        },
        # ... больше врачей
    ]
}
"""

DOCTORS_CONFIG = {
    'therapist': {
        'name': {
            'ru': 'Терапевт',
            'en': 'Therapist', 
            'zh': '治疗师'
        },
        'doctors': [
            {
                'key': 'ivanov_aa',
                'name': {
                    'ru': 'Иванов А.А.',
                    'en': 'Ivanov A.A.',
                    'zh': '伊万诺夫'
                },
                'description': {
                    'ru': 'Врач высшей категории, стаж 15 лет',
                    'en': 'Top category, 15 years experience',
                    'zh': '最高类别，15年经验'
                }
            },
            {
                'key': 'petrova_bb',
                'name': {
                    'ru': 'Петрова Б.Б.',
                    'en': 'Petrova B.B.',
                    'zh': '彼得罗娃'
                },
                'description': {
                    'ru': 'Кандидат медицинских наук',
                    'en': 'Candidate of Medical Sciences',
                    'zh': '医学副博士'
                }
            },
            {
                'key': 'smirnov_cc',
                'name': {
                    'ru': 'Смирнов В.В.',
                    'en': 'Smirnov V.V.',
                    'zh': '斯米尔诺夫'
                },
                'description': {
                    'ru': 'Специалист по профилактике',
                    'en': 'Prevention specialist',
                    'zh': '预防专家'
                }
            }
        ]
    },
    
    'dentist': {
        'name': {
            'ru': 'Стоматолог',
            'en': 'Dentist',
            'zh': '牙医'
        },
        'doctors': [
            {
                'key': 'kozlov_dd',
                'name': {
                    'ru': 'Козлов Д.Д.',
                    'en': 'Kozlov D.D.',
                    'zh': '科兹洛夫'
                },
                'description': {
                    'ru': 'Хирург-имплантолог',
                    'en': 'Surgical implantologist',
                    'zh': '外科种植专家'
                }
            },
            {
                'key': 'volkova_ee',
                'name': {
                    'ru': 'Волкова Е.Е.',
                    'en': 'Volkova E.E.',
                    'zh': '沃尔科娃'
                },
                'description': {
                    'ru': 'Детский стоматолог',
                    'en': 'Pediatric dentist',
                    'zh': '儿童牙医'
                }
            }
        ]
    },
    
    'ophthalmologist': {
        'name': {
            'ru': 'Офтальмолог',
            'en': 'Ophthalmologist',
            'zh': '眼科医生'
        },
        'doctors': [
            {
                'key': 'novikov_ff',
                'name': {
                    'ru': 'Новиков Ф.Ф.',
                    'en': 'Novikov F.F.',
                    'zh': '诺维科夫'
                },
                'description': {
                    'ru': 'Лазерная коррекция зрения',
                    'en': 'Laser vision correction',
                    'zh': '激光视力矫正'
                }
            }
        ]
    }
}


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_specialty_name(specialty_key: str, lang: str = 'ru') -> str:
    """Возвращает название специализации на нужном языке"""
    specialty = DOCTORS_CONFIG.get(specialty_key)
    if not specialty:
        return specialty_key
    return specialty['name'].get(lang, specialty['name']['ru'])


def get_doctors_by_specialty(specialty_key: str) -> list:
    """Возвращает список врачей для специализации"""
    specialty = DOCTORS_CONFIG.get(specialty_key)
    if not specialty:
        return []
    return specialty['doctors']


def get_doctor_by_key(specialty_key: str, doctor_key: str) -> dict | None:
    """Находит врача по ключу внутри специализации"""
    doctors = get_doctors_by_specialty(specialty_key)
    for doctor in doctors:
        if doctor['key'] == doctor_key:
            return doctor
    return None


def get_all_specialties() -> list:
    """Возвращает список всех ключей специализаций"""
    return list(DOCTORS_CONFIG.keys())