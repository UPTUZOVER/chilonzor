# Chilonzor - APK tahlil tizimi

Telegram botdan API orqali kelgan APK fayllarni kursantlar tahlil qiladi (ichidan IP, domen va
Telegram ID topadi), natijani **Chilonzor** roliga yuboradi, Chilonzor esa qabul qiladi yoki
kamchiliklarini yozib qaytaradi. MVD hammasini ko'rib turadi.

## Rollar
- **Admin** (`is_staff`) - hamma narsa: kursantlar, API kalitlari, foydalanuvchilar.
- **Kursant** - jadvalda ustuni bor xodim (`Kursantlar` bo'limi). Ishni "oladi" (birinchi olgan ishlaydi),
  IP / domen / Telegram ID kiritadi va Chilonzorga yuboradi. Qaytarilsa tuzatib qayta yuboradi.
- **MVD** - hammasini ko'radi (faqat o'qish). API orqali ma'lumot yuboruvchi kalitlar ham MVD hisobiga bog'lanadi.
- **Chilonzor** - yuborilgan tahlilni qabul qiladi yoki sababi (kamchiliklari) bilan qaytaradi.

Oqim: `Yangi -> Kursant tahlil qilmoqda -> Chilonzor ko'rib chiqmoqda -> Qabul qilindi`
(yoki `Qaytarildi` -> kursant tuzatadi -> qayta yuboradi). Har bir o'tish "Ish tarixi"da saqlanadi.

## Botdan APK qabul qilish (API)
Admin `/apk/api-keys/` sahifasida kalit yaratadi (MVD hisobiga bog'lanadi; kalit faqat bir marta ko'rsatiladi,
bazada faqat xeshi saqlanadi). Bot shu kalit bilan yuboradi:

```
POST /api/apk/
Authorization: Bearer <kalit>          (yoki X-API-Token: <kalit>)
Content-Type: multipart/form-data

file=<APK fayl>            majburiy, .apk (ZIP), eng ko'pi APK_MAX_UPLOAD_MB
profile_name=Ўткир         yuborgan profil nomi
username=@salom6233        yuborgan username
user_id=5907562354         yuborgan user ID
title=My music             APK yuborilgan guruh nomi
type=supergroup            guruh turi
chat_id=-1003542328393     guruh ID
```

Javob `201`: `{"ok": true, "id": 12, "status": "new", "sha256": "...", "duplicate_of": null}`.
Xato: `400` (maydon/fayl noto'g'ri), `401` (kalit noto'g'ri), `413` (fayl katta), `405` (POST emas).
Bir xil fayl (SHA-256) qayta kelsa ham yangi yozuv ochiladi, `duplicate_of` oldingi yozuvni ko'rsatadi
va kursant oldingi topilmalarni bir tugma bilan ko'chira oladi.

APK fayllar ochiq `/media/` orqali **berilmaydi**; faqat tizimga kirgan, ruxsati bor foydalanuvchi
`Yuklab olish` orqali oladi. Fayl zararli bo'lishi mumkin - faqat izolyatsiyalangan muhitda oching.

## Tarkibi
- `apk/` - asosiy ilova: modellar, API (`api.py`), ish oqimi (`workflow.py`), tekshiruv (`parsing.py`), sahifalar.
- `app/` - umumiy asos: login/ro'yxatdan o'tish, foydalanuvchilar va guruhlar, ichki xabarlar, UI tarjimasi (uz/en).
- `chilonzor/` - Django sozlamalari va URL'lar.

## Ishga tushirish (Windows)
`ishga_tushir.bat` - venv yaratadi, kutubxonalarni o'rnatadi, migratsiya qiladi va serverni ochadi
(`http://127.0.0.1:8000/apk/works/`).

Qo'lda:
```
python -m venv winenv && winenv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
`python manage.py demo_data` - demo hisoblar (admin1, mvd1, kursant1, kursant2, chilonzor1) va namunaviy APK ishlar;
`--clear` bilan o'chiriladi. Baza: lokalda `chilonzor_db.sqlite3`, Docker ichida PostgreSQL (`.env.example`).
Migratsiyalar MVD va Chilonzor guruhlarini avtomatik yaratadi.

Eslatma: avvalgi (karta bloklash) versiyada ishlatilgan eski baza bu versiyaga mos kelmaydi -
`chilonzor_db.sqlite3` faylini o'chirib, `migrate` ni qaytadan ishga tushiring.
