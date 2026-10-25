"""
Layer 1: Biomechanical Deterministic Layer
Computes allometric scaling, lever ratios, Hill-type force-velocity dynamics,
muscle architecture proxies, and elastic strain energy return.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple
from .config import InputProfile, EvidenceGrade


def calculate_segment_ratios(p: InputProfile) -> Dict[str, Any]:
    """Computes biomechanical segment lever arms and ratios."""
    femur = p.femur_length or (0.245 * p.height)
    tibia = p.tibia_length or (0.215 * p.height)
    foot = p.foot_length or (0.152 * p.height)
    calcaneus = p.calcaneus_length or (0.20 * foot)
    forefoot = max(5.0, foot - calcaneus)
    torso = p.torso_length or (0.300 * p.height)
    arm_span = p.arm_span or (p.height * 1.02)
    leg_length = femur + tibia

    # 1. Crural Index (tibia / femur)
    crural_index = tibia / femur if femur > 0 else 0.88

    # 2. Ankle Gear Ratio (forefoot lever / calcaneus moment arm)
    # High gear ratio (> 3.8) favors high sprint speed; low gear ratio (< 3.2) favors heavy lifting torque
    ankle_gear_ratio = forefoot / calcaneus if calcaneus > 0 else 3.5

    # 3. Ape Index (arm span - height in cm) and ratio
    ape_index_diff = arm_span - p.height
    ape_index_ratio = arm_span / p.height if p.height > 0 else 1.0

    # 4. Torso-to-Leg Ratio
    torso_to_leg = torso / leg_length if leg_length > 0 else 0.55

    return {
        "crural_index": round(crural_index, 3),
        "crural_index_eval": (
            "High (>0.88, sprint/speed favored)"
            if crural_index >= 0.88
            else "Moderate/Low (<0.85, torque/lifting favored)"
        ),
        "ankle_gear_ratio": round(ankle_gear_ratio, 2),
        "ankle_gear_eval": (
            "High Gear (>3.6: Speed/Sprint velocity optimized)"
            if ankle_gear_ratio >= 3.6
            else "Low Gear / High Mechanical Advantage (<3.3: High torque / Heavy load optimized)"
        ),
        "ape_index_diff_cm": round(ape_index_diff, 1),
        "ape_index_ratio": round(ape_index_ratio, 3),
        "torso_to_leg_ratio": round(torso_to_leg, 3),
        "total_leg_length_cm": round(leg_length, 1),
        "calcaneus_moment_arm_cm": round(calcaneus, 2),
        "forefoot_lever_cm": round(forefoot, 2),
    }


def estimate_muscle_architecture(p: InputProfile, ratios: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimates muscle architecture parameters (fascicle length, pennation angle, PCSA proxy)
    using ultrasound if provided, or empirical regression from anthropometry.
    """
    femur = p.femur_length or (0.245 * p.height)
    thigh_g = p.thigh_girth or (56.0 * (p.body_mass / 75.0) ** 0.33)
    bf_frac = p.body_fat_pct / 100.0

    # 1. Fascicle Length (cm) of Vastus Lateralis
    if p.us_fascicle_length_cm is not None and p.us_fascicle_length_cm > 0:
        fascicle_length = p.us_fascicle_length_cm
        lf_source = "Direct Ultrasound Measurement"
        lf_uncertainty = 0.35  # cm
    else:
        # Base allometry: ~19.2% of femur length with genotype/training modifiers
        actn3_boost = 0.03 if p.actn3_genotype == "RR" else (-0.02 if p.actn3_genotype == "XX" else 0.0)
        crural_mod = (ratios["crural_index"] - 0.86) * 0.15
        fascicle_length = round(0.192 * femur * (1.0 + actn3_boost + crural_mod), 2)
        lf_source = "Estimated from Segment Allometry"
        lf_uncertainty = 1.15  # cm

    # 2. Pennation Angle (degrees)
    if p.us_pennation_angle_deg is not None and p.us_pennation_angle_deg > 0:
        pennation_deg = p.us_pennation_angle_deg
        theta_source = "Direct Ultrasound Measurement"
        theta_uncertainty = 1.2  # deg
    else:
        # Thigh thickness relative to femur length drives pennation angle
        girth_to_length_ratio = (thigh_g / femur) * 100.0 if femur > 0 else 135.0
        pennation_deg = round(11.2 + 0.065 * (girth_to_length_ratio - 110.0), 1)
        pennation_deg = float(np.clip(pennation_deg, 11.0, 24.0))
        theta_source = "Estimated from Girth/Lever Ratio"
        theta_uncertainty = 2.4  # deg

    # 3. Thigh Lean Muscle Volume & PCSA Proxy (Bilateral Quadriceps)
    # Subcutaneous fat thickness estimate from body fat %
    subcut_fat_cm = max(0.2, (bf_frac * 2.2))
    radius_thigh_cm = max(4.5, (thigh_g / (2.0 * math.pi)) - subcut_fat_cm)
    thigh_muscle_csa = math.pi * (radius_thigh_cm ** 2)  # cm^2 total thigh cross-section
    # Quadriceps represents ~45% of thigh musculature; bilateral (2 legs)
    quad_vol_bilateral = (thigh_muscle_csa * 0.45) * femur * 0.72 * 2.0  # cm^3

    theta_rad = math.radians(pennation_deg)
    pcsa_proxy = (quad_vol_bilateral * math.cos(theta_rad)) / max(4.0, fascicle_length)

    # 4. Fast-Twitch (Type II) Fiber Propensity Proxy (0 - 100%)
    if p.fiber_type_ii_pct is not None:
        fiber_type_ii = p.fiber_type_ii_pct
        fiber_source = "Direct Biopsy / TMG Proxy"
        fiber_uncertainty = 4.0
    else:
        # Bayesian prior combining ACTN3, gear ratio, and crural index
        base_fiber = 52.0  # general human population mean
        if p.actn3_genotype == "RR":
            base_fiber += 4.5
        elif p.actn3_genotype == "XX":
            base_fiber -= 3.5

        if ratios["crural_index"] > 0.90:
            base_fiber += 3.0
        if ratios["ankle_gear_ratio"] > 3.8:
            base_fiber += 2.5
        fiber_type_ii = round(float(np.clip(base_fiber, 35.0, 78.0)), 1)
        fiber_source = "Prior Composite (Biomechanical & Genetic Markers)"
        fiber_uncertainty = 12.0  # High uncertainty when non-invasive

    return {
        "fascicle_length_cm": round(fascicle_length, 2),
        "fascicle_length_sd": round(lf_uncertainty, 2),
        "fascicle_source": lf_source,
        "pennation_angle_deg": round(pennation_deg, 1),
        "pennation_angle_sd": round(theta_uncertainty, 1),
        "pennation_source": theta_source,
        "pcsa_proxy_cm2": round(pcsa_proxy, 1),
        "thigh_muscle_csa_cm2": round(thigh_muscle_csa, 1),
        "fiber_type_ii_pct": round(fiber_type_ii, 1),
        "fiber_type_ii_sd": round(fiber_uncertainty, 1),
        "fiber_source": fiber_source,
    }


def compute_force_velocity_profile(
    p: InputProfile, ratios: Dict[str, Any], arch: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes lower-limb ballistic Force-Velocity-Power characteristics:
    F0 (theoretical isometric force), V0 (maximum shortening velocity),
    Pmax (maximum mechanical power), and optimal F-V profile comparison.
    """
    mass = p.body_mass
    lean = p.lean_mass or (mass * (1.0 - p.body_fat_pct / 100.0))
    pcsa = arch["pcsa_proxy_cm2"]
    lf = arch["fascicle_length_cm"]
    gear = ratios["ankle_gear_ratio"]
    crural = ratios["crural_index"]

    # 1. Theoretical Isometric Force F0 (N)
    # Effective vertical ground reaction force at zero velocity (Samozino et al., 2012)
    # Lever-reduced PCSA specific tension + lean mass allometry (lean^0.67)
    mech_adv_factor = (3.5 / gear) ** 0.5  # higher calcaneus arm increases force capacity
    f0_base = (pcsa * 7.8 + 24.0 * (lean ** 0.67)) * mech_adv_factor
    f0 = f0_base * (1.0 + (arch["fiber_type_ii_pct"] - 50.0) * 0.003)

    # 2. Theoretical Maximum Velocity V0 (m/s)
    # Governed by fascicle length (sarcomeres in series), fast-twitch %, crural index, gear ratio
    v0_base = 2.40 + (lf - 8.0) * 0.22 + (crural - 0.86) * 1.5 + (gear - 3.5) * 0.18
    v0_mod = (arch["fiber_type_ii_pct"] - 50.0) * 0.015
    v0 = max(1.8, v0_base + v0_mod)

    # 3. Maximum Mechanical Power Pmax (Watts)
    # Hill parabolic peak: Pmax = (F0 * V0) / 4
    pmax = (f0 * v0) / 4.0
    sfv = f0 / v0  # Slope (N*s/m)

    # 4. Optimal F-V Profile for Ballistic Push-off (Samozino et al., 2014)
    # Push-off distance h_po estimate from leg length and squat depth
    h_po = max(0.30, ratios["total_leg_length_cm"] * 0.01 * 0.44)  # ~0.35-0.42 m
    g = 9.81
    sfv_opt = (mass * g) / (h_po * math.sqrt(2.0 * g * h_po))
    fv_imbalance_pct = ((sfv - sfv_opt) / sfv_opt) * 100.0

    if fv_imbalance_pct > 15.0:
        deficit_diagnosis = "Force Deficit (Heavy load strength training prioritized)"
    elif fv_imbalance_pct < -15.0:
        deficit_diagnosis = "Velocity Deficit (High-speed ballistic & plyometric training prioritized)"
    else:
        deficit_diagnosis = "Well-Balanced Force-Velocity Profile"

    # Allometric normalization (Jaric 2002)
    pmax_allometric = pmax / (mass ** 0.67)
    pmax_per_kg = pmax / mass

    return {
        "f0_n": round(f0, 1),
        "v0_m_s": round(v0, 2),
        "pmax_watts": round(pmax, 1),
        "pmax_allometric": round(pmax_allometric, 2),  # W / kg^0.67
        "pmax_per_kg": round(pmax_per_kg, 2),  # W / kg
        "sfv_actual": round(sfv, 1),
        "sfv_optimal": round(sfv_opt, 1),
        "fv_imbalance_pct": round(fv_imbalance_pct, 1),
        "deficit_diagnosis": deficit_diagnosis,
        "push_off_distance_m": round(h_po, 3),
    }


def compute_elastic_and_fascial_contribution(
    p: InputProfile, arch: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes series elastic component (SEC) tendon strain energy,
    foot arch windlass mechanism contribution, and flags distant fascial chain uncertainty.
    """
    # 1. Tendon Stiffness (N/mm)
    if p.tendon_stiffness_n_mm is not None and p.tendon_stiffness_n_mm > 0:
        k_tendon = p.tendon_stiffness_n_mm
        k_source = "Measured Ultrasound / Shear Wave"
    else:
        # Normative average: ~520 N/mm in trained athletes, modified by lean mass
        k_tendon = 480.0 + 3.2 * (p.lean_mass or 65.0)
        k_source = "Normative Tendon Model"

    # Elastic strain energy stored in Achilles tendon during fast ground impact (~3.5 kN load)
    peak_achilles_force = max(2000.0, p.body_mass * 9.81 * 4.2)  # N
    tendon_elongation_mm = peak_achilles_force / k_tendon
    # Strain energy U = 0.5 * k * x^2
    u_strain_joules = 0.5 * (k_tendon * 1000.0) * ((tendon_elongation_mm / 1000.0) ** 2)
    recoil_efficiency = 0.92  # 8% hysteresis loss (Bojsen-Moller 2005)
    elastic_energy_return_j = u_strain_joules * recoil_efficiency

    # 2. Foot Arch & Windlass Mechanism Contribution
    fpi = p.fpi_6 if p.fpi_6 is not None else 0.0
    # Neutral arch (-1 to +4) optimizes elastic return; severe pronation (>+6) or supination (<-2) dissipates energy
    if -1.0 <= fpi <= 4.0:
        arch_stiffness_factor = 1.0
        arch_status = "Optimal Longitudinal Arch Stiffness (Efficient Windlass)"
    elif fpi > 4.0:
        arch_stiffness_factor = max(0.85, 1.0 - (fpi - 4.0) * 0.03)
        arch_status = "Excessive Pronation / Arch Collapse (Moderate Energy Dissipation)"
    else:
        arch_stiffness_factor = max(0.88, 1.0 + (fpi + 1.0) * 0.025)
        arch_status = "Rigid Supinated Arch (Lower Shock Absorption)"

    # Hallux strength bonus
    hallux_n = p.hallux_flexor_strength_n if p.hallux_flexor_strength_n is not None else 180.0
    hallux_propulsion_factor = 1.0 + (hallux_n - 180.0) * 0.0004

    # 3. SSC Augmentation (CMJ vs SJ Pre-stretch Potentiation Ratio)
    # Typical SSC boost is +10% to +18% in power athletes
    ssc_boost_pct = 12.0 * (k_tendon / 550.0) * arch_stiffness_factor
    ssc_boost_pct = float(np.clip(ssc_boost_pct, 6.0, 24.0))

    # 4. Critical Appraisal of Distant "Fascial Chains"
    fascia_kpa = p.fascia_shear_modulus_kpa if p.fascia_shear_modulus_kpa is not None else 45.0
    # Empirical science shows <10-15% passive force transmission; active contraction isolates compartments
    fascia_uncertainty_note = (
        "Evidence Grade: SPECULATIVE. Long-distance myofascial force transmission across remote joints "
        "is attenuated by >85% due to tissue compliance and active muscle compartment stiffening (Wilke et al., 2016). "
        "Elastic strain energy is primarily localized to the triceps surae-Achilles tendon and plantar fascia."
    )

    return {
        "tendon_stiffness_n_mm": round(k_tendon, 1),
        "tendon_elongation_mm": round(tendon_elongation_mm, 2),
        "elastic_energy_return_joules": round(elastic_energy_return_j, 1),
        "ssc_pre_stretch_augmentation_pct": round(ssc_boost_pct, 1),
        "arch_stiffness_factor": round(arch_stiffness_factor, 2),
        "arch_status": arch_status,
        "hallux_propulsion_factor": round(hallux_propulsion_factor, 3),
        "fascia_uncertainty_note": fascia_uncertainty_note,
        "evidence_grade_local_tendon": EvidenceGrade.MODERATE.value,
        "evidence_grade_fascial_chain": EvidenceGrade.SPECULATIVE.value,
    }
