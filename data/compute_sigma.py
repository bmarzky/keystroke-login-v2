import numpy as np
import pandas as pd

# ── Definisi kolom ───────────────────────────────────────────
DWELL_COLS = [
    'H.period', 'H.t', 'H.i', 'H.e', 'H.five',
    'H.Shift.r', 'H.o', 'H.a', 'H.n', 'H.l', 'H.Return'
]

FLIGHT_COLS = [
    'UD.period.t', 'UD.t.i',       'UD.i.e',      'UD.e.five',
    'UD.five.Shift.r', 'UD.Shift.r.o', 'UD.o.a',
    'UD.a.n',     'UD.n.l',        'UD.l.Return'
]

# ── Ekstrak 9 fitur dari satu baris ─────────────────────────
def extract_features(row):
    d = row[DWELL_COLS].values  * 1000  # detik → ms
    f = row[FLIGHT_COLS].values * 1000

    n        = len(d)
    interval = d[:-1] + f

    total_time   = np.sum(d) + np.sum(f)
    typing_speed = n / total_time * 1000
    mean_dwell   = np.mean(d)
    mean_flight  = np.mean(f)
    std_dwell    = np.std(d)
    std_flight   = np.std(f)
    rhythm       = np.std(interval) / (np.mean(interval) + 1e-9)
    flow_score   = np.mean(np.abs(np.diff(f)))
    acceleration = np.mean(np.diff(interval))

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

# ── Validasi satu baris ──────────────────────────────────────
def is_valid_row(row):
    d = row[DWELL_COLS].values * 1000
    f = row[FLIGHT_COLS].values * 1000

    if np.any(d <= 0):       return False
    if np.any(d > 2000):     return False
    if np.any(f < -500):     return False

    return True

# ── Hitung Σ_global ──────────────────────────────────────────
def compute_sigma_global(filepath):
    print(f"Membaca dataset: {filepath}")
    df = pd.read_csv(filepath)
    print(f"Total baris: {len(df)}, subjek: {df['subject'].nunique()}")

    # Kumpulkan fitur per subjek
    from collections import defaultdict
    by_user = defaultdict(list)
    skipped = 0

    for _, row in df.iterrows():
        if not is_valid_row(row):
            skipped += 1
            continue
        features = extract_features(row)
        by_user[row['subject']].append(features)

    print(f"Valid: {sum(len(v) for v in by_user.values())}, dibuang: {skipped}")

    # Kumpulkan within-user deviations
    all_deviations = []

    for subject, feats in by_user.items():
        feats_arr = np.array(feats)
        mu_user   = np.mean(feats_arr, axis=0)

        for f in feats_arr:
            all_deviations.append(f - mu_user)

    deviations   = np.array(all_deviations)
    sigma_global = np.cov(deviations, rowvar=False)

    return sigma_global

# ── Validasi matrix ──────────────────────────────────────────
def validate_sigma(sigma):
    print("\n── Validasi Σ_global ──────────────────")
    print(f"Shape          : {sigma.shape}")

    eigenvalues = np.linalg.eigvalsh(sigma)
    print(f"Min eigenvalue : {eigenvalues.min():.6f}")

    cond = np.linalg.cond(sigma)
    print(f"Condition num  : {cond:.2f}")

    # Regularisasi adaptif — cari lambda yang cukup
    lam = 1e-6
    while True:
        sigma_reg   = sigma + lam * np.eye(sigma.shape[0])
        eigenvalues = np.linalg.eigvalsh(sigma_reg)
        cond        = np.linalg.cond(sigma_reg)

        if eigenvalues.min() > 1e-6 and cond < 1e6:
            break

        lam *= 10
        if lam > 1e6:
            print("⚠ Lambda terlalu besar — cek fitur")
            break

    print(f"Regularisasi   : lambda = {lam}")
    print(f"Min eigenvalue : {np.linalg.eigvalsh(sigma_reg).min():.6f} ✓")
    print(f"Condition num  : {np.linalg.cond(sigma_reg):.2f} ✓")

    sigma_inv = np.linalg.inv(sigma_reg)
    print(f"Invertible     : ✓")

    return sigma_inv

# ── Main ─────────────────────────────────────────────────────
if __name__ == '__main__':
    filepath = 'data/cmu/DSL-StrongPasswordData.csv'

    sigma     = compute_sigma_global(filepath)
    sigma_inv = validate_sigma(sigma)

    np.save('data/sigma_global.npy',     sigma)
    np.save('data/sigma_global_inv.npy', sigma_inv)

    print("\n✓ Σ_global tersimpan di data/sigma_global.npy")
    print("✓ Σ_global_inv tersimpan di data/sigma_global_inv.npy")