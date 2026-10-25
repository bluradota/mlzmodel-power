# Mlzmodel: Biomechanical & Anthropometric Power Output Profiling System

A research-grade sports biomechanics and data-science engine relating individual anthropometry, segment lever mechanics, and muscle architecture to athletic power output across multi-sport movements.

---

## Key Features

1. **Layer 1: Biomechanical Physics Layer**
   - **Allometric Scaling**: Geometric similarity scaling ($m^{0.67}$ for force and power; $m^{-0.33}$ for relative acceleration; Jaric, 2002). Eliminates misleading body-mass ratio standards.
   - **Segment Lever Mechanics**: Crural index (tibia/femur ratio), ankle gear ratio (forefoot lever / calcaneus moment arm), ape index reach advantage, and torso-to-leg proportions.
   - **Muscle Architecture Estimator**: Vastus lateralis fascicle length ($L_f$), pennation angle ($\theta_p$), and physiological cross-sectional area (PCSA proxy; Lieber & Friden, 2000). Direct ultrasound measurements override estimations.
   - **Hill-Type Ballistic Dynamics**: Theoretical maximum isometric force ($F_0$), unloaded shortening velocity ($V_0$), optimal force-velocity slope ($S_{fv\_opt}$), and force/velocity deficit diagnosis (Samozino et al., 2012, 2014).
   - **Elasticity & Stretch-Shortening Cycle (SSC)**: Achilles tendon strain energy storage ($U_{strain}$), foot arch windlass mechanics (FPI-6), hallux flexor propulsion, and critical appraisal of distant "fascial chains" (Wilke et al., 2016).

2. **Layer 2: Statistical Bayesian Layer**
   - **Uncertainty Quantification**: Outputs 90% Bayesian credibility/prediction intervals $[P_{0.05}, P_{0.50}, P_{0.95}]$ in real engineering units (Watts, cm, m/s).
   - **Principled Missing Data Handling**: Imputation uncertainty inflation ensures predictions made with incomplete inputs carry wider, honest error bounds.
   - **Longitudinal Bayesian Updating**: Conjugate updating narrows athlete prediction intervals as repeated test sessions accumulate over training cycles.

3. **Layer 3: Interpretable Machine Learning & Local SHAP Attribution**
   - **Local Feature Attribution**: TreeSHAP decomposition reveals exactly how many Watts each anatomical parameter adds or subtracts from the cohort baseline.
   - **Transparent Evidence Grading**: Classifies every modeled relationship into **[STRONG]**, **[MODERATE]**, **[WEAK]**, or **[SPECULATIVE]** with verified DOIs.

---

## Directory Structure

```
Mlzmodel/
├── docs/
│   ├── literature_review.md       # Comprehensive evidence matrix, verified citations, DOIs, and debunked myths
│   ├── dataset_inventory.md       # Open datasets (ANSUR II, NHANES, OSF) and empirical data-collection protocol
│   ├── model_specification.md     # Equations, 3-layer architecture, allometry, and Bayesian updating formulas
│   ├── validation_report.md       # Person-grouped cross-validation, MAE/RMSE in real units, and ethical safeguards
│   └── fascia_testing_roadmap.md  # 4-phase experimental roadmap to empirically test the fascia hypothesis
├── mlzmodel/
│   ├── __init__.py
│   ├── config.py                  # Schemas, dataclasses, evidence taxonomies, and athletic presets
│   ├── literature_db.py           # Structured literature database with verified DOIs and effect sizes
│   ├── biomechanics.py            # Physics, lever mechanics, muscle architecture, Hill dynamics, and SEC elasticity
│   ├── statistical_layer.py       # Bayesian prediction intervals, uncertainty engine, and longitudinal updating
│   ├── ml_layer.py                # Gradient Boosting model with TreeSHAP local feature attribution
│   ├── profiler.py                # End-to-end multi-sport movement profiler
│   └── data_manager.py            # Longitudinal test logging and synthetic benchmark cohort generator
├── tests/
│   └── test_biomechanics.py       # Unit and integration test suite (100% passing)
├── app.py                         # Full interactive Streamlit web dashboard
└── requirements.txt               # Frozen dependencies
```

---

## Quickstart

### 1. Run Unit Tests
```bash
.venv\Scripts\python -m unittest tests/test_biomechanics.py
```

### 2. Launch Streamlit Web Dashboard
```bash
.venv\Scripts\streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## Scientific & Ethical Safeguards

1. **Variance Bounds**: Anthropometry and structural anatomy explain **$15\%\text{--}35\%$ of the inter-individual variance** in explosive power. Non-structural factors (neural drive, rate coding, motor unit recruitment, and technique) govern the remaining $65\%\text{--}85\%$.
2. **Not for Exclusionary Talent Deselection**: Biometric and genetic markers must never be used to eliminate or deselected athletes from sports programs.
3. **Research & Training Insight Only**: This system does not constitute medical diagnosis or orthopedic advice.
