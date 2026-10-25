"""
Mlzmodel: Sports Biomechanics & Anthropometric Power Output Engine
Interactive Research-Grade Web Application.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any

from mlzmodel.config import InputProfile, SAMPLE_ARCHETYPES, EvidenceGrade
from mlzmodel.biomechanics import calculate_segment_ratios, estimate_muscle_architecture
from mlzmodel.profiler import AthleteProfiler
from mlzmodel.literature_db import get_literature_df
from mlzmodel.data_manager import CohortManager


# Page Setup
st.set_page_config(
    page_title="Mlzmodel | Biomechanical Power Profiler",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .metric-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        margin-right: 6px;
    }
    .badge-strong { background-color: #065f46; color: #34d399; border: 1px solid #059669; }
    .badge-moderate { background-color: #1e3a8a; color: #60a5fa; border: 1px solid #2563eb; }
    .badge-weak { background-color: #78350f; color: #fbbf24; border: 1px solid #d97706; }
    .badge-speculative { background-color: #831843; color: #f472b6; border: 1px solid #db2777; }
    
    .card-container {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .card-title {
        color: #9ca3af;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .card-value {
        color: #f9fafb;
        font-size: 1.65rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 4px;
    }
    .card-sub {
        color: #6b7280;
        font-size: 0.8rem;
    }
    .callout-box {
        background: rgba(31, 41, 55, 0.5);
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "profiler" not in st.session_state:
    st.session_state.profiler = AthleteProfiler()
if "cohort_mgr" not in st.session_state:
    st.session_state.cohort_mgr = CohortManager()


# SIDEBAR: Athlete Selection & Presets
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=600&auto=format&fit=crop&q=80", use_container_width=True)
    st.title("⚡ Athlete Profile")
    st.caption("Principal Investigator: **Paul-Mihai Cosarca**")
    
    selected_preset = st.selectbox(
        "Load Preset Archetype",
        options=["Custom Athlete"] + list(SAMPLE_ARCHETYPES.keys()),
        index=1,
    )
    
    # Load defaults from archetype if selected
    if selected_preset in SAMPLE_ARCHETYPES:
        p_data = SAMPLE_ARCHETYPES[selected_preset]
    else:
        p_data = {
            "name": "Paul-Mihai Cosarca",
            "age": 25.0,
            "sex": "male",
            "height": 180.0,
            "body_mass": 80.0,
            "body_fat_pct": 12.0,
        }
    
    st.subheader("1. Core Anthropometry")
    ath_name = st.text_input("Athlete Name / ID", value=p_data.get("name", "Paul-Mihai Cosarca"))
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        ath_sex = st.selectbox("Sex", ["male", "female"], index=0 if p_data.get("sex") == "male" else 1)
        ath_height = st.number_input("Height (cm)", min_value=130.0, max_value=230.0, value=float(p_data.get("height", 180.0)), step=0.5)
    with col_a2:
        ath_age = st.number_input("Age (yrs)", min_value=14.0, max_value=75.0, value=float(p_data.get("age", 24.0)), step=1.0)
        ath_mass = st.number_input("Body Mass (kg)", min_value=40.0, max_value=200.0, value=float(p_data.get("body_mass", 80.0)), step=0.5)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        ath_bf = st.number_input("Body Fat %", min_value=4.0, max_value=45.0, value=float(p_data.get("body_fat_pct", 12.0)), step=0.5)
    with col_b2:
        ath_bf_method = st.selectbox("BF Method", ["DEXA", "Caliper 7-site", "BIA", "Estimated"], index=0)
    
    calc_lean = ath_mass * (1.0 - ath_bf / 100.0)
    st.caption(f"Calculated Fat-Free Lean Mass: **{calc_lean:.1f} kg**")
    
    st.divider()
    st.subheader("2. Segment Levers (cm)")
    with st.expander("Expand Segment Lengths", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            femur_len = st.number_input("Femur Length", value=float(p_data.get("femur_length", round(0.245 * ath_height, 1))), step=0.5)
            tibia_len = st.number_input("Tibia Length", value=float(p_data.get("tibia_length", round(0.215 * ath_height, 1))), step=0.5)
            foot_len = st.number_input("Foot Length", value=float(p_data.get("foot_length", round(0.152 * ath_height, 1))), step=0.5)
            calcaneus_len = st.number_input("Calcaneus (Moment Arm)", value=float(p_data.get("calcaneus_length", round(0.20 * foot_len, 2))), step=0.1)
        with c2:
            torso_len = st.number_input("Torso Length", value=float(p_data.get("torso_length", round(0.300 * ath_height, 1))), step=0.5)
            arm_span = st.number_input("Arm Span", value=float(p_data.get("arm_span", round(ath_height * 1.02, 1))), step=0.5)
            humerus_len = st.number_input("Humerus Length", value=float(p_data.get("humerus_length", round(0.186 * ath_height, 1))), step=0.5)
            forearm_len = st.number_input("Forearm Length", value=float(p_data.get("forearm_length", round(0.146 * ath_height, 1))), step=0.5)

    st.subheader("3. Girths & Foot Mechanics")
    with st.expander("Expand Circumferences & Foot", expanded=False):
        cg1, cg2 = st.columns(2)
        with cg1:
            thigh_girth = st.number_input("Thigh Girth (cm)", value=float(p_data.get("thigh_girth", round(56.0 * (ath_mass / 75.0)**0.33, 1))), step=0.5)
            calf_girth = st.number_input("Calf Girth (cm)", value=float(p_data.get("calf_girth", round(37.0 * (ath_mass / 75.0)**0.33, 1))), step=0.5)
            arm_girth = st.number_input("Upper Arm Girth (cm)", value=float(p_data.get("upper_arm_girth", 34.0)), step=0.5)
        with cg2:
            fpi_val = st.slider("FPI-6 (Foot Posture)", min_value=-12.0, max_value=12.0, value=float(p_data.get("fpi_6", 0.0)), step=1.0)
            hallux_n = st.number_input("Hallux Strength (N)", value=float(p_data.get("hallux_flexor_strength_n", 185.0)), step=5.0)
            toe_pattern = st.selectbox("Toe Length Pattern", ["Egyptian (Big toe longest)", "Greek / Morton (2nd toe longest)", "Roman (Square)"], index=0)
            st.caption("⚠️ *Toe pattern is flagged [LOW EVIDENCE / FOLK MYTH]*")

    st.subheader("4. Optional Tissue & Diagnostics")
    with st.expander("Expand Ultrasound, Elastography, Genetics", expanded=False):
        ut1, ut2 = st.columns(2)
        with ut1:
            us_lf = st.number_input("Ultrasound VL Fascicle Length (cm)", value=float(p_data.get("us_fascicle_length_cm", 0.0)), step=0.1)
            us_penn = st.number_input("Ultrasound Pennation Angle (°)", value=float(p_data.get("us_pennation_angle_deg", 0.0)), step=0.5)
            tendon_k = st.number_input("Tendon Stiffness (N/mm)", value=float(p_data.get("tendon_stiffness_n_mm", 0.0)), step=10.0)
        with ut2:
            actn3_choice = st.selectbox("ACTN3 Genotype", ["Unknown", "RR", "RX", "XX"], index=["Unknown", "RR", "RX", "XX"].index(p_data.get("actn3_genotype", "Unknown")))
            fiber_pct = st.number_input("MHC Type II % (Biopsy/TMG)", value=float(p_data.get("fiber_type_ii_pct", 0.0)), step=1.0)
            fascia_kpa = st.number_input("Fascia Shear Modulus (kPa)", value=float(p_data.get("fascia_shear_modulus_kpa", 0.0)), step=5.0)


# Instantiate Profile Object
current_profile = InputProfile(
    name=ath_name,
    age=ath_age,
    sex=ath_sex,
    height=ath_height,
    body_mass=ath_mass,
    body_fat_pct=ath_bf,
    body_fat_method=ath_bf_method,
    lean_mass=calc_lean,
    femur_length=femur_len,
    tibia_length=tibia_len,
    foot_length=foot_len,
    calcaneus_length=calcaneus_len,
    torso_length=torso_len,
    arm_span=arm_span,
    humerus_length=humerus_len,
    forearm_length=forearm_len,
    thigh_girth=thigh_girth,
    calf_girth=calf_girth,
    upper_arm_girth=arm_girth,
    fpi_6=fpi_val,
    hallux_flexor_strength_n=hallux_n if hallux_n > 0 else None,
    toe_length_pattern=toe_pattern,
    us_fascicle_length_cm=us_lf if us_lf > 0 else None,
    us_pennation_angle_deg=us_penn if us_penn > 0 else None,
    tendon_stiffness_n_mm=tendon_k if tendon_k > 0 else None,
    fascia_shear_modulus_kpa=fascia_kpa if fascia_kpa > 0 else None,
    actn3_genotype=actn3_choice,
    fiber_type_ii_pct=fiber_pct if fiber_pct > 0 else None,
)

# Run Engine Profiling
results = st.session_state.profiler.profile_athlete(current_profile)
ratios = results["segment_ratios"]
arch = results["muscle_architecture"]
fv = results["force_velocity"]
elastic = results["elastic_contribution"]
preds = results["movement_predictions"]


# MAIN DASHBOARD INTERFACE
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("⚡ Dynamic Sports Biomechanics & Power Profiling System")
with col_status:
    st.markdown(
        "<div style='text-align: right; margin-top: 20px;'>"
        "<span class='metric-badge badge-strong'>⚡ LIVE RECALCULATION ACTIVE</span>"
        "<div style='color: #6b7280; font-size: 0.75rem; margin-top: 4px;'>Inputs auto-update dynamically</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    "A research-grade platform integrating **allometric scaling**, **lever mechanics**, "
    "**muscle architecture**, and **Bayesian uncertainty intervals** to model multi-sport athletic power."
)

# Top KPI Overview
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"""
    <div class="card-container">
        <div class="card-title">Allometric Power (P_allo)</div>
        <div class="card-value">{fv['pmax_allometric']} <span style="font-size: 0.9rem; font-weight: 400;">W/kg^0.67</span></div>
        <div class="card-sub">Absolute: <b>{fv['pmax_watts']:.0f} W</b> ({fv['pmax_per_kg']:.1f} W/kg)</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
    <div class="card-container">
        <div class="card-title">Crural Index (Tibia/Femur)</div>
        <div class="card-value">{ratios['crural_index']}</div>
        <div class="card-sub">{ratios['crural_index_eval']}</div>
    </div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
    <div class="card-container">
        <div class="card-title">Ankle Gear Ratio</div>
        <div class="card-value">{ratios['ankle_gear_ratio']}</div>
        <div class="card-sub">{ratios['ankle_gear_eval']}</div>
    </div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown(f"""
    <div class="card-container">
        <div class="card-title">F-V Deficit Diagnosis</div>
        <div class="card-value" style="font-size: 1.15rem; color: #60a5fa;">{fv['deficit_diagnosis'].split(' (')[0]}</div>
        <div class="card-sub">Imbalance: <b>{fv['fv_imbalance_pct']:+.1f}%</b> from optimal</div>
    </div>
    """, unsafe_allow_html=True)


# TABS FOR SPECIALIZED WORKFLOWS
tab_power, tab_arch, tab_fv, tab_shap, tab_whatif, tab_evidence, tab_longitudinal = st.tabs([
    "🏃 Movement Predictions",
    "🔬 Muscle Architecture & Levers",
    "📈 Force-Velocity & Elasticity",
    "🧠 SHAP Feature Attribution",
    "🎯 What-If Scenario Simulator",
    "📚 Scientific Evidence Matrix",
    "⏱️ Longitudinal Bayesian Tracking",
])


# ----------------------------------------------------
# TAB 1: MOVEMENT-SPECIFIC POWER PREDICTIONS
# ----------------------------------------------------
with tab_power:
    st.subheader("Multi-Sport Power Output Profiles (with 90% Prediction Intervals)")
    st.caption("Prediction intervals [5th - 95th percentiles] incorporate both biomechanical variance and measurement imputation penalties.")

    row1_c1, row1_c2, row1_c3 = st.columns(3)
    
    with row1_c1:
        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-strong">STRONG EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">Countermovement Jump (CMJ)</div>
            <div class="card-value">{preds['cmj_height_cm']['median']} cm</div>
            <div class="card-sub">90% Prediction Interval: <b>[{preds['cmj_height_cm']['ci_lower']} - {preds['cmj_height_cm']['ci_upper']}] cm</b></div>
            <div class="card-sub" style="margin-top: 4px;">CMJ Peak Power: <b>{preds['cmj_peak_power_w']['median']} W</b> [{preds['cmj_peak_power_w']['ci_lower']} - {preds['cmj_peak_power_w']['ci_upper']} W]</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-strong">STRONG EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">Maximal Sprint Velocity (Vmax)</div>
            <div class="card-value">{preds['sprint_vmax_m_s']['median']} m/s</div>
            <div class="card-sub">90% Prediction Interval: <b>[{preds['sprint_vmax_m_s']['ci_lower']} - {preds['sprint_vmax_m_s']['ci_upper']}] m/s</b></div>
            <div class="card-sub" style="margin-top: 4px;">Top Speed in km/h: <b>{preds['sprint_vmax_m_s']['median'] * 3.6:.1f} km/h</b></div>
        </div>
        """, unsafe_allow_html=True)

    with row1_c2:
        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-moderate">MODERATE EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">0-10m Sprint Acceleration</div>
            <div class="card-value">{preds['sprint_10m_s']['median']} s</div>
            <div class="card-sub">90% Prediction Interval: <b>[{preds['sprint_10m_s']['ci_lower']} - {preds['sprint_10m_s']['ci_upper']}] s</b></div>
            <div class="card-sub" style="margin-top: 4px;">Hallux Propulsion Boost: <b>{(elastic['hallux_propulsion_factor']-1.0)*100:+.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-strong">STRONG EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">Olympic Snatch Peak Power</div>
            <div class="card-value">{preds['olympic_snatch_power_w']['median']:.0f} W</div>
            <div class="card-sub">90% Prediction Interval: <b>[{preds['olympic_snatch_power_w']['ci_lower']:.0f} - {preds['olympic_snatch_power_w']['ci_upper']:.0f}] W</b></div>
            <div class="card-sub" style="margin-top: 4px;">Governed by FFM^0.67 allometric scaling & gear mechanical advantage.</div>
        </div>
        """, unsafe_allow_html=True)

    with row1_c3:
        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-moderate">MODERATE EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">Combat Striking Impact Force</div>
            <div class="card-value">{preds['striking_impact_force_n']['median']:.0f} N</div>
            <div class="card-sub">90% Prediction Interval: <b>[{preds['striking_impact_force_n']['ci_lower']:.0f} - {preds['striking_impact_force_n']['ci_upper']:.0f}] N</b></div>
            <div class="card-sub" style="margin-top: 4px;">Ape index reach bonus: <b>{ratios['ape_index_diff_cm']:+.1f} cm</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-moderate">MODERATE EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">Grappling Takedown Drive Force</div>
            <div class="card-value">{preds['grappling_thrust_force_n']['median']:.0f} N</div>
            <div class="card-sub">90% Prediction Interval: <b>[{preds['grappling_thrust_force_n']['ci_lower']:.0f} - {preds['grappling_thrust_force_n']['ci_upper']:.0f}] N</b></div>
            <div class="card-sub" style="margin-top: 4px;">High mechanical advantage lever transmission.</div>
        </div>
        """, unsafe_allow_html=True)

    # Additional Sports Summary Table
    st.subheader("Complete Movement Battery Comparison")
    table_rows = []
    for m_key, m_data in preds.items():
        tag = results["evidence_tags"].get(m_key, {"grade": "Moderate", "notes": "Standard biomechanical formulation"})
        table_rows.append({
            "Sport Movement": m_key.replace("_", " ").upper(),
            "Predicted Median": m_data["median"],
            "90% Prediction Interval": f"[{m_data['ci_lower']} - {m_data['ci_upper']}]",
            "Unit": m_data["unit"],
            "Uncertainty (±%)": f"±{m_data['uncertainty_pct']}%",
            "Evidence Grade": tag["grade"],
            "Imputation Penalty": "Applied" if m_data["imputation_penalty"] else "None (Direct)",
        })
    df_preds = pd.DataFrame(table_rows)
    st.dataframe(df_preds, use_container_width=True, hide_index=True)


# ----------------------------------------------------
# TAB 2: MUSCLE ARCHITECTURE & LEVERS
# ----------------------------------------------------
with tab_arch:
    st.subheader("Structural & Architectural Estimations")
    st.markdown("Muscle architecture governs maximum contraction velocity ($V_0$) and maximum isometric force ($F_0$).")
    
    col_arch1, col_arch2 = st.columns(2)
    
    with col_arch1:
        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Vastus Lateralis Fascicle Length (Lf)</div>
            <div class="card-value">{arch['fascicle_length_cm']} cm</div>
            <div class="card-sub">Standard Error: ±{arch['fascicle_length_sd']} cm | Source: <b>{arch['fascicle_source']}</b></div>
            <div class="callout-box">
                <b>Mechanism:</b> Fascicle length reflects sarcomeres in series. Longer fascicles shift the force-velocity curve rightward, raising unloaded shortening velocity (Kumagai et al., 2000).
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Physiological Cross-Sectional Area (PCSA) Proxy</div>
            <div class="card-value">{arch['pcsa_proxy_cm2']} cm²</div>
            <div class="card-sub">Thigh Muscle Anatomical CSA: <b>{arch['thigh_muscle_csa_cm2']} cm²</b></div>
            <div class="callout-box">
                <b>Mechanism:</b> PCSA packs contractile cross-bridges in parallel. Governs absolute peak force capacity at zero velocity (Lieber & Friden, 2000).
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_arch2:
        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Pennation Angle (θ)</div>
            <div class="card-value">{arch['pennation_angle_deg']}°</div>
            <div class="card-sub">Standard Error: ±{arch['pennation_angle_sd']}° | Source: <b>{arch['pennation_source']}</b></div>
            <div class="callout-box">
                <b>Mechanism:</b> Greater pennation angles allow more muscle fibers to pack onto an aponeurosis, sacrificing shortening velocity for higher specific force.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Fast-Twitch (Type II) Fiber Propensity</div>
            <div class="card-value">{arch['fiber_type_ii_pct']}%</div>
            <div class="card-sub">Uncertainty: ±{arch['fiber_type_ii_sd']}% | Source: <b>{arch['fiber_source']}</b></div>
            <div class="callout-box">
                <b>Caution:</b> Non-invasive fiber-type estimation carries substantial uncertainty (±12%). ACTN3 genotype provides population-level risk ratios but explains &lt;1.5% individual variance.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Segment Lever Diagram
    st.subheader("Anatomical Lever Arms & Geometric Scaling")
    lever_df = pd.DataFrame([
        {"Segment Metric": "Crural Index (Tibia / Femur)", "Value": ratios['crural_index'], "Normative Range": "0.80 - 0.94", "Evaluation": ratios['crural_index_eval']},
        {"Segment Metric": "Ankle Gear Ratio (Forefoot / Calcaneus)", "Value": ratios['ankle_gear_ratio'], "Normative Range": "3.0 - 4.5", "Evaluation": ratios['ankle_gear_eval']},
        {"Segment Metric": "Ape Index Difference (Arm Span - Height)", "Value": f"{ratios['ape_index_diff_cm']:+.1f} cm", "Normative Range": "-5 to +10 cm", "Evaluation": "Positive = Extended Reach Advantage"},
        {"Segment Metric": "Torso-to-Leg Ratio", "Value": ratios['torso_to_leg_ratio'], "Normative Range": "0.50 - 0.62", "Evaluation": "Lower = Longer Stride Mechanics"},
    ])
    st.dataframe(lever_df, use_container_width=True, hide_index=True)


# ----------------------------------------------------
# TAB 3: FORCE-VELOCITY PROFILE & ELASTIC ENERGY
# ----------------------------------------------------
with tab_fv:
    st.subheader("Lower-Limb Ballistic Force-Velocity-Power Profile")
    st.markdown("Based on the linearized ballistic push-off formulation by Samozino, Morin et al. (2012, 2014).")

    fv_c1, fv_c2 = st.columns([2, 1])

    with fv_c1:
        # Generate Interactive Plotly F-V and P-V Curves
        v_range = np.linspace(0.0, fv['v0_m_s'], 100)
        f_actual = fv['f0_n'] - (fv['f0_n'] / fv['v0_m_s']) * v_range
        p_actual = f_actual * v_range

        # Optimal F-V line
        f0_opt = fv['sfv_optimal'] * fv['v0_m_s']
        f_optimal = fv['sfv_optimal'] * (fv['v0_m_s'] - v_range)

        fig_fv = go.Figure()
        fig_fv.add_trace(go.Scatter(
            x=v_range, y=f_actual, mode='lines', name='Actual F-V Profile',
            line=dict(color='#3b82f6', width=3)
        ))
        fig_fv.add_trace(go.Scatter(
            x=v_range, y=f_optimal, mode='lines', name='Optimal F-V Profile',
            line=dict(color='#10b981', width=2, dash='dash')
        ))
        fig_fv.add_trace(go.Scatter(
            x=v_range, y=p_actual, mode='lines', name='Power Parabola P(V)',
            line=dict(color='#f59e0b', width=2.5), yaxis='y2'
        ))

        fig_fv.update_layout(
            title="Force-Velocity Line and Power Parabola",
            xaxis=dict(title="Extension Velocity V (m/s)"),
            yaxis=dict(title="Vertical Force F (N)", side='left'),
            yaxis2=dict(title="Mechanical Power P (Watts)", side='right', overlaying='y'),
            legend=dict(x=0.02, y=0.98),
            template="plotly_dark",
            margin=dict(l=40, r=40, t=40, b=40),
            height=420,
        )
        st.plotly_chart(fig_fv, use_container_width=True)

    with fv_c2:
        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Theoretical Isometric Force (F0)</div>
            <div class="card-value">{fv['f0_n']:.0f} N</div>
            <div class="card-sub">{fv['f0_n'] / ath_mass:.1f} N/kg body mass</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Theoretical Max Velocity (V0)</div>
            <div class="card-value">{fv['v0_m_s']:.2f} m/s</div>
            <div class="card-sub">Governed by sarcomeres in series (Lf)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <div class="card-title">Maximum Mechanical Power (Pmax)</div>
            <div class="card-value">{fv['pmax_watts']:.0f} W</div>
            <div class="card-sub">Allometric: <b>{fv['pmax_allometric']} W/kg^0.67</b></div>
        </div>
        """, unsafe_allow_html=True)

    # Elastic Strain Energy Breakdown
    st.subheader("Connective Tissue & Elastic Energy Storage (SSC)")
    el_col1, el_col2 = st.columns(2)
    with el_col1:
        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-moderate">MODERATE EVIDENCE</span>
            <div class="card-title" style="margin-top: 8px;">Achilles Tendon Elastic Return</div>
            <div class="card-value">{elastic['elastic_energy_return_joules']} Joules</div>
            <div class="card-sub">Stiffness: <b>{elastic['tendon_stiffness_n_mm']} N/mm</b> | Elongation: <b>{elastic['tendon_elongation_mm']} mm</b></div>
            <div class="card-sub" style="margin-top: 6px;">Stretch-Shortening Pre-Stretch Boost: <b>+{elastic['ssc_pre_stretch_augmentation_pct']}%</b></div>
        </div>
        """, unsafe_allow_html=True)
    with el_col2:
        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge badge-speculative">SPECULATIVE CLAIM</span>
            <div class="card-title" style="margin-top: 8px;">Distant Fascial Continuous Slings</div>
            <div class="card-value" style="color: #f472b6; font-size: 1.25rem;">Attenuated (&lt; 15%)</div>
            <div class="card-sub">{elastic['fascia_uncertainty_note']}</div>
        </div>
        """, unsafe_allow_html=True)


# ----------------------------------------------------
# TAB 4: SHAP LOCAL ATTRIBUTION EXPLORER
# ----------------------------------------------------
with tab_shap:
    st.subheader("Local SHAP Attribution: What Drives this Athlete's Power?")
    st.markdown("Decomposes predicted peak power into additive contributions (Watts) above or below the cohort baseline.")

    shap_data = results["shap_attribution"]
    base_val = shap_data["base_value_w"]
    breakdown = shap_data["breakdown"]

    st.info(f"Cohort Baseline Power: **{base_val:.1f} W** | Athlete Predicted Power: **{shap_data['predicted_power_w']:.1f} W**")

    # Plotly Horizontal Bar for SHAP Impacts
    df_shap = pd.DataFrame(breakdown)
    df_shap["Color"] = df_shap["shap_impact_watts"].apply(lambda x: "#10b981" if x >= 0 else "#ef4444")

    fig_shap = px.bar(
        df_shap,
        x="shap_impact_watts",
        y="feature",
        orientation="h",
        color="Color",
        color_discrete_map="identity",
        title="Shapley Feature Contributions to CMJ Peak Power (Watts)",
        labels={"shap_impact_watts": "Power Impact (Watts)", "feature": "Biological Feature"},
    )
    fig_shap.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_shap, use_container_width=True)

    # Detailed Table
    st.dataframe(df_shap[["feature", "input_value", "shap_impact_watts", "direction"]], use_container_width=True, hide_index=True)


# ----------------------------------------------------
# TAB 5: WHAT-IF SCENARIO SIMULATOR
# ----------------------------------------------------
with tab_whatif:
    st.subheader("🎯 What-If Scenario Simulator: Interactive Recalculation")
    st.markdown(
        "Adjust physiological, lever, or tissue variables below to simulate training adaptations "
        "(e.g., hypertrophy, eccentric fascicle elongation, isometric tendon stiffening) "
        "and immediately observe recalculated power profiles and force-velocity shifts in real time."
    )
    
    sim_c1, sim_c2, sim_c3 = st.columns(3)
    with sim_c1:
        delta_lean = st.slider("Δ Lean Muscle Mass (kg)", min_value=-6.0, max_value=8.0, value=0.0, step=0.5, help="Simulate hypertrophy or cutting")
        delta_lf = st.slider("Δ Fascicle Length Lf (cm)", min_value=-1.5, max_value=2.0, value=0.0, step=0.1, help="Simulate eccentric overload adaptations (Kumagai 2000)")
    with sim_c2:
        delta_tendon = st.slider("Δ Tendon Stiffness (N/mm)", min_value=-150.0, max_value=250.0, value=0.0, step=10.0, help="Simulate heavy isometric / plyometric tendon adaptation")
        sim_fpi = st.slider("Simulated Foot Posture (FPI-6)", min_value=-12.0, max_value=12.0, value=float(current_profile.fpi_6 or 0.0), step=1.0)
    with sim_c3:
        delta_hallux = st.slider("Δ Hallux Flexor Strength (N)", min_value=-60.0, max_value=120.0, value=0.0, step=10.0, help="Simulate toe flexor strengthening (Goldmann 2013)")
        st.caption("⚡ **Recalculation:** All predictions update dynamically as you drag any slider.")

    # Build simulated profile
    sim_mass = current_profile.body_mass + delta_lean
    sim_lean = (current_profile.lean_mass or (current_profile.body_mass * (1.0 - current_profile.body_fat_pct/100.0))) + delta_lean
    sim_bf = max(4.0, ((sim_mass - sim_lean) / sim_mass) * 100.0)
    sim_lf_base = arch["fascicle_length_cm"] + delta_lf
    sim_k_base = elastic["tendon_stiffness_n_mm"] + delta_tendon
    sim_hallux_base = (current_profile.hallux_flexor_strength_n or 180.0) + delta_hallux

    sim_profile = InputProfile(
        name=f"{current_profile.name} (Simulated)",
        age=current_profile.age,
        sex=current_profile.sex,
        height=current_profile.height,
        body_mass=sim_mass,
        body_fat_pct=sim_bf,
        body_fat_method=current_profile.body_fat_method,
        lean_mass=sim_lean,
        femur_length=current_profile.femur_length,
        tibia_length=current_profile.tibia_length,
        foot_length=current_profile.foot_length,
        calcaneus_length=current_profile.calcaneus_length,
        torso_length=current_profile.torso_length,
        arm_span=current_profile.arm_span,
        humerus_length=current_profile.humerus_length,
        forearm_length=current_profile.forearm_length,
        thigh_girth=(current_profile.thigh_girth or 56.0) + delta_lean * 0.45,
        calf_girth=current_profile.calf_girth,
        upper_arm_girth=current_profile.upper_arm_girth,
        fpi_6=sim_fpi,
        hallux_flexor_strength_n=sim_hallux_base,
        toe_length_pattern=current_profile.toe_length_pattern,
        us_fascicle_length_cm=sim_lf_base,
        us_pennation_angle_deg=arch["pennation_angle_deg"],
        tendon_stiffness_n_mm=sim_k_base,
        actn3_genotype=current_profile.actn3_genotype,
        fiber_type_ii_pct=arch["fiber_type_ii_pct"],
    )

    sim_res = st.session_state.profiler.profile_athlete(sim_profile)
    sim_preds = sim_res["movement_predictions"]
    sim_fv = sim_res["force_velocity"]

    # Comparative KPI Cards
    st.markdown("#### Baseline vs. Simulated Recalculation Results")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        d_cmj = sim_preds["cmj_height_cm"]["median"] - preds["cmj_height_cm"]["median"]
        st.metric("CMJ Height", f"{sim_preds['cmj_height_cm']['median']:.1f} cm", delta=f"{d_cmj:+.1f} cm")
    with sc2:
        d_pmax = sim_fv["pmax_watts"] - fv["pmax_watts"]
        st.metric("Peak Power Pmax", f"{sim_fv['pmax_watts']:.0f} W", delta=f"{d_pmax:+.0f} W")
    with sc3:
        d_vmax = (sim_preds["sprint_vmax_m_s"]["median"] - preds["sprint_vmax_m_s"]["median"]) * 3.6
        st.metric("Sprint Top Speed", f"{sim_preds['sprint_vmax_m_s']['median']*3.6:.1f} km/h", delta=f"{d_vmax:+.2f} km/h")
    with sc4:
        d_sprint10 = sim_preds["sprint_10m_s"]["median"] - preds["sprint_10m_s"]["median"]
        st.metric("0-10m Split Time", f"{sim_preds['sprint_10m_s']['median']:.3f} s", delta=f"{d_sprint10:+.3f} s", delta_color="inverse")

    # Comparative Plotly F-V Curve Overlay
    v_sim = np.linspace(0.0, max(fv["v0_m_s"], sim_fv["v0_m_s"]), 100)
    f_base_curve = np.clip(fv["f0_n"] - (fv["f0_n"] / fv["v0_m_s"]) * v_sim, 0, None)
    f_sim_curve = np.clip(sim_fv["f0_n"] - (sim_fv["f0_n"] / sim_fv["v0_m_s"]) * v_sim, 0, None)

    fig_sim = go.Figure()
    fig_sim.add_trace(go.Scatter(x=v_sim, y=f_base_curve, mode="lines", name="Baseline F-V Profile", line=dict(color="#3b82f6", width=2.5, dash="dash")))
    fig_sim.add_trace(go.Scatter(x=v_sim, y=f_sim_curve, mode="lines", name="Simulated F-V Profile", line=dict(color="#10b981", width=3.5)))
    fig_sim.update_layout(
        title="Force-Velocity Shift: Baseline (Dashed Blue) vs Simulated (Solid Green)",
        xaxis_title="Extension Velocity V (m/s)",
        yaxis_title="Vertical Ground Force F (N)",
        template="plotly_dark",
        height=380,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig_sim, use_container_width=True)


# ----------------------------------------------------
# TAB 6: SCIENTIFIC EVIDENCE MATRIX
# ----------------------------------------------------
with tab_evidence:
    st.subheader("Peer-Reviewed Literature Matrix & Verification Directory")
    st.markdown("Every relationship modeled in this system is linked to verified peer-reviewed publications with DOIs.")

    lit_df = get_literature_df()
    
    # Filter by category
    selected_cat = st.selectbox("Filter by Domain", ["All Domains"] + list(lit_df["category"].unique()))
    if selected_cat != "All Domains":
        display_df = lit_df[lit_df["category"] == selected_cat]
    else:
        display_df = lit_df

    for _, row in display_df.iterrows():
        grade_cls = "badge-strong" if "Strong" in row["grade"] else ("badge-moderate" if "Moderate" in row["grade"] else ("badge-weak" if "Weak" in row["grade"] else "badge-speculative"))
        st.markdown(f"""
        <div class="card-container">
            <span class="metric-badge {grade_cls}">{row['grade']}</span>
            <span style="color: #9ca3af; font-size: 0.85rem; font-weight: 500;">{row['category']}</span>
            <div style="font-size: 1.15rem; font-weight: 700; color: #f9fafb; margin-top: 6px;">{row['factor']} → {row['target']}</div>
            <div style="color: #60a5fa; font-size: 0.85rem; margin-top: 2px;">
                <b>{row['author_year']}</b>, <i>{row['journal']}</i> | DOI: <a href="https://doi.org/{row['doi']}" target="_blank" style="color: #93c5fd;">{row['doi']}</a>
            </div>
            <div style="color: #d1d5db; font-size: 0.9rem; margin-top: 8px;">
                <b>Effect Size:</b> {row['effect_size']} (Sample Size: {row['sample_size']})
            </div>
            <div class="callout-box" style="margin-top: 8px; font-size: 0.88rem;">
                <b>Empirical Finding:</b> {row['finding']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ----------------------------------------------------
# TAB 6: LONGITUDINAL BAYESIAN TRACKING
# ----------------------------------------------------
with tab_longitudinal:
    st.subheader("Longitudinal Athlete Tracking & Bayesian Posterior Updating")
    st.markdown("As repeated physical test sessions are logged, Bayesian updating incorporates likelihood evidence, narrowing prediction uncertainty bands.")

    history_records = st.session_state.cohort_mgr.load_history(ath_name, "cmj_height_cm")
    
    col_hist_left, col_hist_right = st.columns([2, 1])

    with col_hist_right:
        st.markdown("#### Log New Performance Test")
        with st.form("add_test_form"):
            new_date = st.date_input("Test Date")
            new_metric = st.selectbox("Metric", ["cmj_height_cm", "sprint_10m_s", "sprint_vmax_m_s"])
            new_val = st.number_input("Recorded Performance Value", min_value=0.0, max_value=200.0, value=60.0, step=0.5)
            new_unit = "cm" if "cm" in new_metric else ("s" if "_s" in new_metric else "m/s")
            submit_btn = st.form_submit_button("Add Session to Record")
            if submit_btn:
                st.session_state.cohort_mgr.add_test_session(
                    ath_name, new_metric, new_val, new_unit, new_date.strftime("%Y-%m-%d")
                )
                st.success(f"Added test on {new_date}: {new_val} {new_unit}")
                st.rerun()

    with col_hist_left:
        if len(history_records) > 0:
            bayes_engine = st.session_state.profiler.bayes_engine
            prior_baseline = preds["cmj_height_cm"]["median"]
            updated_series = bayes_engine.update_longitudinal_series(prior_baseline, "cmj_height_cm", history_records)
            
            df_hist = pd.DataFrame(updated_series)
            
            # Trajectory Plot
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=df_hist["date"], y=df_hist["recorded_value"],
                mode='markers+lines', name='Empirical Observed Test',
                marker=dict(size=10, color='#3b82f6')
            ))
            fig_hist.add_trace(go.Scatter(
                x=df_hist["date"], y=df_hist["posterior_median"],
                mode='lines', name='Updated Bayesian Posterior',
                line=dict(color='#10b981', width=3)
            ))
            # Uncertainty Ribbon
            fig_hist.add_trace(go.Scatter(
                x=list(df_hist["date"]) + list(df_hist["date"])[::-1],
                y=list(df_hist["ci_upper"]) + list(df_hist["ci_lower"])[::-1],
                fill='toself',
                fillcolor='rgba(16, 185, 129, 0.15)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='90% Credibility Ribbon'
            ))
            fig_hist.update_layout(
                title=f"Longitudinal CMJ Trajectory & Shrinkage of Uncertainty for {ath_name}",
                xaxis_title="Testing Session Date",
                yaxis_title="CMJ Height (cm)",
                template="plotly_dark",
                height=380,
                margin=dict(l=40, r=40, t=40, b=40),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info(f"No longitudinal test sessions recorded yet for {ath_name}. Add a session in the right panel to initiate Bayesian trajectory tracking.")

    st.divider()
    st.subheader("Generate & Inspect Benchmark Synthetic Cohort")
    st.caption("Inspect multivariate cohort covariance for model validation. Explicitly tagged [SYNTHETIC_BENCHMARK].")
    if st.button("Generate Benchmark Cohort (N=30)"):
        syn_df = st.session_state.cohort_mgr.generate_benchmark_synthetic_cohort(30)
        st.dataframe(syn_df, use_container_width=True)
        csv_data = syn_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Benchmark Cohort CSV", data=csv_data, file_name="benchmark_synthetic_cohort.csv", mime="text/csv")


# Footer
st.divider()
st.caption(
    "🔬 **Mlzmodel Engine** | Developed by **Paul-Mihai Cosarca** | Sports Biomechanics & Athletic Performance Research\n\n"
    "⚠️ **Ethical & Scientific Disclaimer:** This system is an exploratory biomechanical modeling tool for research and training insights. "
    "Anthropometry alone explains ~15-35% of power output variance; non-structural factors (neural drive, skill, recruitment) dominate. "
    "Do NOT use structural or genetic markers for medical diagnosis or exclusionary talent deselection."
)
