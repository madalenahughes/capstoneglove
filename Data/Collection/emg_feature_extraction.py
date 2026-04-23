import os
import glob
import numpy as np
import pandas as pd

# ─── CONFIG ────────────────────────────────────────────────────────────────────
INPUT_FOLDER   = "/Users/evansmacbookair/Downloads/capstone26_data"          # folder containing your subject CSVs
OUTPUT_FILE    = "emg_features_combined.csv"

SAMPLING_RATE  = 200          # Hz
WINDOW_MS      = 200          # window length in milliseconds
OVERLAP_PCT    = 0.5          # 50% overlap between consecutive windows

# Labels to discard before windowing (transition buffer + empty rows)
DROP_LABELS    = {"CHANGE", ""}

# Derived window parameters
WINDOW_SAMPLES = int(SAMPLING_RATE * WINDOW_MS / 1000)   # 40 samples
STEP_SAMPLES   = int(WINDOW_SAMPLES * (1 - OVERLAP_PCT)) # 20 samples
# ───────────────────────────────────────────────────────────────────────────────


def zero_crossings(x, threshold=5):
    """Count zero crossings with a dead-zone threshold to ignore noise."""
    count = 0
    for i in range(1, len(x)):
        if abs(x[i] - x[i-1]) > threshold:
            if (x[i] >= 0 and x[i-1] < 0) or (x[i] < 0 and x[i-1] >= 0):
                count += 1
    return count


def slope_sign_changes(x, threshold=5):
    """Count slope sign changes (direction reversals) with threshold."""
    count = 0
    for i in range(1, len(x) - 1):
        diff1 = x[i] - x[i-1]
        diff2 = x[i+1] - x[i]
        if abs(diff1) > threshold and abs(diff2) > threshold:
            if (diff1 > 0 and diff2 < 0) or (diff1 < 0 and diff2 > 0):
                count += 1
    return count


def extract_window_features(window_f, window_p, window_e):
    """Compute all features for one window across three EMG channels."""
    feats = {}

    window_f = np.array(window_f, dtype=float)
    window_p = np.array(window_p, dtype=float)
    window_e = np.array(window_e, dtype=float)

    for name, w in [("F", window_f), ("P", window_p), ("E", window_e)]:
        w = np.array(w, dtype=float)

        # ── Tier 1: Time-domain features ──────────────────────────────────────
        feats[f"{name}_rms"]  = np.sqrt(np.mean(w ** 2))
        feats[f"{name}_mav"]  = np.mean(np.abs(w))
        feats[f"{name}_std"]  = np.std(w)
        feats[f"{name}_wl"]   = np.sum(np.abs(np.diff(w)))         # waveform length
        feats[f"{name}_zc"]   = zero_crossings(w)
        feats[f"{name}_ssc"]  = slope_sign_changes(w)
        feats[f"{name}_iemg"] = np.sum(np.abs(w))                  # integrated EMG
        feats[f"{name}_var"]  = np.var(w)
        feats[f"{name}_min"]  = np.min(w)
        feats[f"{name}_max"]  = np.max(w)
        feats[f"{name}_range"]= np.max(w) - np.min(w)

        # ── Frequency-domain features (FFT-based) ─────────────────────────────
        fft_vals = np.abs(np.fft.rfft(w))
        freqs    = np.fft.rfftfreq(len(w), d=1.0 / SAMPLING_RATE)

        total_power = np.sum(fft_vals ** 2) + 1e-9  # avoid div-by-zero

        # Mean & median frequency
        feats[f"{name}_mean_freq"]   = np.sum(freqs * fft_vals) / (np.sum(fft_vals) + 1e-9)
        cumulative = np.cumsum(fft_vals)
        median_idx = np.searchsorted(cumulative, cumulative[-1] / 2)
        feats[f"{name}_median_freq"] = freqs[median_idx] if median_idx < len(freqs) else 0

        # Band power ratios (slow-twitch 20–60 Hz, fast-twitch 60–150 Hz)
        slow_mask = (freqs >= 20) & (freqs < 60)
        fast_mask = (freqs >= 60) & (freqs < 150)
        feats[f"{name}_power_slow"] = np.sum(fft_vals[slow_mask] ** 2) / total_power
        feats[f"{name}_power_fast"] = np.sum(fft_vals[fast_mask] ** 2) / total_power

    # ── Tier 2: Cross-channel ratio features ──────────────────────────────────
    f_rms = feats["F_rms"]
    p_rms = feats["P_rms"]
    e_rms = feats["E_rms"]

    feats["cross_F_E_ratio"]      = f_rms / (e_rms + 1e-9)          # flexor/extensor
    feats["cross_P_FE_ratio"]     = p_rms / (f_rms + e_rms + 1e-9)  # palmar relative
    feats["cross_total_rms"]      = f_rms + p_rms + e_rms           # global activation
    feats["cross_FP_corr"]        = float(np.corrcoef(window_f, window_p)[0, 1])
    feats["cross_FE_corr"]        = float(np.corrcoef(window_f, window_e)[0, 1])
    feats["cross_PE_corr"]        = float(np.corrcoef(window_p, window_e)[0, 1])

    # Co-contraction: both F and E active above their baseline
    COCONTRACT_THRESH = 20
    feats["cross_cocontraction"]  = int(f_rms > COCONTRACT_THRESH and e_rms > COCONTRACT_THRESH)

    return feats


def majority_label(labels):
    """Return the most common label in a window, ignoring DROP_LABELS."""
    filtered = [l for l in labels if l not in DROP_LABELS]
    if not filtered:
        return None
    return max(set(filtered), key=filtered.count)


def process_csv(filepath, subject_id):
    """Load one subject CSV, apply sliding window, return feature DataFrame."""
    df = pd.read_csv(filepath)

    # Normalize column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Coerce EMG columns to numeric, dropping any corrupt/non-numeric rows
    for col in ["F", "P", "E"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    bad_rows = df[["F", "P", "E"]].isna().any(axis=1).sum()
    if bad_rows:
        print(f"  [WARN] {os.path.basename(filepath)} — dropped {bad_rows} corrupt row(s)")
    df = df.dropna(subset=["F", "P", "E"])

    # Drop pure CHANGE/empty rows upfront for cleaner windowing
    df = df[~df["Class"].isin(DROP_LABELS)].reset_index(drop=True)

    if len(df) < WINDOW_SAMPLES:
        print(f"  [SKIP] {os.path.basename(filepath)} — too few rows after filtering")
        return None

    rows = []
    n = len(df)

    for start in range(0, n - WINDOW_SAMPLES + 1, STEP_SAMPLES):
        end = start + WINDOW_SAMPLES
        chunk = df.iloc[start:end]

        label = majority_label(chunk["Class"].tolist())
        if label is None:
            continue  # window is all CHANGE/empty, skip

        feats = extract_window_features(
            chunk["F"].values,
            chunk["P"].values,
            chunk["E"].values
        )
        feats["subject_id"] = subject_id
        feats["label"]      = label
        rows.append(feats)

    return pd.DataFrame(rows)


def main():
    csv_files = sorted(glob.glob(os.path.join(INPUT_FOLDER, "*.csv")))
    # Exclude the output file itself if it already exists
    csv_files = [f for f in csv_files if os.path.basename(f) != OUTPUT_FILE]

    if not csv_files:
        print(f"No CSV files found in '{INPUT_FOLDER}'. Check INPUT_FOLDER path.")
        return

    print(f"Found {len(csv_files)} CSV file(s). Processing...")
    all_dfs = []

    for i, filepath in enumerate(csv_files):
        subject_id = f"S{i+1:02d}"
        print(f"  [{i+1}/{len(csv_files)}] {os.path.basename(filepath)} → {subject_id}")
        result = process_csv(filepath, subject_id)
        if result is not None and not result.empty:
            all_dfs.append(result)

    if not all_dfs:
        print("No data extracted. Check your CSV format.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)

    # Replace NaN correlations (e.g., flat channels) with 0
    combined = combined.fillna(0)

    combined.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✓ Done! Output: {OUTPUT_FILE}")
    print(f"  Total windows : {len(combined):,}")
    print(f"  Total features: {len(combined.columns) - 2}  (excluding label & subject_id)")
    print(f"  Label counts:\n{combined['label'].value_counts().to_string()}")
    print(f"\n  Window size   : {WINDOW_SAMPLES} samples ({WINDOW_MS}ms @ {SAMPLING_RATE}Hz)")
    print(f"  Step size     : {STEP_SAMPLES} samples (50% overlap)")


if __name__ == "__main__":
    main()