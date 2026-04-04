# Mitra Revamp Dashboard Backend

FastAPI backend untuk dashboard superadmin Mitranesia.

## Jalankan

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# isi .env lebih dulu atau salin dari .env.example lalu ganti secret/password
alembic upgrade head
uvicorn app.main:app --reload
```

## Jalankan dengan Docker

```bash
docker compose up --build
```

Service yang tersedia:
- API: `http://localhost:5001`
- Health check: `http://localhost:5001/health`

Catatan:
- `docker-compose.yml` hanya menjalankan backend dan membaca semua konfigurasi langsung dari `.env`.
- database tidak dijalankan di Docker; koneksi mengikuti `DATABASE_URL` dan `PSQL_DATABASE_URL` yang sudah ada di `.env`.
- Saat container backend start, `alembic upgrade head` dijalankan otomatis sebelum `uvicorn`.

## Postman

File collection tersedia di `postman_collection.json`.

Langkah pakai:
- import `postman_collection.json` ke Postman
- collection variable `dashboardUsername` dan `dashboardPassword` sudah disamakan dengan default admin di `.env`; ubah jika `.env` berubah
- sesuaikan `baseUrl` bila backend tidak berjalan di `http://localhost:5001`
- jalankan `POST /api/dashboard/auth/login` lebih dulu agar `dashboardAccessToken` terisi otomatis
- request create merchant, carousel, insight, dan admin user akan menyimpan ID ke collection variable agar request detail, update, status, dan delete berikutnya bisa langsung dipakai

Catatan:
- folder `Client` memakai route `/api/client/...` dan folder `Dashboard` memakai route `/api/dashboard/...`
- auth collection memakai header `Authorization: Bearer {{dashboardAccessToken}}` untuk dashboard dan `Authorization: Bearer {{clientAccessToken}}` untuk client
- endpoint yang dimasukkan mengikuti route backend yang benar-benar ada saat ini, termasuk `POST /api/dashboard/admin-users/{user_id}/reset-password`

## Persiapan database

Project ini menyediakan dua cara untuk menyiapkan database PostgreSQL.

Pakai SQL langsung:

```bash
set -a
source .env
set +a
psql "$DATABASE_URL" -f migration.sql
```

Atau gunakan `PSQL_DATABASE_URL` bila `.env` menyimpan URL SQLAlchemy:

```bash
set -a
source .env
set +a
psql "$PSQL_DATABASE_URL" -f migration.sql
```

Pakai reset schema lalu Alembic:

```bash
set -a
source .env
set +a
psql "$PSQL_DATABASE_URL" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
alembic upgrade head
```

Catatan:
- `migration.sql` akan menghapus semua tabel di schema `public` lalu membuat ulang tabel backend ini.
- Jika memakai `migration.sql`, jangan jalankan `alembic upgrade head` lagi pada database yang sama kecuali schema sudah dibersihkan ulang lebih dulu.

## Test

```bash
pytest
```
