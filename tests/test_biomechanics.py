"""
Unit & Integration Tests for Mlzmodel Sports Biomechanics Engine
Validates physics consistency, allometry, Bayesian prediction intervals, and SHAP attribution.
"""

import unittest
import numpy as np
from mlzmodel.config import InputProfile, SAMPLE_ARCHETYPES
from mlzmodel.biomechanics import (
    calculate_segment_ratios,
    estimate_muscle_architecture,
    compute_force_velocity_profile,
    compute_elastic_and_fascial_contribution,
)
from mlzmodel.statistical_layer import BayesianPowerEngine
from mlzmodel.ml_layer import InterpretablePowerModel
from mlzmodel.profiler import AthleteProfiler
from mlzmodel.data_manager import CohortManager


class TestBiomechanics(unittest.TestCase):

    def test_segment_ratios(self):
        p = InputProfile(
            height=180.0,
            femur_length=45.0,
            tibia_length=40.0,
            foot_length=27.0,
            calcaneus_length=5.0,
            arm_span=188.0,
        )
        ratios = calculate_segment_ratios(p)
        self.assertEqual(ratios["crural_index"], round(40.0 / 45.0, 3))
        # forefoot = 27.0 - 5.0 = 22.0; gear = 22.0 / 5.0 = 4.4
        self.assertEqual(ratios["ankle_gear_ratio"], 4.4)
        self.assertEqual(ratios["ape_index_diff_cm"], 8.0)
        self.assertEqual(ratios["total_leg_length_cm"], 85.0)

    def test_muscle_architecture_ultrasound_override(self):
        # When ultrasound is provided, it must be directly respected
        p = InputProfile(
            us_fascicle_length_cm=9.5,
            us_pennation_angle_deg=13.5,
        )
        ratios = calculate_segment_ratios(p)
        arch = estimate_muscle_architecture(p, ratios)
        self.assertEqual(arch["fascicle_length_cm"], 9.5)
        self.assertEqual(arch["pennation_angle_deg"], 13.5)
        self.assertIn("Direct Ultrasound", arch["fascicle_source"])

    def test_allometric_scaling_consistency(self):
        p_light = InputProfile(body_mass=60.0, body_fat_pct=10.0)
        p_heavy = InputProfile(body_mass=100.0, body_fat_pct=10.0)

        r_light = calculate_segment_ratios(p_light)
        r_heavy = calculate_segment_ratios(p_heavy)

        arch_l = estimate_muscle_architecture(p_light, r_light)
        arch_h = estimate_muscle_architecture(p_heavy, r_heavy)

        fv_l = compute_force_velocity_profile(p_light, r_light, arch_l)
        fv_h = compute_force_velocity_profile(p_heavy, r_heavy, arch_h)

        # Absolute power of heavier athlete must be greater
        self.assertGreater(fv_h["pmax_watts"], fv_l["pmax_watts"])
        # Allometric power (W / kg^0.67) normalizes the curve
        self.assertGreater(fv_h["pmax_allometric"], 0)
        self.assertGreater(fv_l["pmax_allometric"], 0)

    def test_bayesian_prediction_intervals(self):
        bayes = BayesianPowerEngine()
        interval = bayes.compute_interval(
            predicted_mean=3000.0,
            metric_key="cmj_peak_power_w",
            unit="Watts",
            missing_count=0,
        )
        self.assertLess(interval.ci_lower, interval.median)
        self.assertLess(interval.median, interval.ci_upper)
        self.assertGreater(interval.ci_lower, 0)

        # Imputation penalty inflates uncertainty width
        interval_imputed = bayes.compute_interval(
            predicted_mean=3000.0,
            metric_key="cmj_peak_power_w",
            unit="Watts",
            missing_count=4,
        )
        self.assertGreater(
            interval_imputed.ci_upper - interval_imputed.ci_lower,
            interval.ci_upper - interval.ci_lower,
        )

    def test_bayesian_longitudinal_updating_shrinkage(self):
        bayes = BayesianPowerEngine()
        # Prior mean = 50 cm
        history = [
            {"date": "2026-01-01", "value": 55.0, "unit": "cm"},
            {"date": "2026-03-01", "value": 56.0, "unit": "cm"},
            {"date": "2026-05-01", "value": 55.5, "unit": "cm"},
            {"date": "2026-07-01", "value": 57.0, "unit": "cm"},
        ]
        series = bayes.update_longitudinal_series(
            baseline_prior_mean=50.0,
            metric_key="cmj_height_cm",
            test_history=history,
        )
        self.assertEqual(len(series), 4)
        # Uncertainty percentage should decrease as observations accumulate
        self.assertLess(series[-1]["uncertainty_pct"], series[0]["uncertainty_pct"])
        # Posterior median shifts toward observed data (~56 cm)
        self.assertGreater(series[-1]["posterior_median"], 53.0)

    def test_athlete_profiler_end_to_end(self):
        profiler = AthleteProfiler()
        p = InputProfile(name="Test Subject", body_mass=80.0, height=180.0)
        res = profiler.profile_athlete(p)

        self.assertIn("movement_predictions", res)
        preds = res["movement_predictions"]
        self.assertIn("cmj_height_cm", preds)
        self.assertIn("sprint_vmax_m_s", preds)
        self.assertIn("olympic_snatch_power_w", preds)
        self.assertIn("striking_impact_force_n", preds)
        self.assertIn("grappling_thrust_force_n", preds)

        # Check intervals
        for key, item in preds.items():
            self.assertLessEqual(item["ci_lower"], item["median"])
            self.assertLessEqual(item["median"], item["ci_upper"])

        # Check SHAP decomposition
        shap_res = res["shap_attribution"]
        self.assertIn("predicted_power_w", shap_res)
        self.assertGreater(len(shap_res["breakdown"]), 0)

    def test_synthetic_cohort_labeling(self):
        df = CohortManager.generate_benchmark_synthetic_cohort(20)
        self.assertTrue((df["DATA_ORIGIN"] == "SYNTHETIC_BENCHMARK").all())
        self.assertEqual(len(df), 20)
        self.assertIn("Athlete_ID", df.columns)


if __name__ == "__main__":
    unittest.main()
