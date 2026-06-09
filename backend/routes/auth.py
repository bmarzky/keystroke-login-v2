from flask import Blueprint, request, jsonify, render_template
from backend.services.supabase_client import get_supabase
from backend.services.keystroke_service import save_session, get_sessions
from backend.services.scoring_service import verify

auth_bp = Blueprint('auth', __name__)

# ── Halaman ──────────────────────────────────────────────────

@auth_bp.route('/register')
def register_page():
    return render_template('register.html')

@auth_bp.route('/login')
def login_page():
    return render_template('login.html')

# ── API: Register ─────────────────────────────────────────────

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data     = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username dan password wajib diisi'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password minimal 6 karakter'}), 400

    supabase = get_supabase()

    existing = supabase.table('users') \
        .select('id') \
        .eq('username', username) \
        .execute()

    if existing.data:
        return jsonify({'error': 'Username sudah dipakai'}), 409

    supabase.table('users').insert({
        'username':    username,
        'password':    password,
        'login_count': 0,
        'status':      'enrolling'
    }).execute()

    return jsonify({'message': 'Register berhasil, silakan login'}), 201

# ── API: Login ────────────────────────────────────────────────

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data      = request.get_json()
    username  = data.get('username', '').strip()
    password  = data.get('password', '')
    keystroke = data.get('keystroke', {})

    if not username or not password:
        return jsonify({'error': 'Username dan password wajib diisi'}), 400

    supabase = get_supabase()

    # Ambil user
    result = supabase.table('users') \
        .select('*') \
        .eq('username', username) \
        .execute()

    if not result.data:
        return jsonify({'error': 'Username atau password salah'}), 401

    user = result.data[0]

    # Verifikasi password
    if user['password'] != password:
        return jsonify({'error': 'Username atau password salah'}), 401

    # Validasi keystroke
    dwell  = keystroke.get('dwell',  [])
    flight = keystroke.get('flight', [])
    meta   = keystroke.get('meta',   {})

    if meta.get('paste_detected'):
        return jsonify({'error': 'Input tidak valid'}), 400

    if len(dwell) < 2:
        return jsonify({
            'message':     'Login berhasil',
            'status':      user['status'],
            'login_count': user['login_count']
        }), 200

    # Ambil sesi sebelumnya untuk bangun profil
    previous_sessions = get_sessions(user['id'])

    # Verifikasi keystroke
    score = verify(
        new_dwell   = dwell,
        new_flight  = flight,
        sessions    = previous_sessions,
        login_count = user['login_count']
    )

    # Jika profil sudah ada dan pola tidak cocok → tolak
    if score['verified'] is False:
        return jsonify({
            'error':     'Pola ketikan tidak cocok',
            'distance':  score['distance'],
            'threshold': score['threshold']
        }), 401

    # Simpan sesi keystroke
    if len(dwell) >= 2:
        save_session(
            user_id = user['id'],
            dwell   = dwell,
            flight  = flight,
            meta    = meta
        )

    # Update login_count dan status
    new_count  = user['login_count'] + 1
    new_status = 'active' if new_count >= 5 else 'enrolling'

    supabase.table('users').update({
        'login_count': new_count,
        'status':      new_status
    }).eq('id', user['id']).execute()

    # Pesan berbeda tergantung status
    if score['verified'] is None:
        message = f'Login berhasil — mengumpulkan data sesi ke-{new_count}'
    else:
        message = f'Login berhasil — pola ketikan terverifikasi'

    return jsonify({
        'message':     message,
        'status':      new_status,
        'login_count': new_count,
        'distance':    score['distance'],
        'threshold':   score['threshold']
    }), 200