import os
import numpy as np

# ── Load Σ_global_inv sekali saat startup ────────────────────
_BASE_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SIGMA_PATH = os.path.join(_BASE_DIR, 'data', 'sigma_global_inv.npy')

try:
    SIGMA_INV = np.load(_SIGMA_PATH)
    print(f"✓ Σ_global_inv loaded: {SIGMA_INV.shape}")
except FileNotFoundError:
    SIGMA_INV = None
    print("⚠ sigma_global_inv.npy tidak ditemukan")

# ── 1. Ekstrak 9 fitur dari dwell + flight ───────────────────
def extract_features(dwell: list, flight: list) -> np.ndarray:
    d = np.array(dwell,  dtype=float)
    f = np.array(flight, dtype=float)

    # Pastikan flight selalu panjang dwell - 1
    expected = len(d) - 1
    if len(f) > expected:
        f = f[:expected]
    elif len(f) < expected:
        f = np.append(f, 0.0)

    n        = len(d)
    interval = d[:-1] + f

    total_time   = np.sum(d) + np.sum(f)
    typing_speed = n / total_time * 1000 if total_time > 0 else 0
    mean_dwell   = np.mean(d)
    mean_flight  = np.mean(f)
    std_dwell    = np.std(d)
    std_flight   = np.std(f)
    rhythm       = np.std(interval) / (np.mean(interval) + 1e-9)
    flow_score   = np.mean(np.abs(np.diff(f))) if len(f) > 1 else 0
    acceleration = np.mean(np.diff(interval))  if len(interval) > 1 else 0

    return np.array([
        mean_dwell,
        mean_flight,
        std_dwell,
        std_flight,
        typing_speed,
        total_time,
        rhythm,
        flow_score,
        acceleration
    ])

# ── 2. Hitung mean profil dari sesi sebelumnya ───────────────
def build_profile(sessions: list) -> np.ndarray | None:
    if not sessions:
        return None

    features = []
    for s in sessions:
        dwell  = s.get('dwell',  [])
        flight = s.get('flight', [])

        # Minimal 2 karakter untuk ekstraksi valid
        if len(dwell) < 2 or len(flight) < 1:
            continue

        features.append(extract_features(dwell, flight))

    if not features:
        return None

    return np.mean(features, axis=0)

# ── 3. Hitung Mahalanobis distance ───────────────────────────
def mahalanobis_distance(x: np.ndarray, mu: np.ndarray) -> float:
    if SIGMA_INV is None:
        return -1.0   # sigma belum tersedia

    diff = x - mu
    dist = float(np.sqrt(diff @ SIGMA_INV @ diff))
    return round(dist, 4)

# ── 4. Threshold adaptif per login_count ─────────────────────
def adaptive_threshold(login_count: int, base: float = 2.0) -> float:
    # Semakin sedikit data → threshold lebih longgar
    # Mengikuti CLT: ketidakpastian ∝ 1/√n
    uncertainty = 1.5 / np.sqrt(max(login_count, 1))
    return round(base + uncertainty, 3)

# ── 5. Fungsi utama: verifikasi satu sesi login ──────────────
def verify(
    new_dwell:   list,
    new_flight:  list,
    sessions:    list,
    login_count: int
) -> dict:

    # Belum ada sigma → tidak bisa verifikasi
    if SIGMA_INV is None:
        return {
            'verified':    None,
            'reason':      'sigma_not_ready',
            'distance':    None,
            'threshold':   None,
            'login_count': login_count
        }

    # Belum ada sesi sebelumnya → tidak bisa bangun profil
    if not sessions:
        return {
            'verified':    None,
            'reason':      'no_profile_yet',
            'distance':    None,
            'threshold':   None,
            'login_count': login_count
        }

    # Ekstrak fitur login baru
    if len(new_dwell) < 2 or len(new_flight) < 1:
        return {
            'verified':    None,
            'reason':      'insufficient_data',
            'distance':    None,
            'threshold':   None,
            'login_count': login_count
        }

    x  = extract_features(new_dwell, new_flight)

    # Bangun profil dari sesi sebelumnya
    mu = build_profile(sessions)
    if mu is None:
        return {
            'verified':    None,
            'reason':      'profile_build_failed',
            'distance':    None,
            'threshold':   None,
            'login_count': login_count
        }

    # Hitung jarak dan threshold
    distance  = mahalanobis_distance(x, mu)
    threshold = adaptive_threshold(login_count)
    verified  = distance < threshold

    return {
        'verified':    verified,
        'reason':      'ok',
        'distance':    distance,
        'threshold':   threshold,
        'login_count': login_count
    }