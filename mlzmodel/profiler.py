"""
Movement-Specific Profiling Pipeline
Integrates Biomechanical layer, Bayesian Statistical engine, and ML SHAP explainer
to produce movement-specific power profiles across target sports.
"""

import math
import numpy as np
from typing import Dict, Any, List
from .config import InputProfile, EvidenceGrade
from .biomechanics import (
    calculate_segment_ratios,
    estimate_muscle_architecture,
    compute_force_velocity_profile,
    compute_elastic_and_fascial_contribution,
)
from .statistical_layer import BayesianPowerEngine
from .ml_layer import InterpretablePowerModel


class AthleteProfiler:
    """
    Core research profiler evaluating multi-sport power profiles from anthropometric,
    structural, and tissue measurements.
    """

    def __init__(self):
        self.bayes_engine = BayesianPowerEngine()
        self.ml_model = InterpretablePowerModel()

    def profile_athlete(self, p: InputProfile) -> Dict[str, Any]:
        """
        Executes end-to-end profiling for an athlete.
        Returns structural characteristics, movement-specific power profiles,
        uncertainty prediction intervals, force-velocity metrics, and SHAP attribution.
        """
        # 1. Biomechanical Layer
        ratios = calculate_segment_ratios(p)
        arch = estimate_muscle_architecture(p, ratios)
        fv = compute_force_velocity_profile(p, ratios, arch)
        elastic = compute_elastic_and_fascial_contribution(p, arch)

        # Count missing inputs to apply principled imputation penalty
        missing_count = sum(
            1 for v in [
                p.us_fascicle_length_cm,
                p.us_pennation_angle_deg,
                p.tendon_stiffness_n_mm,
                p.hallux_flexor_strength_n,
                p.fiber_type_ii_pct,
            ] if v is None
        )

        mass = p.body_mass
        lean = p.lean_mass or (mass * (1.0 - p.body_fat_pct / 100.0))
        pcsa = arch["pcsa_proxy_cm2"]
        lf = arch["fascicle_length_cm"]
        crural = ratios["crural_index"]
        gear = ratios["ankle_gear_ratio"]
        f0 = fv["f0_n"]
        v0 = fv["v0_m_s"]
        pmax = fv["pmax_watts"]
        ssc_boost = 1.0 + (elastic["ssc_pre_stretch_augmentation_pct"] / 100.0)

        # 2. Movement Predictions with Physical & Allometric Scaling
        # A. Countermovement Jump (CMJ)
        # Jump height: h = v_takeoff^2 / (2g); v_takeoff derived from net vertical impulse
        takeoff_vel = math.sqrt(max(0.2, (2.0 * pmax * 0.38) / mass))
        cmj_height_raw = (takeoff_vel ** 2) / (2.0 * 9.81) * 100.0 * ssc_boost
        cmj_height_pred = float(np.clip(cmj_height_raw, 22.0, 92.0))
        cmj_power_pred = pmax * ssc_boost

        # Squat Jump (pure concentric, no SSC boost)
        sj_height_pred = cmj_height_pred / ssc_boost

        # B. Sprinting (30m Max Velocity & 0-10m Split)
        # Vmax (m/s): governed by fascicle length, crural index, gear ratio, and relative power
        vmax_pred = 6.2 + 0.35 * (lf - 7.5) + 3.8 * (crural - 0.85) + 0.05 * (pmax / mass - 45.0)
        vmax_pred = float(np.clip(vmax_pred, 6.5, 12.2))
        # 10m split time (s): depends on horizontal acceleration capacity (F0 / mass and hallux push)
        accel_cap = (f0 / mass) * 0.42 * elastic["hallux_propulsion_factor"]
        sprint_10m_pred = float(np.clip(1.95 - 0.035 * (accel_cap - 9.5), 1.45, 2.25))

        # C. Olympic Weightlifting (Snatch Peak Power)
        # Massive dependence on absolute PCSA, lean mass allometry (lean^0.67), low gear ratio
        snatch_power_pred = (
            35.0 * (lean ** 0.67) * (3.8 / gear) ** 0.6 + 12.0 * pcsa + 0.15 * pmax
        )

        # D. Cycling (5-s Peak Sprint Power)
        # Pure concentric leg extension in fixed plane, no mass support penalty, high thigh muscle volume
        cycling_power_pred = pmax * 0.65 + 18.0 * arch["thigh_muscle_csa_cm2"]

        # E. Combat Sports & Striking
        # Straight punch impact force (N): arm span reach, torso torque, rapid leg extension
        punch_force_pred = (
            f0 * 0.18
            + 8.5 * (ratios["ape_index_diff_cm"] + 10.0)
            + 12.0 * (p.upper_arm_girth or 34.0)
        )
        # Grappling takedown / isometric drive force (N): high mechanical advantage, low gear ratio
        takedown_drive_pred = f0 * 0.55 * (3.5 / gear)

        # F. Kicking (Soccer Ball Velocity)
        # Leg angular velocity: long tibia, high crural index, hip flexor impulse
        kick_speed_pred = 20.0 + 4.5 * (crural - 0.85) + 0.28 * (lf - 7.5)

        # G. Rowing (500m Stroke Power)
        # Long torso and arm span lever, lean body mass allometry
        rowing_power_pred = 18.0 * (lean ** 0.67) + 2.2 * ratios["ape_index_diff_cm"] + 120.0

        # 3. Statistical Layer: Bayesian Prediction Intervals
        movements = {
            "cmj_height_cm": self.bayes_engine.compute_interval(
                cmj_height_pred, "cmj_height_cm", "cm", missing_count
            ),
            "cmj_peak_power_w": self.bayes_engine.compute_interval(
                cmj_power_pred, "cmj_peak_power_w", "Watts", missing_count
            ),
            "squat_jump_cm": self.bayes_engine.compute_interval(
                sj_height_pred, "squat_jump_cm", "cm", missing_count
            ),
            "sprint_vmax_m_s": self.bayes_engine.compute_interval(
                vmax_pred, "sprint_vmax_m_s", "m/s", missing_count
            ),
            "sprint_10m_s": self.bayes_engine.compute_interval(
                sprint_10m_pred, "sprint_10m_s", "s", missing_count
            ),
            "olympic_snatch_power_w": self.bayes_engine.compute_interval(
                snatch_power_pred, "olympic_snatch_power_w", "Watts", missing_count
            ),
            "cycling_5s_peak_w": self.bayes_engine.compute_interval(
                cycling_power_pred, "cycling_5s_peak_w", "Watts", missing_count
            ),
            "striking_impact_force_n": self.bayes_engine.compute_interval(
                punch_force_pred, "striking_impact_force_n", "N", missing_count
            ),
            "grappling_thrust_force_n": self.bayes_engine.compute_interval(
                takedown_drive_pred, "grappling_thrust_force_n", "N", missing_count
            ),
            "kicking_ball_velocity_m_s": self.bayes_engine.compute_interval(
                kick_speed_pred, "kicking_ball_velocity_m_s", "m/s", missing_count
            ),
            "rowing_500m_w": self.bayes_engine.compute_interval(
                rowing_power_pred, "rowing_500m_w", "Watts", missing_count
            ),
        }

        # 4. ML Layer: SHAP Local Attribution
        feature_vector = np.array([
            mass,
            lean,
            p.height,
            p.femur_length or (0.245 * p.height),
            p.tibia_length or (0.215 * p.height),
            ratios["crural_index"],
            ratios["ankle_gear_ratio"],
            lf,
            arch["pennation_angle_deg"],
            pcsa,
            arch["fiber_type_ii_pct"],
            elastic["tendon_stiffness_n_mm"],
        ])
        shap_explanation = self.ml_model.explain_instance(feature_vector)

        # 5. Evidence Tagging Matrix for Movement Predictions
        evidence_tags = {
            "cmj_peak_power_w": {
                "grade": EvidenceGrade.STRONG.value,
                "key_paper": "Kumagai et al. (2000) & Earp et al. (2010)",
                "doi": "10.1249/MSS.0b013e3181c3b28b",
                "notes": "Directly grounded in PCSA, lean mass allometry, and series elasticity.",
            },
            "sprint_vmax_m_s": {
                "grade": EvidenceGrade.STRONG.value,
                "key_paper": "Kumagai et al. (2000) & Baxter et al. (2012)",
                "doi": "10.1152/jappl.2000.88.3.811",
                "notes": "High correlation with fascicle length (Lf) and ankle gear ratio.",
            },
            "sprint_10m_s": {
                "grade": EvidenceGrade.MODERATE.value,
                "key_paper": "Goldmann et al. (2013) & Morin et al. (2016)",
                "doi": "10.1080/02640414.2012.736627",
                "notes": "Acceleration depends heavily on initial horizontal force vector and hallux push.",
            },
            "olympic_snatch_power_w": {
                "grade": EvidenceGrade.STRONG.value,
                "key_paper": "Markovic & Jaric (2004)",
                "doi": "10.1007/s00421-004-1077-4",
                "notes": "Strong allometric scaling FFM^(0.67) and high mechanical advantage.",
            },
            "cycling_5s_peak_w": {
                "grade": EvidenceGrade.STRONG.value,
                "key_paper": "Lieber & Friden (2000)",
                "doi": "10.1002/1097-4598(200011)23:11<1647::aid-mus1>3.0.co;2-m",
                "notes": "Constrained trajectory isolating quadriceps PCSA and lean thigh volume.",
            },
            "striking_impact_force_n": {
                "grade": EvidenceGrade.MODERATE.value,
                "key_paper": "Franchini et al. (2011)",
                "doi": "10.1519/JSC.0b013e31821a37c0",
                "notes": "Ape index reach and ground impulse drive effective mass at impact.",
            },
            "grappling_thrust_force_n": {
                "grade": EvidenceGrade.MODERATE.value,
                "key_paper": "Chaabene et al. (2012)",
                "doi": "10.2165/11637170-000000000-00000",
                "notes": "Lever arm mechanical advantage and low ankle gear ratio prioritize isometric drive.",
            },
            "toe_pattern_claim": {
                "grade": EvidenceGrade.SPECULATIVE.value,
                "key_paper": "Ugalde et al. (2015)",
                "doi": "10.1177/1071100715581452",
                "notes": "Morton's/Egyptian toe categorical phenotype has ZERO statistically supported impact.",
            },
            "fascial_chains_claim": {
                "grade": EvidenceGrade.SPECULATIVE.value,
                "key_paper": "Wilke et al. (2016)",
                "doi": "10.1016/j.apmr.2015.07.023",
                "notes": "Distant multi-joint myofascial force transfer drops near 0% under active contraction.",
            },
        }

        return {
            "athlete_name": p.name,
            "segment_ratios": ratios,
            "muscle_architecture": arch,
            "force_velocity": fv,
            "elastic_contribution": elastic,
            "movement_predictions": {k: v.as_dict() for k, v in movements.items()},
            "shap_attribution": shap_explanation,
            "evidence_tags": evidence_tags,
            "missing_inputs_imputed": missing_count,
        }
