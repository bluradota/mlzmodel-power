# Dataset Inventory & Empirical Data Collection Protocols

This document indexes accessible open-access repositories for human anthropometry and athletic performance, details their parameters and limitations, and outlines an empirical data-collection protocol to bridge the primary data gap: linking fascia distribution and stiffness directly to multi-sport power production.

---

## 1. Open & Accessible Datasets Inventory

| Dataset Name | Primary Domain | Sample Size ($N$) | Key Anthropometric & Performance Variables | Licence | Access URL / Identifier | Inherent Limitations & Biases |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ANSUR II (2012 Anthropometric Survey of U.S. Army Personnel)** | Detailed 3D & Manual Anthropometry | $N = 6,068$ (4,082 males, 1,986 females) | 93 direct physical measures: stature, trochanteric height, tibial height, foot length, foot breadth, limb circumferences, biacromial breadth, chest/waist/hip girths, body mass. | Public Domain (U.S. DoD / NSRDEC) | [OpenLab Penn State ANSUR II Portal](https://www.openlab.psu.edu/ansur2/) | Military personnel; while fit, subjects are not sport-specialized ballistic power athletes. Lacks dynamic power outputs (CMJ, sprint splits, force plates). |
| **CDC NHANES (National Health and Nutrition Examination Survey)** | Epidemiology & Whole-Body Composition | $N > 10,000$ per 2-year cycle | Whole-body DXA scans (lean mass, fat mass, bone mineral content by segment), anthropometry, isokinetic knee extensor strength (selected cohorts). | Public Domain (U.S. CDC / NCHS) | [CDC NHANES Data Portal](https://wwwn.cdc.gov/nchs/nhanes/) | Cross-sectional representative general population (high heterogeneity, sedentary to recreationally active). No sport-specific jump or sprint power metrics. |
| **Samozino & Morin Ballistic Profiling Database (OSF / Zenodo)** | Force-Velocity-Power Profiling in Athletes | $N \approx 320$ competitive athletes | Body mass, push-off distance ($h_{po}$), CMJ height, Squat Jump height, loaded jump force-velocity parameters ($F_0, V_0, P_{max}$, optimal $S_{fv}$), 30m sprint radar/timing splits. | Creative Commons Attribution 4.0 (CC-BY 4.0) | [OSF / Zenodo Repositories](https://doi.org/10.5281/zenodo.4764831) | Contains performance and macroscopic limb lengths ($L_0$), but lacks B-mode ultrasound muscle architecture or shear-wave elastography. |
| **OpenSim / SimTK Biomechanics Repositories** | Musculoskeletal Models & Motion Capture | $N = 40\text{--}150$ per project | 3D kinematics (optical marker trajectories), ground reaction forces (dual AMTI/Kistler plates), electromyography (surface EMG), computed inverse dynamics joint moments and powers. | Apache 2.0 / GNU LGPL | [SimTK Biomotion Project Portal](https://simtk.org/) | Computationally rich, but small sample sizes ($N < 50$ per study), predominantly running/gait rather than multi-sport maximum power efforts. |
| **Sports Biomechanics Dataverse (PhysioNet / Zenodo Athlete Cohorts)** | Elite Athlete Countermovement Jump Force-Time Series | $N = 185$ elite collegiate athletes | Dual force deck vertical ground reaction force (vGRF) sampled at 1000 Hz: eccentric duration, concentric impulse, reactive strength index modified (mRSI), peak power, body mass. | ODC-BY / CC-BY 4.0 | [PhysioNet / Dryad Digital Repository](https://physionet.org/) | High-fidelity kinetic time-series, but detailed segment lengths and ultrasound muscle architecture are uncoupled. |

---

## 2. Critical Data Gap: Fascia Distribution & Elastic Power

### 2.1 The Missing Empirical Link
While the biomechanical capacity of localized tendons (e.g., Achilles tendon, patellar tendon) to store and return strain energy is established in the literature ($k_{tendon} \approx 20\text{--}40$ J elastic return during fast SSC), **there is currently no published, open-access dataset linking multi-site fascia thickness/shear modulus to multi-sport power metrics across an athlete cohort**. 

Popular claims attributing athletic elasticity to global "fascial continuous slings" rely almost entirely on passive anatomical dissections (e.g., Myers, 2001; Stecco et al., 2013) without concurrent dynamic force-time or ultrasound quantification during explosive tasks.

### 2.2 Proposed Empirical Data-Collection Protocol

To validate or refute the fascial contribution hypothesis rigorously, the following pre-registered data-collection protocol is proposed:

#### A. Target Cohort & Design
- **Sample Size**: $N = 60$ sprint/jump trained competitive athletes (30 male, 30 female; age 18–30; minimum 2 years systematic power training).
- **Study Design**: Prospective cross-sectional and 12-week longitudinal training intervention with pre/post high-resolution tissue scanning.

#### B. Tissue Diagnostic Equipment & Standardized Sites
1. **Apparatus**: Supersonic Shear Imaging (SSI) shear-wave elastography (e.g., Aixplorer Ultimate or Canon Aplio i800) with a 50–70 mm linear transducer (4–15 MHz).
2. **Standardized Measurement Sites**:
   - **Plantar Fascia**: 2 cm anterior to the calcaneal tuberosity insertion in resting prone and $30^\circ$ hallux dorsiflexion.
   - **Achilles Tendon & Aponeurosis**: Free tendon (4 cm proximal to calcaneus) and medial gastrocnemius distal aponeurosis.
   - **Iliotibial Band (ITB) & Fascia Lata**: 10 cm proximal to lateral femoral epicondyle and at mid-thigh.
   - **Thoracolumbar Fascia (TLF)**: Posterior layer at L3/L4 level, 3 cm lateral to spinous process.
3. **Scan Reliability & Quality Control**:
   - Strict probe alignment with collagen fiber orientation (verified by B-mode echogenicity).
   - Zero probe compression (thick acoustic coupling gel standoff pad).
   - 3 consecutive acquisitions averaged per site; test-retest reliability threshold: Intraclass Correlation Coefficient $\text{ICC}_{(3,1)} \ge 0.88$, Coefficient of Variation $\text{CV} \le 5.5\%$.
   - Quantified metrics: Fascia thickness (mm), Young's shear modulus ($\mu = \rho c_s^2$ in kPa), and resting echogenicity index.

#### C. Kinematic & Kinetic Testing Battery
1. **Force Deck Dynamics**: Dual force plates ($1000\text{ Hz}$) recording:
   - Squat Jump (SJ, pure concentric) vs Countermovement Jump (CMJ, slow SSC) vs Drop Jump from 20/40 cm (DJ, fast SSC $< 250\text{ ms}$).
   - **Elastic Energy Contribution Proxy**: Stretch-Shortening Pre-stretch Augmentation Ratio:
     $$\Delta \text{SSC}_{\%} = \frac{\text{CMJ Height} - \text{SJ Height}}{\text{SJ Height}} \times 100$$
     and Reactive Strength Index ($\text{RSI} = \text{DJ Height} / \text{Contact Time}$).
2. **Synchronized Motion Analysis & Ultrasound**:
   - High-speed B-mode dynamic ultrasound (120 Hz) affixed to the gastrocnemius-Achilles junction during take-off to distinguish fascicle shortening velocity vs tendon recoil velocity.

---

## 3. Synthetic Prototyping Standards in this Engine
For prototype development and validation prior to uploading private cohort data:
- **Mandatory Synthetic Labeling**: All simulated cohort records are generated with exact multivariate covariance distributions observed in empirical literature (Kumagai et al., 2000; Baxter et al., 2012; Samozino et al., 2014) and are explicitly flagged: `DATA_ORIGIN: SYNTHETIC_BENCHMARK`.
- **Zero Fabrication Policy**: Synthetic data is used exclusively to verify algorithmic stability, Bayesian updating convergence, and interface functionality. It is never presented to the user as empirical evidence.
