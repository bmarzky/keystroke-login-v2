# Keystroke Authentication System

Sistem autentikasi berbasis pola ketikan (keystroke dynamics) menggunakan Flask dan Supabase. Sistem ini menganalisis cara pengguna mengetik password untuk memverifikasi identitas secara pasif tanpa mengganggu pengalaman pengguna.

## Cara Kerja

Setiap orang memiliki pola ketikan yang unik — kecepatan, ritme, dan jeda antar tombol berbeda-beda. Sistem ini merekam pola tersebut secara diam-diam saat login, lalu membandingkannya dengan profil yang sudah dibangun dari sesi-sesi sebelumnya menggunakan **Mahalanobis Distance**.

```
Register → Login pertama → Kumpulkan data → Bangun profil → Verifikasi aktif
```

## Fitur yang Diekstraksi

| Fitur | Asal |
|-------|------|
| Mean Dwell | Rata-rata lama tombol ditekan |
| Mean Flight | Rata-rata jeda antar tombol |
| Std Dwell | Konsistensi tekanan |
| Std Flight | Konsistensi jeda |
| Typing Speed | Karakter per detik |
| Total Time | Durasi total mengetik |
| Rhythm | Keteraturan pola ketikan |
| Flow Score | Perubahan flight antar pasangan |
| Acceleration | Perubahan kecepatan dalam satu sesi |

## Struktur Proyek

```
keystroke-auth/
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/collector.js       ← merekam dwell + flight
│   └── templates/
│       ├── base.html
│       ├── register.html
│       └── login.html
├── backend/
│   ├── app.py                    ← entry point Flask
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth.py               ← endpoint register + login
│   └── services/
│       ├── supabase_client.py    ← koneksi Supabase
│       ├── keystroke_service.py  ← simpan sesi
│       └── scoring_service.py    ← verifikasi (tahap 2)
├── data/
│   ├── compute_sigma.py          ← hitung Σ_global dari CMU
│   ├── sigma_global.npy          ← hasil (tidak di-commit)
│   ├── sigma_global_inv.npy      ← hasil (tidak di-commit)
│   └── cmu/                      ← dataset CMU (tidak di-commit)
├── config.py
├── requirements.txt
└── .env                          ← tidak di-commit
```

## Teknologi

- **Backend** — Python, Flask
- **Database** — Supabase (PostgreSQL)
- **Numerik** — NumPy, SciPy
- **Frontend** — HTML, CSS, JavaScript (vanilla)

## Instalasi

```bash
# Clone repository
git clone https://github.com/bmarzky/keystroke-login-v2.git
cd keystroke-login-v2

# Buat virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## Konfigurasi

Buat file `.env` di root proyek:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key

FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

MIN_PASSWORD_LENGTH=6
MAX_LOGIN_BEFORE_ACTIVE=5
```

## Database

Jalankan SQL berikut di Supabase SQL Editor:

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT UNIQUE NOT NULL,
    password      TEXT NOT NULL,
    login_count   INTEGER DEFAULT 0,
    status        TEXT DEFAULT 'enrolling',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE keystroke_sessions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
    dwell            FLOAT[] NOT NULL,
    flight           FLOAT[] NOT NULL,
    backspace_count  INTEGER DEFAULT 0,
    paste_detected   BOOLEAN DEFAULT FALSE,
    is_synthetic     BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE keystroke_sessions DISABLE ROW LEVEL SECURITY;
```

## Menjalankan Aplikasi

```bash
python backend/app.py
```

Buka browser di `http://127.0.0.1:5000/register`

## Hitung Σ_global dari Dataset CMU

Letakkan dataset CMU di `data/cmu/DSL-StrongPasswordData.csv` lalu jalankan:

```bash
python data/compute_sigma.py
```

Dataset CMU tersedia di: https://www.cs.cmu.edu/~keystroke/

## Tahap Pengembangan

- [x] Tahap 1 — Fondasi sistem (register, login, rekam keystroke)
- [x] Tahap 2 — Hitung Σ_global dari dataset CMU
- [ ] Tahap 3 — Scoring service (Mahalanobis verification)
- [ ] Tahap 4 — Integrasi scoring ke endpoint login
- [ ] Tahap 5 — Validasi dan evaluasi sistem

## Referensi Dataset

Killourhy, K.S. & Maxion, R.A. (2009). *Comparing Anomaly Detectors for Keystroke Dynamics*. Carnegie Mellon University.