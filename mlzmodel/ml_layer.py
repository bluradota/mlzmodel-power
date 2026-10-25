"""
Layer 3: Interpretable Machine Learning & SHAP Explainer Layer
Provides Gradient Boosting and regularized regression with local SHAP feature attribution
to decompose power predictions into physiological drivers.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
import shap


class InterpretablePowerModel:
    """
    Interpretable machine learning wrapper trained on empirical-allometric distributions.
    Computes local SHAP explanations for any athlete prediction.
    """

    FEATURE_NAMES = [
        "body_mass",
        "lean_mass",
        "height",
        "femur_length",
        "tibia_length",
        "crural_index",
        "ankle_gear_ratio",
        "fascicle_length_cm",
        "pennation_deg",
        "pcsa_proxy_cm2",
        "fiber_type_ii_pct",
        "tendon_stiffness",
    ]

    def __init__(self, target_name: str = "CMJ Peak Power (W)"):
        self.target_name = target_name
        self.model = GradientBoostingRegressor(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.08,
            random_state=42,
        )
        self.explainer: Optional[shap.TreeExplainer] = None
        self.is_fitted = False
        self._fit_default_baseline()

    def _fit_default_baseline(self):
        """Fits on standard simulated cohort that respects physiological covariance."""
        np.random.seed(42)
        n_samples = 400

        # Generate realistic physiological distributions
        mass = np.random.normal(78.0, 11.0, n_samples)
        mass = np.clip(mass, 50.0, 125.0)
        bf = np.random.normal(14.0, 5.0, n_samples)
        bf = np.clip(bf, 6.0, 30.0)
        lean = mass * (1.0 - bf / 100.0)
        height = np.random.normal(178.0, 8.5, n_samples)
        femur = 0.245 * height + np.random.normal(0, 1.2, n_samples)
        tibia = 0.215 * height + np.random.normal(0, 1.1, n_samples)
        crural = tibia / femur
        calcaneus = 0.03 * height + np.random.normal(0, 0.4, n_samples)
        forefoot = 0.12 * height + np.random.normal(0, 0.8, n_samples)
        gear = forefoot / np.clip(calcaneus, 3.5, 7.0)

        lf = 0.192 * femur + np.random.normal(0, 0.7, n_samples)
        penn = 14.5 + 0.12 * (mass / 75.0) * 15.0 + np.random.normal(0, 1.5, n_samples)
        pcsa = (lean * 3.8) * np.cos(np.radians(penn)) / np.clip(lf, 4.0, 12.0)
        fiber = np.random.normal(52.0, 9.0, n_samples)
        k_tendon = 450.0 + 3.0 * lean + np.random.normal(0, 45.0, n_samples)

        X = np.column_stack([
            mass,
            lean,
            height,
            femur,
            tibia,
            crural,
            gear,
            lf,
            penn,
            pcsa,
            fiber,
            k_tendon,
        ])

        # Underlying biomechanical ground-truth for CMJ Peak Power:
        # Allometric scaling (lean^0.67), PCSA contribution, fascicle length for V0, tendon elasticity
        y = (
            55.0 * (lean ** 0.67)
            + 6.5 * pcsa
            + 45.0 * (lf - 8.0)
            + 180.0 * (crural - 0.86)
            + 0.35 * k_tendon
            + 4.0 * (fiber - 50.0)
            + np.random.normal(0, 150.0, n_samples)
        )

        self.model.fit(X, y)
        self.explainer = shap.TreeExplainer(self.model)
        self.is_fitted = True

    def explain_instance(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Computes local SHAP decomposition for an individual athlete.
        Returns base value and list of feature impacts in Watts.
        """
        if not self.is_fitted or self.explainer is None:
            self._fit_default_baseline()

        feat_2d = feature_vector.reshape(1, -1)
        pred_val = float(self.model.predict(feat_2d)[0])
        shap_values = self.explainer.shap_values(feat_2d)[0]
        base_val = float(self.explainer.expected_value[0]) if isinstance(self.explainer.expected_value, (list, np.ndarray)) else float(self.explainer.expected_value)

        shap_breakdown = []
        for name, val, s_val in zip(self.FEATURE_NAMES, feature_vector, shap_values):
            shap_breakdown.append({
                "feature": name,
                "input_value": round(float(val), 2),
                "shap_impact_watts": round(float(s_val), 1),
                "direction": "Positive (+)" if s_val >= 0 else "Negative (-)",
            })

        # Sort by absolute magnitude of contribution
        shap_breakdown.sort(key=lambda x: abs(x["shap_impact_watts"]), reverse=True)

        return {
            "predicted_power_w": round(pred_val, 1),
            "base_value_w": round(base_val, 1),
            "breakdown": shap_breakdown,
        }
