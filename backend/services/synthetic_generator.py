"""
NexSight AI - Synthetic Manufacturing Data Generator
Generates realistic 70% synthetic telemetry data with built-in correlations
to enable meaningful pattern discovery, root cause analysis, and predictions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import (
    SYNTHETIC_DATA_PATH, SYNTHETIC_NUM_RECORDS,
    SYNTHETIC_NUM_MACHINES, SYNTHETIC_SHIFTS,
    SYNTHETIC_PRODUCT_LINES, THRESHOLDS
)


def generate_synthetic_data(num_records: int = None, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic manufacturing sensor / telemetry data with
    intentionally embedded correlations and anomalies so that downstream
    analytics (pattern discovery, root-cause, prediction) can discover
    meaningful insights.

    Key embedded patterns:
      • Night shift to higher defect rates (fatigue, lower staffing)
      • High vibration to soldering defects spike
      • Temperature excursions to yield drops
      • Calibration drift over time to gradual quality degradation
      • Machine M3 / M7 to more maintenance issues
      • Humidity + temperature interaction to mousebite defects
    """
    if num_records is None:
        num_records = SYNTHETIC_NUM_RECORDS

    np.random.seed(seed)

    # ── Time axis: 90 days of production ───────────────────────
    start_date = datetime(2025, 1, 1)
    timestamps = [
        start_date + timedelta(hours=i * 0.5)
        for i in range(num_records)
    ]

    # ── Machine assignments ────────────────────────────────────
    machine_ids = [f"M{i+1}" for i in range(SYNTHETIC_NUM_MACHINES)]
    machines = np.random.choice(machine_ids, num_records)

    # ── Shift assignment based on hour ─────────────────────────
    hours = np.array([t.hour for t in timestamps])
    shifts = np.where(hours < 8, "Morning",
             np.where(hours < 16, "Afternoon", "Night"))

    # ── Product line ───────────────────────────────────────────
    products = np.random.choice(SYNTHETIC_PRODUCT_LINES, num_records)

    # ── Base sensor readings (normal operating ranges) ─────────
    base_temp = np.random.normal(65, 8, num_records)
    base_vibration = np.random.exponential(1.8, num_records)
    base_humidity = np.random.normal(50, 12, num_records)
    base_pressure = np.random.normal(1.0, 0.08, num_records)
    base_speed = np.random.normal(90, 15, num_records)

    # ── Calibration drift: increases over time per machine ─────
    day_index = np.array([(t - start_date).days for t in timestamps])
    calibration_offset = np.zeros(num_records)
    for m in machine_ids:
        mask = machines == m
        drift_rate = np.random.uniform(0.0005, 0.002)
        noise = np.random.normal(0, 0.01, mask.sum())
        calibration_offset[mask] = drift_rate * day_index[mask] + noise
        # Machine M3 and M7 drift faster (problematic machines)
        if m in ["M3", "M7"]:
            calibration_offset[mask] *= 2.5

    # ── Inject anomalies & correlations ────────────────────────

    # Pattern 1: Night shift to higher temperature (less cooling)
    night_mask = shifts == "Night"
    base_temp[night_mask] += np.random.normal(8, 3, night_mask.sum())

    # Pattern 2: Machine M3 to higher vibration
    m3_mask = machines == "M3"
    base_vibration[m3_mask] += np.random.exponential(2.0, m3_mask.sum())

    # Pattern 3: Humidity spikes during afternoon (environmental)
    afternoon_mask = shifts == "Afternoon"
    base_humidity[afternoon_mask] += np.random.normal(10, 4, afternoon_mask.sum())

    # Pattern 4: Speed variation for PCB-Gamma (production issue)
    gamma_mask = products == "PCB-Gamma"
    base_speed[gamma_mask] += np.random.normal(15, 8, gamma_mask.sum())

    # Clamp values to realistic ranges
    temperature = np.clip(base_temp, 10, 120)
    vibration = np.clip(base_vibration, 0.1, 15)
    humidity = np.clip(base_humidity, 15, 95)
    pressure = np.clip(base_pressure, 0.5, 1.5)
    speed = np.clip(base_speed, 30, 160)
    calibration_offset = np.clip(calibration_offset, 0, 0.5)

    # ── Defect count: correlated with multiple factors ─────────
    defect_base = np.random.poisson(1.5, num_records).astype(float)

    # High vibration to more defects
    high_vib = vibration > THRESHOLDS["vibration_high"]
    defect_base[high_vib] += np.random.poisson(3, high_vib.sum())

    # Temperature excursion to more defects
    high_temp = temperature > THRESHOLDS["temperature_high"]
    defect_base[high_temp] += np.random.poisson(2, high_temp.sum())

    # Night shift to more defects
    defect_base[night_mask] += np.random.poisson(1, night_mask.sum())

    # Calibration drift to more defects
    high_cal = calibration_offset > THRESHOLDS["calibration_drift_max"]
    defect_base[high_cal] += np.random.poisson(2, high_cal.sum())

    # Humidity + temperature interaction to mousebite defects
    humid_hot = (humidity > THRESHOLDS["humidity_high"]) & (temperature > 70)
    defect_base[humid_hot] += np.random.poisson(2, humid_hot.sum())

    # High speed to more defects
    high_speed = speed > THRESHOLDS["speed_high"]
    defect_base[high_speed] += np.random.poisson(1, high_speed.sum())

    defect_count = np.clip(defect_base, 0, 25).astype(int)

    # ── Yield rate: inversely correlated with defects ──────────
    yield_rate = np.clip(
        98.0 - defect_count * 1.2
        - (vibration - 2.0) * 0.5
        - calibration_offset * 15
        + np.random.normal(0, 0.8, num_records),
        60, 100
    )

    # ── Defect types per record ────────────────────────────────
    defect_types = []
    for i in range(num_records):
        if defect_count[i] == 0:
            defect_types.append("none")
        else:
            # Weighted based on conditions
            weights = [0.15, 0.15, 0.15, 0.20, 0.20, 0.15]  # base
            if vibration[i] > THRESHOLDS["vibration_high"]:
                weights[0] += 0.25  # open
                weights[1] += 0.20  # short
            if humidity[i] > THRESHOLDS["humidity_high"]:
                weights[2] += 0.30  # mousebite
            if temperature[i] > THRESHOLDS["temperature_high"]:
                weights[3] += 0.20  # spur
            if calibration_offset[i] > THRESHOLDS["calibration_drift_max"]:
                weights[4] += 0.25  # pinhole
            if speed[i] > THRESHOLDS["speed_high"]:
                weights[5] += 0.20  # spurious_copper

            weights = np.array(weights) / sum(weights)
            types = ["open", "short", "mousebite", "spur", "pinhole", "spurious_copper"]
            primary = np.random.choice(types, p=weights)
            defect_types.append(primary)

    # ── Power consumption (correlated with speed & vibration) ──
    power_consumption = (
        150 + speed * 0.8 + vibration * 5
        + temperature * 0.3
        + np.random.normal(0, 10, num_records)
    )
    power_consumption = np.clip(power_consumption, 80, 400)

    # ── Downtime minutes (correlated with defects & vibration) ─
    downtime = np.where(
        defect_count > 5,
        np.random.exponential(30, num_records),
        np.where(defect_count > 2,
                 np.random.exponential(10, num_records),
                 np.random.exponential(2, num_records))
    )
    downtime = np.clip(downtime, 0, 180).astype(int)

    # ── Build DataFrame ────────────────────────────────────────
    df = pd.DataFrame({
        "timestamp": timestamps,
        "machine_id": machines,
        "shift": shifts,
        "product_line": products,
        "temperature_c": np.round(temperature, 2),
        "vibration_mm_s": np.round(vibration, 3),
        "humidity_pct": np.round(humidity, 1),
        "pressure_bar": np.round(pressure, 3),
        "speed_units_hr": np.round(speed, 1),
        "calibration_offset": np.round(calibration_offset, 4),
        "power_consumption_kw": np.round(power_consumption, 1),
        "defect_count": defect_count,
        "primary_defect_type": defect_types,
        "yield_rate_pct": np.round(yield_rate, 2),
        "downtime_minutes": downtime,
    })

    # ── Add derived features ───────────────────────────────────
    df["is_anomaly"] = (
        (df["vibration_mm_s"] > THRESHOLDS["vibration_high"]) |
        (df["temperature_c"] > THRESHOLDS["temperature_high"]) |
        (df["calibration_offset"] > THRESHOLDS["calibration_drift_max"])
    ).astype(int)

    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["week_number"] = df["timestamp"].dt.isocalendar().week.astype(int)

    return df


def save_synthetic_data(df: pd.DataFrame = None) -> str:
    """Generate and save synthetic data to CSV."""
    if df is None:
        df = generate_synthetic_data()

    filepath = SYNTHETIC_DATA_PATH / "manufacturing_telemetry.csv"
    df.to_csv(filepath, index=False)
    print(f"[OK] Saved {len(df)} synthetic records to {filepath}")
    return str(filepath)


def generate_machine_maintenance_log(seed: int = 42) -> pd.DataFrame:
    """Generate synthetic maintenance log data."""
    np.random.seed(seed)
    start_date = datetime(2025, 1, 1)

    records = []
    machine_ids = [f"M{i+1}" for i in range(SYNTHETIC_NUM_MACHINES)]
    maintenance_types = [
        "Scheduled Maintenance", "Emergency Repair",
        "Calibration", "Part Replacement",
        "Firmware Update", "Deep Cleaning"
    ]

    for day in range(90):
        date = start_date + timedelta(days=day)
        # 1-3 maintenance events per day
        n_events = np.random.randint(1, 4)
        for _ in range(n_events):
            machine = np.random.choice(machine_ids)
            # M3 and M7 get more emergency repairs
            if machine in ["M3", "M7"]:
                weights = [0.15, 0.35, 0.20, 0.15, 0.05, 0.10]
            else:
                weights = [0.35, 0.10, 0.20, 0.15, 0.10, 0.10]

            mtype = np.random.choice(maintenance_types, p=weights)
            duration = max(15, int(np.random.normal(
                120 if "Emergency" in mtype else 60, 20
            )))

            records.append({
                "date": date,
                "machine_id": machine,
                "maintenance_type": mtype,
                "duration_minutes": duration,
                "technician": f"Tech-{np.random.randint(1, 6)}",
                "parts_replaced": np.random.choice(
                    ["None", "Solder Tip", "Conveyor Belt",
                     "Sensor Module", "Motor", "Filter"],
                    p=[0.4, 0.15, 0.10, 0.15, 0.10, 0.10]
                ),
                "cost_usd": round(duration * np.random.uniform(5, 25), 2)
            })

    df = pd.DataFrame(records)
    filepath = SYNTHETIC_DATA_PATH / "maintenance_log.csv"
    df.to_csv(filepath, index=False)
    print(f"[OK] Saved {len(df)} maintenance records to {filepath}")
    return df


def generate_all_synthetic_data():
    """Generate all synthetic datasets."""
    print("=" * 60)
    print("[INFO] NexSight AI - Synthetic Data Generation")
    print("=" * 60)

    telemetry_df = generate_synthetic_data()
    save_synthetic_data(telemetry_df)

    generate_machine_maintenance_log()

    # Summary statistics
    print(f"\n[INFO] Data Summary:")
    print(f"   Total records: {len(telemetry_df)}")
    print(f"   Date range: {telemetry_df['timestamp'].min()} to {telemetry_df['timestamp'].max()}")
    print(f"   Machines: {telemetry_df['machine_id'].nunique()}")
    print(f"   Avg defect count: {telemetry_df['defect_count'].mean():.2f}")
    print(f"   Anomaly rate: {telemetry_df['is_anomaly'].mean()*100:.1f}%")
    print(f"   Avg yield: {telemetry_df['yield_rate_pct'].mean():.1f}%")
    print("=" * 60)

    return telemetry_df


if __name__ == "__main__":
    generate_all_synthetic_data()

