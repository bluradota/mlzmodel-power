"""
Configuration, schema constants, and evidence taxonomies.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class EvidenceGrade(str, Enum):
    STRONG = "Strong (Replicated / Meta-Analytic)"
    MODERATE = "Moderate (Consistent Experimental / Biomechanical)"
    WEAK = "Weak or Conflicting (Indirect / Small N)"
    SPECULATIVE = "Speculative (Folk Myth / Contradicted by Data)"


@dataclass
class InputProfile:
    # Basic
    name: str = "Athlete 01"
    age: float = 24.0
    sex: str = "male"  # 'male' or 'female'
    height: float = 180.0  # cm
    body_mass: float = 80.0  # kg
    body_fat_pct: float = 12.0  # %
    body_fat_method: str = "DEXA"  # 'DEXA', 'Caliper (7-site)', 'BIA', 'Estimated'
    lean_mass: Optional[float] = None  # kg (auto-calculated if None)

    # Segment lengths (cm)
    femur_length: Optional[float] = None
    tibia_length: Optional[float] = None
    foot_length: Optional[float] = None
    humerus_length: Optional[float] = None
    forearm_length: Optional[float] = None
    hand_length: Optional[float] = None
    torso_length: Optional[float] = None
    arm_span: Optional[float] = None
    calcaneus_length: Optional[float] = None  # Achilles tendon moment arm proxy (cm)

    # Circumferences (cm)
    thigh_girth: Optional[float] = None
    calf_girth: Optional[float] = None
    upper_arm_girth: Optional[float] = None
    chest_girth: Optional[float] = None
    waist_girth: Optional[float] = None
    hip_girth: Optional[float] = None

    # Foot metrics
    fpi_6: Optional[float] = 0.0  # Foot Posture Index (-12 to +12, 0 is neutral)
    arch_height_index: Optional[float] = 0.34  # normalized arch height
    navicular_drop: Optional[float] = 6.0  # mm
    toe_length_pattern: str = "Egyptian (Big toe longest)"  # 'Egyptian', 'Greek/Morton', 'Roman (Square)'
    hallux_flexor_strength_n: Optional[float] = None  # N (isometric hallux force)

    # Optional Performance Data
    cmj_height_cm: Optional[float] = None
    squat_jump_cm: Optional[float] = None
    sprint_10m_s: Optional[float] = None
    sprint_30m_s: Optional[float] = None
    imtp_peak_force_n: Optional[float] = None
    squat_1rm_kg: Optional[float] = None
    bench_1rm_kg: Optional[float] = None
    cycling_5s_peak_w: Optional[float] = None
    rowing_500m_w: Optional[float] = None

    # Optional Tissue Data
    us_fascicle_length_cm: Optional[float] = None  # cm (Vastus lateralis)
    us_pennation_angle_deg: Optional[float] = None  # degrees
    us_muscle_thickness_cm: Optional[float] = None  # cm
    tendon_stiffness_n_mm: Optional[float] = None  # N/mm (Achilles / Patellar)
    fascia_shear_modulus_kpa: Optional[float] = None  # kPa (plantar/crural shear wave)
    actn3_genotype: str = "Unknown"  # 'RR', 'RX', 'XX', 'Unknown'
    ace_genotype: str = "Unknown"  # 'II', 'ID', 'DD', 'Unknown'
    fiber_type_ii_pct: Optional[float] = None  # % fast twitch proxy if biopsy/TMG known

    def __post_init__(self):
        if self.lean_mass is None:
            self.lean_mass = self.body_mass * (1.0 - (self.body_fat_pct / 100.0))
        # Default allometry for segment lengths if not provided
        h = self.height
        if self.femur_length is None:
            self.femur_length = round(0.245 * h, 1)
        if self.tibia_length is None:
            self.tibia_length = round(0.215 * h, 1)
        if self.foot_length is None:
            self.foot_length = round(0.152 * h, 1)
        if self.humerus_length is None:
            self.humerus_length = round(0.186 * h, 1)
        if self.forearm_length is None:
            self.forearm_length = round(0.146 * h, 1)
        if self.hand_length is None:
            self.hand_length = round(0.108 * h, 1)
        if self.torso_length is None:
            self.torso_length = round(0.300 * h, 1)
        if self.arm_span is None:
            self.arm_span = round(h * 1.02, 1)
        if self.calcaneus_length is None:
            self.calcaneus_length = round(0.20 * self.foot_length, 2)  # ~5.1 cm average
        if self.thigh_girth is None:
            self.thigh_girth = round(56.0 * (self.body_mass / 75.0) ** 0.33, 1)
        if self.calf_girth is None:
            self.calf_girth = round(37.0 * (self.body_mass / 75.0) ** 0.33, 1)


# Preset Archetypes for Demonstrations
SAMPLE_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "Elite 100m Sprinter": {
        "name": "Elite Sprinter",
        "age": 25.0,
        "sex": "male",
        "height": 185.0,
        "body_mass": 82.0,
        "body_fat_pct": 8.0,
        "femur_length": 44.0,
        "tibia_length": 42.0,  # High crural index = 0.954
        "calcaneus_length": 4.6,  # Short calcaneus -> high gear ratio
        "foot_length": 28.0,
        "thigh_girth": 62.0,
        "calf_girth": 38.0,
        "arm_span": 192.0,
        "fpi_6": 1.0,
        "hallux_flexor_strength_n": 240.0,
        "us_fascicle_length_cm": 9.6,  # Very long fascicles
        "us_pennation_angle_deg": 14.5,  # Low pennation -> high V0
        "tendon_stiffness_n_mm": 680.0,  # Stiff tendon
        "actn3_genotype": "RR",
        "fiber_type_ii_pct": 72.0,
    },
    "Olympic Weightlifter (Powerlifter)": {
        "name": "Olympic Lifter",
        "age": 27.0,
        "sex": "male",
        "height": 172.0,
        "body_mass": 89.0,
        "body_fat_pct": 13.0,
        "femur_length": 41.0,
        "tibia_length": 34.5,  # Low crural index = 0.841, compact levers
        "calcaneus_length": 5.6,  # Longer calcaneus -> high mechanical advantage
        "foot_length": 26.5,
        "thigh_girth": 67.0,
        "calf_girth": 42.0,
        "arm_span": 170.0,
        "torso_length": 55.0,  # Strong upright trunk
        "us_fascicle_length_cm": 7.4,
        "us_pennation_angle_deg": 22.0,  # High pennation -> massive PCSA
        "tendon_stiffness_n_mm": 620.0,
        "actn3_genotype": "RX",
        "fiber_type_ii_pct": 64.0,
    },
    "Combat Sports (MMA / Sambo Grappler)": {
        "name": "Combat Athlete",
        "age": 26.0,
        "sex": "male",
        "height": 178.0,
        "body_mass": 77.0,
        "body_fat_pct": 11.0,
        "femur_length": 43.0,
        "tibia_length": 38.0,
        "arm_span": 186.0,  # Long reach (+8 cm ape index)
        "torso_length": 52.0,
        "thigh_girth": 59.0,
        "calf_girth": 38.5,
        "calcaneus_length": 5.2,
        "us_fascicle_length_cm": 8.1,
        "us_pennation_angle_deg": 17.5,
        "tendon_stiffness_n_mm": 540.0,
        "actn3_genotype": "RX",
    },
    "Track Cyclist (Velodrome Match Sprint)": {
        "name": "Track Cyclist",
        "age": 24.0,
        "sex": "male",
        "height": 182.0,
        "body_mass": 91.0,
        "body_fat_pct": 9.5,
        "femur_length": 45.0,
        "tibia_length": 39.0,
        "thigh_girth": 69.5,  # Massive thigh volume
        "calf_girth": 41.0,
        "us_fascicle_length_cm": 8.0,
        "us_pennation_angle_deg": 21.5,
        "tendon_stiffness_n_mm": 600.0,
        "cycling_5s_peak_w": 2150.0,
    },
    "Recreational Multi-Sport Athlete": {
        "name": "Recreational Athlete",
        "age": 30.0,
        "sex": "female",
        "height": 168.0,
        "body_mass": 63.0,
        "body_fat_pct": 21.0,
        "femur_length": 41.0,
        "tibia_length": 36.0,
        "thigh_girth": 54.0,
        "calf_girth": 35.0,
        "fpi_6": 2.0,
    },
}
