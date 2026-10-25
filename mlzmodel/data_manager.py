"""
Data Manager & Longitudinal Tracker
Handles cohort data ingestion, benchmark cohort generation (strictly labeled SYNTHETIC_BENCHMARK),
and longitudinal session tracking with dynamic Bayesian updating.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from .config import InputProfile, SAMPLE_ARCHETYPES


class CohortManager:
    """
    Manages longitudinal athlete tracking, session logging, and benchmark cohort generation.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.athletes_file = os.path.join(self.data_dir, "athletes.json")
        self.history_file = os.path.join(self.data_dir, "longitudinal_tests.json")
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(self.athletes_file):
            # Seed with preset archetypes
            with open(self.athletes_file, "w") as f:
                json.dump(SAMPLE_ARCHETYPES, f, indent=2)
        if not os.path.exists(self.history_file):
            # Seed with sample longitudinal tracking data
            sample_history = {
                "Elite Sprinter": [
                    {"date": "2026-01-15", "metric": "cmj_height_cm", "value": 58.5, "unit": "cm"},
                    {"date": "2026-04-10", "metric": "cmj_height_cm", "value": 61.2, "unit": "cm"},
                    {"date": "2026-07-22", "metric": "cmj_height_cm", "value": 63.4, "unit": "cm"},
                    {"date": "2026-10-18", "metric": "cmj_height_cm", "value": 64.1, "unit": "cm"},
                ],
                "Olympic Lifter": [
                    {"date": "2026-02-01", "metric": "cmj_height_cm", "value": 47.0, "unit": "cm"},
                    {"date": "2026-05-15", "metric": "cmj_height_cm", "value": 49.5, "unit": "cm"},
                    {"date": "2026-09-01", "metric": "cmj_height_cm", "value": 51.0, "unit": "cm"},
                ]
            }
            with open(self.history_file, "w") as f:
                json.dump(sample_history, f, indent=2)

    def load_athletes(self) -> Dict[str, Dict[str, Any]]:
        with open(self.athletes_file, "r") as f:
            return json.load(f)

    def save_athlete(self, key: str, athlete_dict: Dict[str, Any]):
        athletes = self.load_athletes()
        athletes[key] = athlete_dict
        with open(self.athletes_file, "w") as f:
            json.dump(athletes, f, indent=2)

    def load_history(self, athlete_name: str, metric: str = "cmj_height_cm") -> List[Dict[str, Any]]:
        with open(self.history_file, "r") as f:
            all_history = json.load(f)
        records = all_history.get(athlete_name, [])
        return [r for r in records if r.get("metric") == metric]

    def add_test_session(self, athlete_name: str, metric: str, value: float, unit: str, date_str: Optional[str] = None):
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        with open(self.history_file, "r") as f:
            all_history = json.load(f)
        if athlete_name not in all_history:
            all_history[athlete_name] = []
        all_history[athlete_name].append({
            "date": date_str,
            "metric": metric,
            "value": float(value),
            "unit": unit
        })
        with open(self.history_file, "w") as f:
            json.dump(all_history, f, indent=2)

    @staticmethod
    def generate_benchmark_synthetic_cohort(n: int = 50) -> pd.DataFrame:
        """
        Generates an empirical benchmark cohort adhering to published physiological covariance
        (Kumagai 2000, Baxter 2012, Samozino 2014).
        CRITICAL: Explicitly tagged with DATA_ORIGIN: SYNTHETIC_BENCHMARK.
        """
        np.random.seed(101)
        mass = np.random.normal(80.0, 10.0, n)
        height = np.random.normal(180.0, 7.5, n)
        bf = np.random.normal(12.5, 4.0, n)
        lean = mass * (1.0 - bf / 100.0)
        femur = 0.245 * height + np.random.normal(0, 1.1, n)
        tibia = 0.215 * height + np.random.normal(0, 1.0, n)
        crural = tibia / femur
        calcaneus = 0.20 * (0.152 * height) + np.random.normal(0, 0.35, n)
        gear = (0.12 * height) / calcaneus
        lf = 0.192 * femur + np.random.normal(0, 0.65, n)
        penn = 14.0 + 0.10 * (mass / 75.0) * 14.0 + np.random.normal(0, 1.4, n)
        pcsa = (lean * 3.7) * np.cos(np.radians(penn)) / np.clip(lf, 4.0, 12.0)
        k_tendon = 480.0 + 3.2 * lean + np.random.normal(0, 40.0, n)

        # Performance targets with realistic noise
        cmj_height = 28.0 + 0.35 * (lf - 7.5) * 4.0 + 0.22 * (lean / mass * 100.0) + np.random.normal(0, 2.5, n)
        vmax = 6.8 + 0.32 * (lf - 7.5) + 3.5 * (crural - 0.86) + np.random.normal(0, 0.3, n)
        pmax = (55.0 * (lean ** 0.67) + 6.0 * pcsa + 0.3 * k_tendon) + np.random.normal(0, 180.0, n)

        df = pd.DataFrame({
            "DATA_ORIGIN": ["SYNTHETIC_BENCHMARK"] * n,
            "Athlete_ID": [f"ATH_{i+1:03d}" for i in range(n)],
            "Body_Mass_kg": np.round(mass, 1),
            "Height_cm": np.round(height, 1),
            "Body_Fat_pct": np.round(bf, 1),
            "Lean_Mass_kg": np.round(lean, 1),
            "Femur_Length_cm": np.round(femur, 1),
            "Tibia_Length_cm": np.round(tibia, 1),
            "Crural_Index": np.round(crural, 3),
            "Ankle_Gear_Ratio": np.round(gear, 2),
            "Fascicle_Length_cm": np.round(lf, 2),
            "Pennation_Angle_deg": np.round(penn, 1),
            "PCSA_proxy_cm2": np.round(pcsa, 1),
            "Tendon_Stiffness_N_mm": np.round(k_tendon, 1),
            "CMJ_Height_cm": np.round(cmj_height, 1),
            "Sprint_Vmax_m_s": np.round(vmax, 2),
            "Peak_Power_Watts": np.round(pmax, 1),
        })
        return df
