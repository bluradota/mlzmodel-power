"""
Layer 2: Statistical Bayesian Layer & Uncertainty Engine
Computes Bayesian prediction intervals (5th, 50th, 95th percentiles),
principled missingness uncertainty propagation, and longitudinal Bayesian updating.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PredictionInterval:
    median: float
    ci_lower: float  # 5th percentile
    ci_upper: float  # 95th percentile
    unit: str
    relative_uncertainty_pct: float
    imputation_penalty_applied: bool

    def as_dict(self) -> Dict[str, Any]:
        return {
            "median": round(self.median, 2),
            "ci_lower": round(self.ci_lower, 2),
            "ci_upper": round(self.ci_upper, 2),
            "interval_formatted": f"{round(self.median, 1)} [{round(self.ci_lower, 1)} - {round(self.ci_upper, 1)}] {self.unit}",
            "unit": self.unit,
            "uncertainty_pct": round(self.relative_uncertainty_pct, 1),
            "imputation_penalty": self.imputation_penalty_applied,
        }


class BayesianPowerEngine:
    """
    Manages empirical priors, handles missing variable variance inflation,
    and performs conjugate Bayesian updating for longitudinal test sessions.
    """

    def __init__(self):
        # Normative residual standard errors (RMSE in real units) from cross-validation
        self.base_rmse = {
            "cmj_height_cm": 3.2,
            "cmj_peak_power_w": 340.0,
            "sprint_vmax_m_s": 0.35,
            "sprint_10m_s": 0.052,
            "squat_jump_cm": 3.0,
            "olympic_snatch_power_w": 410.0,
            "cycling_5s_peak_w": 120.0,
            "rowing_500m_w": 38.0,
            "striking_impact_force_n": 220.0,
            "kicking_ball_velocity_m_s": 2.8,
            "grappling_thrust_force_n": 210.0,
        }

    def compute_interval(
        self,
        predicted_mean: float,
        metric_key: str,
        unit: str,
        missing_count: int = 0,
        repeat_observations: Optional[List[float]] = None,
    ) -> PredictionInterval:
        """
        Calculates 90% prediction intervals (5th, 50th, 95th percentiles).
        Applies Bayesian updating if repeat tests exist, and inflates interval width
        if key structural inputs were imputed.
        """
        sigma_base = self.base_rmse.get(metric_key, predicted_mean * 0.08)

        # Missing input penalty: Each missing measurement inflates residual standard error by ~6%
        imputation_penalty = missing_count > 0
        sigma_inflated = sigma_base * (1.0 + 0.06 * min(missing_count, 6))

        # Bayesian conjugate updating if repeat test observations exist
        if repeat_observations and len(repeat_observations) > 0:
            # Prior: N(predicted_mean, sigma_inflated^2)
            # Likelihood: N(theta, sigma_meas^2)
            sigma_meas = sigma_base * 0.7  # measurement error
            n_obs = len(repeat_observations)
            obs_mean = float(np.mean(repeat_observations))

            prior_prec = 1.0 / (sigma_inflated ** 2)
            lik_prec = n_obs / (sigma_meas ** 2)
            post_prec = prior_prec + lik_prec
            post_sigma = math.sqrt(1.0 / post_prec)
            post_mean = (prior_prec * predicted_mean + lik_prec * obs_mean) / post_prec

            # Total predictive variance = posterior variance + measurement variance
            pred_sigma = math.sqrt(post_sigma ** 2 + sigma_meas ** 2)
            center = post_mean
        else:
            center = predicted_mean
            pred_sigma = sigma_inflated

        # 90% interval: z = 1.645
        z_90 = 1.645
        lower = max(0.0, center - z_90 * pred_sigma)
        upper = center + z_90 * pred_sigma
        uncertainty_pct = ((upper - lower) / (2.0 * max(1e-5, center))) * 100.0

        return PredictionInterval(
            median=center,
            ci_lower=lower,
            ci_upper=upper,
            unit=unit,
            relative_uncertainty_pct=uncertainty_pct,
            imputation_penalty_applied=imputation_penalty,
        )

    def update_longitudinal_series(
        self,
        baseline_prior_mean: float,
        metric_key: str,
        test_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Simulates longitudinal Bayesian tracking: as an athlete logs repeated test sessions,
        the model dynamically updates the posterior belief and narrows prediction intervals.
        """
        results = []
        accumulated_obs = []

        sigma_base = self.base_rmse.get(metric_key, baseline_prior_mean * 0.08)

        for session in test_history:
            date_str = session.get("date", "Unknown Date")
            val = session.get("value")
            if val is not None:
                accumulated_obs.append(float(val))

            interval = self.compute_interval(
                predicted_mean=baseline_prior_mean,
                metric_key=metric_key,
                unit=session.get("unit", "Units"),
                missing_count=0,
                repeat_observations=accumulated_obs if len(accumulated_obs) > 0 else None,
            )

            results.append({
                "date": date_str,
                "recorded_value": val,
                "posterior_median": round(interval.median, 2),
                "ci_lower": round(interval.ci_lower, 2),
                "ci_upper": round(interval.ci_upper, 2),
                "uncertainty_pct": round(interval.relative_uncertainty_pct, 1),
                "n_cumulative_tests": len(accumulated_obs),
            })

        return results
