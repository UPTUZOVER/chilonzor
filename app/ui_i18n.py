from threading import local

from django.utils.functional import lazy

from .ui_i18n_en import EN_TRANSLATIONS


DEFAULT_UI_LANGUAGE = "uz"
UI_LANGUAGE_SESSION_KEY = "ui_language"
SUPPORTED_UI_LANGUAGES = (
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
)
SUPPORTED_UI_LANGUAGE_CODES = {code for code, _ in SUPPORTED_UI_LANGUAGES}

_state = local()


TRANSLATIONS = {
    "Admin": {
        "ru": "Админ",
    },
    "Admin analitika": {
        "ru": "Административная аналитика",
    },
    "Admin hali ro'yxatdan o'tish uchun guruh yaratmagan.": {
        "ru": "Администратор пока не создал группу для регистрации.",
    },
    "Admin huquqi": {
        "ru": "Права администратора",
    },
    "Admin sifatida barcha ishlarni va kuzatuvchi holatlarini boshqarasiz. Diagrammalar alohida dashboard sahifasida turadi.": {
        "ru": "Как администратор вы управляете всеми работами и статусами наблюдателя. Диаграммы доступны на отдельной странице панели.",
    },
    "Admin user va guruhlarni boshqaradi, oddiy user esa ro'yxatdan o'tib o'z guruhini tanlay oladi.": {
        "ru": "Администратор управляет пользователями и группами, а обычный пользователь может зарегистрироваться и выбрать свою группу.",
    },
    "Akkauntingiz bormi?": {
        "ru": "У вас уже есть аккаунт?",
    },
    "Akkauntingiz yo'qmi?": {
        "ru": "У вас нет аккаунта?",
    },
    "Amal": {
        "ru": "Действие",
    },
    "Auth": {
        "ru": "Авторизация",
    },
    "Barcha foydalanuvchilar": {
        "ru": "Все пользователи",
    },
    "Barcha foydalanuvchilar uchun": {
        "ru": "Для всех пользователей",
    },
    "Barcha guruhlar": {
        "ru": "Все группы",
    },
    "Barcha holatlar": {
        "ru": "Все статусы",
    },
    "Barcha ijtimoiy tarmoqlar": {
        "ru": "Все соцсети",
    },
    "Barcha kategoriyalar": {
        "ru": "Все категории",
    },
    "Barcha userlarni ko'rishingiz va boshqarishingiz mumkin.": {
        "ru": "Вы можете просматривать и управлять всеми пользователями.",
    },
    "Bo'sh qoldirilsa o'zgarmaydi": {
        "ru": "Если оставить пустым, не изменится",
    },
    "Bu bo'lim faqat admin uchun.": {
        "ru": "Этот раздел доступен только администратору.",
    },
    "Bu IP manzil {failure_limit} marta xato urinish sabab {lockout_hours} soatga bloklangan. Qayta kirish vaqti: {blocked_until}.": {
        "ru": "Этот IP-адрес заблокирован на {lockout_hours} ч. из-за {failure_limit} неудачных попыток. Повторный вход будет доступен: {blocked_until}.",
    },
    "Bu login band, boshqasini kiriting.": {
        "ru": "Этот логин уже занят, введите другой.",
    },
    "Bu nomdagi guruh allaqachon mavjud.": {
        "ru": "Группа с таким названием уже существует.",
    },
    "Bu yerda faqat o'zingiz va guruhingizdagi userlar ko'rinadi.": {
        "ru": "Здесь отображаетесь только вы и пользователи из вашей группы.",
    },
    "Bu yerda lichka xabarlar va hammaga yuborilgan e'lonlar bir oqimda ko'rinadi.": {
        "ru": "Здесь в одном потоке отображаются личные сообщения и объявления для всех.",
    },
    "Bu yerda o'zingiz va guruhingizdagi ishlar ko'rinadi. Oddiy foydalanuvchi kuzatuvchi holatini o'zgartira olmaydi.": {
        "ru": "Здесь отображаются ваши работы и работы вашей группы. Обычный пользователь не может менять статус наблюдателя.",
    },
    "Category": {
        "ru": "Категория",
    },
    "Category A-Z": {
        "ru": "Категория A-Z",
    },
    "Category Z-A": {
        "ru": "Категория Z-A",
    },
    "Category tanlanishi shart.": {
        "ru": "Необходимо выбрать категорию.",
    },
    "Chiqish": {
        "ru": "Выйти",
    },
    "Darhol ishlash": {
        "ru": "Мгновенный старт",
    },
    "Dashboard": {
        "ru": "Панель",
    },
    "Delete": {
        "ru": "Удалить",
    },
    "Description": {
        "ru": "Описание",
    },
    "Edit": {
        "ru": "Изменить",
    },
    "Eng eski": {
        "ru": "Сначала старые",
    },
    "Eng yangi": {
        "ru": "Сначала новые",
    },
    "Faqat ko'rish": {
        "ru": "Только просмотр",
    },
    "Familiya": {
        "ru": "Фамилия",
    },
    "Faollik hali boshlanmagan.": {
        "ru": "Активность пока не началась.",
    },
    "Forma": {
        "ru": "Форма",
    },
    "Foydalanuvchi": {
        "ru": "Пользователь",
    },
    "Foydalanuvchi {pk}": {
        "ru": "Пользователь {pk}",
    },
    "Group": {
        "ru": "Группа",
    },
    "Group / End": {
        "ru": "Группа / завершение",
    },
    "Group / Start": {
        "ru": "Группа / начало",
    },
    "Guruh": {
        "ru": "Группа",
    },
    "Guruh nomi": {
        "ru": "Название группы",
    },
    "Guruh o'chirildi.": {
        "ru": "Группа удалена.",
    },
    "Guruh yangilandi.": {
        "ru": "Группа обновлена.",
    },
    "Guruh yo'q": {
        "ru": "Нет группы",
    },
    "Guruhlar": {
        "ru": "Группы",
    },
    "Guruhlarni boshqarish": {
        "ru": "Управление группами",
    },
    "Guruhni Tahrirlash": {
        "ru": "Редактирование группы",
    },
    "Guruhni tanlang": {
        "ru": "Выберите группу",
    },
    "Guruhsiz": {
        "ru": "Без группы",
    },
    "Hali ma'lumot yo'q.": {
        "ru": "Пока нет данных.",
    },
    "Hamma foydalanuvchi, guruh va ishlar bitta joyda boshqariladi.": {
        "ru": "Все пользователи, группы и работы управляются в одном месте.",
    },
    "Hammaga e'lon": {
        "ru": "Объявление для всех",
    },
    "Hammaga e'lon yuborildi.": {
        "ru": "Объявление для всех отправлено.",
    },
    "Hammaga yoki istalgan foydalanuvchiga yozish": {
        "ru": "Написать всем или любому пользователю",
    },
    "Har bir foydalanuvchi ro'yxatdan o'tib, o'z guruhiga mos ma'lumot bilan ishlaydi.": {
        "ru": "Каждый пользователь регистрируется и работает с данными своей группы.",
    },
    "Har kuni `Ish yakunlandi` ga o'tgan ishlar soni.": {
        "ru": "Количество работ, переведённых в статус `Работа завершена` за каждый день.",
    },
    "Havola": {
        "ru": "Ссылка",
    },
    "Havola oldin kiritilgan, takror bo'lishi mumkin emas.": {
        "ru": "Эта ссылка уже была добавлена, повторение недопустимо.",
    },
    "Holat": {
        "ru": "Статус",
    },
    "Holatni yangilash: {name}": {
        "ru": "Обновление статуса: {name}",
    },
    "Holatlar": {
        "ru": "Статусы",
    },
    "Holatlar taqsimoti": {
        "ru": "Распределение статусов",
    },
    "Hozircha group yo'q.": {
        "ru": "Пока нет групп.",
    },
    "Hozircha ish yo'q.": {
        "ru": "Пока нет работ.",
    },
    "Hozircha ma'lumot yo'q.": {
        "ru": "Пока нет данных.",
    },
    "Hozircha tanlash uchun ochiq guruh yo'q.": {
        "ru": "Пока нет открытых групп для выбора.",
    },
    "Hozircha user yo'q.": {
        "ru": "Пока нет пользователей.",
    },
    "Hozircha xabar yo'q.": {
        "ru": "Пока нет сообщений.",
    },
    "Ijtimoiy tarmoq": {
        "ru": "Соцсеть",
    },
    "Ijtimoiy tarmoqlar": {
        "ru": "Соцсети",
    },
    "Ish": {
        "ru": "Работа",
    },
    "Ish boshlandi": {
        "ru": "Работа начата",
    },
    "Ish boshlandi hujjati": {
        "ru": "Документ о начале работы",
    },
    "Ish boshlandi uchun fayl yuklash majburiy.": {
        "ru": "Для статуса `Работа начата` необходимо загрузить файл.",
    },
    "Ish boshlandi tanlansa, ish boshlanganini tasdiqlovchi fayl yuklanadi.": {
        "ru": "При выборе статуса `Работа начата` загружается файл, подтверждающий начало работы.",
    },
    "Ish yakunlandi": {
        "ru": "Работа завершена",
    },
    "Ish yakunlandi hujjati": {
        "ru": "Документ о завершении работы",
    },
    "Ish yakunlandi uchun fayl yuklash majburiy.": {
        "ru": "Для статуса `Работа завершена` необходимо загрузить файл.",
    },
    "Ish yakunlandi tanlansa, ish yakunlanganini tasdiqlovchi fayl yuklanadi.": {
        "ru": "При выборе статуса `Работа завершена` загружается файл, подтверждающий завершение работы.",
    },
    "Ish ko'pdan kamga": {
        "ru": "Работ больше -> меньше",
    },
    "Ish kamdan ko'pga": {
        "ru": "Работ меньше -> больше",
    },
    "Ish qo'shish": {
        "ru": "Добавление работы",
    },
    "Ish o'chirildi.": {
        "ru": "Работа удалена.",
    },
    "Ish yangilandi.": {
        "ru": "Работа обновлена.",
    },
    "Ishlarga qaytish": {
        "ru": "Вернуться к работам",
    },
    "Ishlar": {
        "ru": "Работы",
    },
    "Ishlar ro'yxati": {
        "ru": "Список работ",
    },
    "Ishlar tizimi": {
        "ru": "Система работ",
    },
    "Ishlar, kuzatuvchi holatlari va asosiy faollik bir ekranda jamlandi.": {
        "ru": "Работы, статусы наблюдателя и основная активность собраны на одном экране.",
    },
    "Ism": {
        "ru": "Имя",
    },
    "Kategoriya": {
        "ru": "Категория",
    },
    "Kesim": {
        "ru": "Срез",
    },
    "Kimga": {
        "ru": "Кому",
    },
    "Kirish": {
        "ru": "Вход",
    },
    "Ko'rib chiqilmagan": {
        "ru": "Не рассмотрено",
    },
    "Ko'k ustunlar yangi yuklangan ishlar, oq chiziq esa kuzatuvchi tomonidan ko'rib chiqilganlar soni.": {
        "ru": "Синие столбцы показывают новые загруженные работы, а белая линия количество просмотренных наблюдателем.",
    },
    "Ko'rish": {
        "ru": "Просмотр",
    },
    "Kutishda": {
        "ru": "Ожидание",
    },
    "Kuzatuvchi": {
        "ru": "Наблюдатель",
    },
    "Kuzatuvchi guruhi o'zgartirilmaydi.": {
        "ru": "Группу наблюдателя нельзя изменять.",
    },
    "Kuzatuvchi guruhini o'chirish yopiq.": {
        "ru": "Удаление группы наблюдателя запрещено.",
    },
    "Kuzatuvchi himoyalangan": {
        "ru": "Наблюдатель защищён",
    },
    "Kuzatuvchi holati": {
        "ru": "Статус наблюдателя",
    },
    "Kuzatuvchi holati yangilandi.": {
        "ru": "Статус наблюдателя обновлён.",
    },
    "Kuzatuvchi ko'rib chiqqanlar: {count}": {
        "ru": "Просмотрено наблюдателем: {count}",
    },
    "Kuzatuvchi sifatida ishlarni ko'rasiz va ularga `Ish boshlandi`, `Ish yakunlandi`, `Kutishda` holatini berasiz.": {
        "ru": "Как наблюдатель вы видите работы и можете присваивать им статусы `Работа начата`, `Работа завершена`, `Ожидание`.",
    },
    "Kuzatuvchi statuslari ulushi.": {
        "ru": "Доля статусов наблюдателя.",
    },
    "Lichka xabar": {
        "ru": "Личное сообщение",
    },
    "Lichka xabarlar ham, hammaga yuborilgan e'lonlar ham shu yerda saqlanadi.": {
        "ru": "Здесь хранятся и личные сообщения, и объявления для всех.",
    },
    "Login": {
        "ru": "Логин",
    },
    "Login biriktirilmagan": {
        "ru": "Логин не привязан",
    },
    "Login va parol noto'g'ri.": {
        "ru": "Логин или пароль указаны неверно.",
    },
    "Login yoki parol xato. Qolgan urinishlar: {remaining_attempts}.": {
        "ru": "Логин или пароль неверны. Осталось попыток: {remaining_attempts}.",
    },
    "Login va parolni kiriting.": {
        "ru": "Введите логин и пароль.",
    },
    "Ma'lumotlarni kiriting va guruhni tanlang.": {
        "ru": "Введите данные и выберите группу.",
    },
    "Manba": {
        "ru": "Источник",
    },
    "Masalan: Alpha Team": {
        "ru": "Например: Alpha Team",
    },
    "Maxsus tizim guruhi": {
        "ru": "Специальная системная группа",
    },
    "Mening threadim": {
        "ru": "Мой тред",
    },
    "Mening xabarlarim": {
        "ru": "Мои сообщения",
    },
    "Muddat: {date}": {
        "ru": "Срок: {date}",
    },
    "Muddati o'tgan": {
        "ru": "Срок истёк",
    },
    "Noma'lum": {
        "ru": "Неизвестно",
    },
    "Noto'g'ri JSON yuborildi.": {
        "ru": "Отправлен некорректный JSON.",
    },
    "Oddiy foydalanuvchi": {
        "ru": "Обычный пользователь",
    },
    "O'qish yopiq.": {
        "ru": "Отслеживание отключено.",
    },
    "O'zingiz ro'yxatdan o'ting va guruhingizni tanlang": {
        "ru": "Зарегистрируйтесь самостоятельно и выберите свою группу",
    },
    "Oddiy foydalanuvchi kuzatuvchi holatini o'zgartira olmaydi.": {
        "ru": "Обычный пользователь не может менять статус наблюдателя.",
    },
    "Oson boshlash": {
        "ru": "Лёгкий старт",
    },
    "Ortga": {
        "ru": "Назад",
    },
    "Parol": {
        "ru": "Пароль",
    },
    "Parol juda o'xshash.": {
        "ru": "Пароль слишком похож на личные данные.",
    },
    "Parol juda qisqa. Kamida {min_length} ta belgidan iborat bo'lishi kerak.": {
        "ru": "Пароль слишком короткий. Он должен содержать минимум {min_length} символов.",
    },
    "Parol juda oddiy.": {
        "ru": "Пароль слишком простой.",
    },
    "Parol faqat raqamlardan iborat bo'lmasligi kerak.": {
        "ru": "Пароль не должен состоять только из цифр.",
    },
    "Parolni qayta kiriting": {
        "ru": "Повторите пароль",
    },
    "Parolni tasdiqlang": {
        "ru": "Подтвердите пароль",
    },
    "Parollar bir xil emas.": {
        "ru": "Пароли не совпадают.",
    },
    "Qidirish": {
        "ru": "Поиск",
    },
    "Qisqa tavsif": {
        "ru": "Краткое описание",
    },
    "Qizil nazorat ostida": {
        "ru": "Под красным контролем",
    },
    "Rasm": {
        "ru": "Изображение",
    },
    "Rasm yo'q": {
        "ru": "Нет изображения",
    },
    "Recipient bo'sh qolsa xabar hammaga ketadi.": {
        "ru": "Если получатель не выбран, сообщение отправится всем.",
    },
    "Register": {
        "ru": "Регистрация",
    },
    "Rol: Guruh": {
        "ru": "Роль: Группа",
    },
    "Ro'yxatdan o'tganingizdan keyin tizimga avtomatik kirasiz.": {
        "ru": "После регистрации вы автоматически входите в систему.",
    },
    "Ro'yxatdan o'tish": {
        "ru": "Регистрация",
    },
    "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi.": {
        "ru": "Регистрация успешно завершена.",
    },
    "Saqlash": {
        "ru": "Сохранить",
    },
    "Sana": {
        "ru": "Дата",
    },
    "Saralash": {
        "ru": "Сортировка",
    },
    "Shaxsiy kirish": {
        "ru": "Личный доступ",
    },
    "Social Media": {
        "ru": "Соцсеть",
    },
    "Social Media tanlanishi shart.": {
        "ru": "Необходимо выбрать соцсеть.",
    },
    "Social media": {
        "ru": "Соцсеть",
    },
    "So'nggi 14 kun": {
        "ru": "Последние 14 дней",
    },
    "So'nggi 14 kunlik oqim": {
        "ru": "Динамика за последние 14 дней",
    },
    "So'nggi haftada {count} taga kamaygan.": {
        "ru": "За последнюю неделю уменьшилось на {count}.",
    },
    "So'nggi haftada {count} taga ko'paygan.": {
        "ru": "За последнюю неделю увеличилось на {count}.",
    },
    "So'nggi ikki hafta bir xil tempda ketmoqda.": {
        "ru": "Последние две недели идут в одинаковом темпе.",
    },
    "Start va yakun faolligi": {
        "ru": "Активность по началу и завершению",
    },
    "Tavsif": {
        "ru": "Описание",
    },
    "Tavsif kiritilmagan.": {
        "ru": "Описание не указано.",
    },
    "Threadlar": {
        "ru": "Треды",
    },
    "Til": {
        "ru": "Язык",
    },
    "Tizimga xavfsiz va qulay kirish": {
        "ru": "Безопасный и удобный вход в систему",
    },
    "To'liq ko'rish": {
        "ru": "Показать полностью",
    },
    "Tozalash": {
        "ru": "Сбросить",
    },
    "Umumiy ko'rinish": {
        "ru": "Общий обзор",
    },
    "User": {
        "ru": "Пользователь",
    },
    "User A-Z": {
        "ru": "Пользователь A-Z",
    },
    "User count bo'yicha": {
        "ru": "По количеству работ пользователя",
    },
    "User o'chirildi.": {
        "ru": "Пользователь удалён.",
    },
    "User work count": {
        "ru": "Количество работ пользователя",
    },
    "User yangilandi.": {
        "ru": "Пользователь обновлён.",
    },
    "Userlar": {
        "ru": "Пользователи",
    },
    "Userlar ro'yxati": {
        "ru": "Список пользователей",
    },
    "Wait": {
        "ru": "Ожидание",
    },
    "Xabar": {
        "ru": "Сообщение",
    },
    "Xabar matni bo'sh bo'lmasligi kerak.": {
        "ru": "Текст сообщения не должен быть пустым.",
    },
    "Xabar matnini kiriting": {
        "ru": "Введите текст сообщения",
    },
    "Xabar yuborish faqat admin uchun.": {
        "ru": "Отправка сообщений доступна только администратору.",
    },
    "Xabarlar": {
        "ru": "Сообщения",
    },
    "Xabarlar markazi": {
        "ru": "Центр сообщений",
    },
    "Xabarlarim": {
        "ru": "Мои сообщения",
    },
    "Xavfsiz chiqish": {
        "ru": "Безопасный выход",
    },
    "Yangilangan: {date}": {
        "ru": "Обновлено: {date}",
    },
    "Yangilash": {
        "ru": "Обновить",
    },
    "Yangi Ish": {
        "ru": "Новая работа",
    },
    "Yangi Guruh": {
        "ru": "Новая группа",
    },
    "Yangi User": {
        "ru": "Новый пользователь",
    },
    "Yangi parol": {
        "ru": "Новый пароль",
    },
    "Yangi foydalanuvchi": {
        "ru": "Новый пользователь",
    },
    "Yangi foydalanuvchi qo'shish": {
        "ru": "Добавить нового пользователя",
    },
    "Yangi guruh": {
        "ru": "Новая группа",
    },
    "Yangi guruh qo'shildi.": {
        "ru": "Новая группа добавлена.",
    },
    "Yangi ish": {
        "ru": "Новая работа",
    },
    "Yangi ish qo'shildi.": {
        "ru": "Новая работа добавлена.",
    },
    "Yangi ishlar: {count}": {
        "ru": "Новые работы: {count}",
    },
    "Yangi login uchun parol kiritilishi kerak.": {
        "ru": "Для нового логина необходимо указать пароль.",
    },
    "Yangi user": {
        "ru": "Новый пользователь",
    },
    "Yangi user qo'shildi.": {
        "ru": "Новый пользователь добавлен.",
    },
    "Yakunlangan": {
        "ru": "Завершено",
    },
    "Yakunlangan ishlar": {
        "ru": "Завершённые работы",
    },
    "Yakunlash trendi": {
        "ru": "Тренд завершения",
    },
    "Yuklash kesimlari": {
        "ru": "Срезы загрузки",
    },
    "aniq emas": {
        "ru": "не указано",
    },
    "barcha foydalanuvchilar": {
        "ru": "все пользователи",
    },
    "jami ish": {
        "ru": "всего работ",
    },
    "ta foydalanuvchi biriktirilgan": {
        "ru": "пользователей привязано",
    },
    "ta ish": {
        "ru": "работ",
    },
    "work_ids ro'yxat bo'lishi kerak.": {
        "ru": "work_ids должен быть списком.",
    },
    "Admin foydalanuvchi va guruhlarni boshqaradi, oddiy foydalanuvchi esa ro'yxatdan o'tib o'z guruhini tanlay oladi.": {
        "ru": "Администратор управляет пользователями и группами, а обычный пользователь может зарегистрироваться и выбрать свою группу.",
    },
    "Admin yaratgan guruhlardan birini tanlab, tizimga mustaqil kirishingiz mumkin.": {
        "ru": "Вы можете самостоятельно войти в систему, выбрав одну из групп, созданных администратором.",
    },
    "Barcha foydalanuvchilarni ko'rishingiz va boshqarishingiz mumkin.": {
        "ru": "Вы можете просматривать и управлять всеми пользователями.",
    },
    "Barcha yuklangan ishlar": {
        "ru": "Все загруженные работы",
    },
    "Bu yerda faqat o'zingiz va guruhingizdagi foydalanuvchilar ko'rinadi.": {
        "ru": "Здесь отображаетесь только вы и пользователи из вашей группы.",
    },
    "Foydalanuvchi A-Z": {
        "ru": "Пользователь A-Z",
    },
    "Foydalanuvchi ishlar soni": {
        "ru": "Количество работ пользователя",
    },
    "Foydalanuvchi o'chirildi.": {
        "ru": "Пользователь удалён.",
    },
    "Foydalanuvchi o'chirilsinmi?": {
        "ru": "Удалить пользователя?",
    },
    "Foydalanuvchi yangilandi.": {
        "ru": "Пользователь обновлён.",
    },
    "Foydalanuvchini tahrirlash": {
        "ru": "Редактирование пользователя",
    },
    "Foydalanuvchilar": {
        "ru": "Пользователи",
    },
    "Foydalanuvchilar ro'yxati": {
        "ru": "Список пользователей",
    },
    "Guruh o'chirilsinmi?": {
        "ru": "Удалить группу?",
    },
    "Guruh tanlash": {
        "ru": "Выбор группы",
    },
    "Hozircha foydalanuvchi yo'q.": {
        "ru": "Пока нет пользователей.",
    },
    "Hozircha guruh yo'q.": {
        "ru": "Пока нет групп.",
    },
    "Ish holatini faqat kuzatuvchi yoki admin boshqara oladi.": {
        "ru": "Статус работы может изменять только наблюдатель или администратор.",
    },
    "Ish o'chirilsinmi?": {
        "ru": "Удалить работу?",
    },
    "Ishni tahrirlash": {
        "ru": "Редактирование работы",
    },
    "Ism A-Z": {
        "ru": "Имя A-Z",
    },
    "Ism Z-A": {
        "ru": "Имя Z-A",
    },
    "Jarayonga olingan ishlar": {
        "ru": "Работы, взятые в процесс",
    },
    "Kiruvchi xabarlar": {
        "ru": "Входящие сообщения",
    },
    "Kutish holatidagi ishlar": {
        "ru": "Работы в ожидании",
    },
    "Kuzatuvchi roli uchun ish qo'shish yopiq.": {
        "ru": "Добавление работ для роли наблюдателя закрыто.",
    },
    "Login, ism, familiya va parol bilan tez ro'yxatdan o'tasiz.": {
        "ru": "Вы быстро зарегистрируетесь с помощью логина, имени, фамилии и пароля.",
    },
    "Ro'yxatdan o'tishda biriktiriladigan guruhni o'zingiz tanlaysiz.": {
        "ru": "Во время регистрации вы сами выбираете группу, к которой будете привязаны.",
    },
    "Suhbatlar": {
        "ru": "Диалоги",
    },
    "Xabar {recipient} ga yuborildi.": {
        "ru": "Сообщение отправлено пользователю {recipient}.",
    },
    "Yangi foydalanuvchi": {
        "ru": "Новый пользователь",
    },
    "Yangi foydalanuvchi qo'shildi.": {
        "ru": "Новый пользователь добавлен.",
    },
    "Yangi xabar": {
        "ru": "Новое сообщение",
    },
    "Yuborish": {
        "ru": "Отправить",
    },
    "{count} ta foydalanuvchi biriktirilgan": {
        "ru": "Привязано пользователей: {count}",
    },
    "{count} ta ish": {
        "ru": "Работ: {count}",
    },
    "{name} uchun lichka": {
        "ru": "Личка для {name}",
    },
    "{name} uchun yozish": {
        "ru": "Написать для {name}",
    },
    "Eng faol kun": {
        "ru": "Самый активный день",
    },
    "Nuqtalar va silliq chiziq so'nggi 14 kun ichida yuklangan ishlar ritmini ko'rsatadi.": {
        "ru": "Точки и плавная линия показывают ритм загрузки работ за последние 14 дней.",
    },
    "Kategoriyalar bo'yicha 14 kunlik oqim": {
        "ru": "14-дневный поток по категориям",
    },
    "Eng faol kategoriyalar kunlar kesimida alohida chiziq sifatida ko'rsatiladi.": {
        "ru": "Самые активные категории показаны отдельными линиями по дням.",
    },
    "Eng faol kategoriya: {category} ({count} ta).": {
        "ru": "Самая активная категория: {category} ({count} шт.).",
    },
    "Eng yuqori nuqta": {
        "ru": "Пиковая точка",
    },
}

TRANSLATIONS.update(
    {
        "Ko'rsatilmoqda: {count} ta ish": {
            "ru": "\u041f\u043e\u043a\u0430\u0437\u0430\u043d\u043e: {count} \u0440\u0430\u0431\u043e\u0442",
        },
        "Jami: {count} ta ish": {
            "ru": "\u0412\u0441\u0435\u0433\u043e: {count} \u0440\u0430\u0431\u043e\u0442",
        },
        "Ko'rsatilmoqda: {count} ta foydalanuvchi": {
            "ru": "\u041f\u043e\u043a\u0430\u0437\u0430\u043d\u043e: {count} \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f",
        },
        "Jami: {count} ta foydalanuvchi": {
            "ru": "\u0412\u0441\u0435\u0433\u043e: {count} \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f",
        },
        "Karta kategoriyasi": {
            "ru": "\u041a\u0430\u0440\u0442\u043e\u0447\u043d\u0430\u044f \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f",
        },
        "Karta kategoriyalari": {
            "ru": "\u041a\u0430\u0440\u0442\u043e\u0447\u043d\u044b\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438",
        },
        "Xarita viloyati": {
            "ru": "\u041e\u0431\u043b\u0430\u0441\u0442\u044c \u043d\u0430 \u043a\u0430\u0440\u0442\u0435",
        },
        "Xarita viloyatlari": {
            "ru": "\u041e\u0431\u043b\u0430\u0441\u0442\u0438 \u043d\u0430 \u043a\u0430\u0440\u0442\u0435",
        },
        "Xarita tumani": {
            "ru": "\u0420\u0430\u0439\u043e\u043d \u043d\u0430 \u043a\u0430\u0440\u0442\u0435",
        },
        "Xarita tumanlari": {
            "ru": "\u0420\u0430\u0439\u043e\u043d\u044b \u043d\u0430 \u043a\u0430\u0440\u0442\u0435",
        },
        "Tuman bo'yicha jinoyat statistikasi": {
            "ru": "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u043f\u0440\u0435\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u0439 \u043f\u043e \u0440\u0430\u0439\u043e\u043d\u0443",
        },
        "Rang HEX formatida bo'lishi kerak. Masalan: #23b383": {
            "ru": "\u0426\u0432\u0435\u0442 \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0432 HEX-\u0444\u043e\u0440\u043c\u0430\u0442\u0435. \u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: #23b383",
        },
    }
)

for _translation_key, _translation_value in EN_TRANSLATIONS.items():
    TRANSLATIONS.setdefault(_translation_key, {})["en"] = _translation_value

del _translation_key, _translation_value


PASSWORD_ERROR_TRANSLATIONS = {
    "password_too_short": "Parol juda qisqa. Kamida {min_length} ta belgidan iborat bo'lishi kerak.",
    "password_too_common": "Parol juda oddiy.",
    "password_entirely_numeric": "Parol faqat raqamlardan iborat bo'lmasligi kerak.",
    "password_too_similar": "Parol juda o'xshash.",
}


def normalize_language(language):
    if language in SUPPORTED_UI_LANGUAGE_CODES:
        return language
    return DEFAULT_UI_LANGUAGE


def get_current_language():
    return normalize_language(getattr(_state, "language", DEFAULT_UI_LANGUAGE))


def set_current_language(language):
    _state.language = normalize_language(language)


def clear_current_language():
    if hasattr(_state, "language"):
        delattr(_state, "language")


def get_language_from_request(request):
    if request is None:
        return DEFAULT_UI_LANGUAGE

    session = getattr(request, "session", None)
    if session is not None:
        return normalize_language(session.get(UI_LANGUAGE_SESSION_KEY))
    return DEFAULT_UI_LANGUAGE


def translate(text, language=None, **kwargs):
    language = normalize_language(language or get_current_language())
    translated = TRANSLATIONS.get(text, {}).get(language, text)
    if kwargs:
        return translated.format(**kwargs)
    return translated


lazy_translate = lazy(translate, str)


def get_language_options():
    return [
        {
            "code": code,
            "label": label,
        }
        for code, label in SUPPORTED_UI_LANGUAGES
    ]


def display_group_name(name):
    normalized_name = str(name or "").strip()
    if normalized_name.casefold() == "watcher":
        return translate("Kuzatuvchi")
    return normalized_name


def display_role_name(name):
    role_map = {
        "Admin": "Admin",
        "User": "Foydalanuvchi",
        "Watcher": "Kuzatuvchi",
        "Foydalanuvchi": "Foydalanuvchi",
        "Kuzatuvchi": "Kuzatuvchi",
    }
    return translate(role_map.get(str(name or "").strip(), str(name or "").strip()))


def display_status_name(value):
    status_map = {
        "pending": "Ko'rib chiqilmagan",
        "start_work": "Ish boshlandi",
        "end_work": "Ish yakunlandi",
        "wait": "Kutishda",
        "overdue": "Muddati o'tgan",
        "Ko'rib chiqilmagan": "Ko'rib chiqilmagan",
        "Ish boshlandi": "Ish boshlandi",
        "Ish yakunlandi": "Ish yakunlandi",
        "Kutishda": "Kutishda",
        "Muddati o'tgan": "Muddati o'tgan",
        "Start Work": "Ish boshlandi",
        "End Work": "Ish yakunlandi",
        "Wait": "Kutishda",
        "Muddat o'tgan": "Muddati o'tgan",
    }
    return translate(status_map.get(str(value or "").strip(), str(value or "").strip()))


_ONES_WORDS = ["", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
_TENS_WORDS = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]
_SCALE_WORDS = ((10**9, "milliard"), (10**6, "million"), (10**3, "ming"))


def _three_digits_to_words(number):
    words = []
    hundreds, remainder = divmod(number, 100)
    if hundreds:
        words.append("yuz" if hundreds == 1 else f"{_ONES_WORDS[hundreds]} yuz")
    tens, ones = divmod(remainder, 10)
    if tens:
        words.append(_TENS_WORDS[tens])
    if ones:
        words.append(_ONES_WORDS[ones])
    return " ".join(words)


def number_to_uzbek_words(value):
    """1200000 -> "bir million ikki yuz ming" turida so'z bilan yozadi."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return ""

    if number == 0:
        return "nol"

    is_negative = number < 0
    number = abs(number)

    groups = []
    for scale_value, scale_name in _SCALE_WORDS:
        if number >= scale_value:
            group, number = divmod(number, scale_value)
            group_words = _three_digits_to_words(group)
            if scale_name == "ming" and group == 1:
                groups.append("ming")
            else:
                groups.append(f"{group_words} {scale_name}")
    if number:
        groups.append(_three_digits_to_words(number))

    words = " ".join(groups)
    return f"minus {words}" if is_negative else words


def translate_password_validation_errors(exc):
    translated_errors = []
    for error in exc.error_list:
        template = PASSWORD_ERROR_TRANSLATIONS.get(error.code)
        if template:
            translated_errors.append(translate(template, **(error.params or {})))
        else:
            translated_errors.append(translate(error.message, **(error.params or {})))
    return translated_errors
