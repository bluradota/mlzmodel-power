# Model Specification: Biomechanical, Statistical, and Machine Learning Architecture

This document specifies the exact equations, variables, distributional priors, and hierarchical layers implemented in the sports biomechanics engine.

---

## 1. Mathematical Framework & Three-Layer Architecture

```
+---------------------------------------------------------------------------------------+
|  LAYER 1: BIOMECHANICAL DETERMINISTIC LAYER                                           |
|  - Anthropometric lever ratios (Crural index, Gear ratio, Torso-to-leg ratio)         |
|  - Allometric dimensional scaling (m^0.67 for force/power, m^-0.33 for acceleration)  |
|  - Muscle architecture proxies (PCSA, Fascicle length L_f, Pennation theta_p)         |
|  - Hill-type force-velocity dynamics & Series elastic component (SEC) strain energy    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  LAYER 2: STATISTICAL BAYESIAN REGRESSION & UNCERTAINTY LAYER                         |
|  - Principled missing data imputation with missingness variance propagation           |
|  - Informative empirical priors derived from validated literature cohorts              |
|  - Bayesian updating: Athlete prior -> Likelihood of new tests -> Updated posterior   |
|  - Prediction Intervals: Output 5th, 50th, and 95th percentiles (never point metrics)  |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  LAYER 3: INTERPRETABLE MACHINE LEARNING & SHAP ATTRIBUTION                           |
|  - Monotonic Gradient Boosting & Regularized Elastic-Net                              |
|  - TreeSHAP feature importance & local waterfall decomposition                        |
|  - Evidence calibration: Output tagged as Strong, Moderate, Weak, or Speculative      |
+---------------------------------------------------------------------------------------+
```

---

## 2. Layer 1: Biomechanical Formulation

### 2.1 Lever Mechanics & Anthropometric Indices
1. **Crural Index (CI)**:
   $$\text{CI} = \frac{L_{tibia}}{L_{femur}}$$
   - *Biomechanical role*: Distal leg segment ratio. High CI ($> 0.88$) lowers leg rotational inertia $I_{hip} \approx \int r^2 dm$, facilitating higher angular velocities during the recovery swing of sprinting.

2. **Ankle Mechanical Advantage & Gear Ratio ($GR_{ankle}$)**:
   $$GR_{ankle} = \frac{L_{forefoot}}{L_{MA\_calcaneus}}$$
   where $L_{forefoot}$ is the distance from the metatarsophalangeal (MTP) joint to the ankle joint center, and $L_{MA\_calcaneus}$ is the Achilles tendon moment arm (calcaneal tuberosity to talocrural axis).
   - *High Gear Ratio ($GR > 3.8$)*: Demands higher triceps surae muscle force, but maximizes foot linear velocity per unit muscle shortening velocity (sprint acceleration and top speed).
   - *Low Gear Ratio ($GR < 3.2$)*: High mechanical advantage; maximizes ground torque for heavy squats, isometric pushing, and grappling.

3. **Arm Span Ratio (Ape Index)**:
   $$\Delta_{span} = L_{arm\_span} - \text{Height}$$
   - *Biomechanical role*: Moment arm advantage in pulling, grappling leverage, and upper-body striking reach.

4. **Torso-to-Leg Ratio**:
   $$R_{TL} = \frac{L_{torso}}{L_{femur} + L_{tibia}}$$
   - *Biomechanical role*: Lower $R_{TL}$ implies longer legs relative to trunk; favorable for stride length in running, but increases lumbar flexion moment in deadlifts and heavy lifting.

### 2.2 Allometric Normalization
To prevent false body-mass artifacts, absolute outputs are scaled following Jaric (2002) and Markovic & Jaric (2004):
- **Allometric Force**:
  $$F_{scaled} = \frac{F_{absolute}}{m^{0.67}} \quad [\text{N} \cdot \text{kg}^{-0.67}]$$
- **Allometric Power**:
  $$P_{scaled} = \frac{P_{absolute}}{m^{0.67}} \quad [\text{W} \cdot \text{kg}^{-0.67}]$$
- **Relative Acceleration Capacity**:
  $$a_{pred} \propto \frac{F_{scaled}}{m^{0.33}} \quad [\text{m} \cdot \text{s}^{-2}]$$

### 2.3 Muscle Architecture Estimation (When Ultrasound is Absent)
When ultrasound measurements are missing, the biomechanical layer provides physiological estimates bounded by population variance:
1. **Fascicle Length ($L_f$)**:
   $$\hat{L}_{f, vastus} = 0.192 \cdot L_{femur} \cdot (1 + \delta_{training}) \pm 1.25\text{ cm}$$
2. **Pennation Angle ($\theta_p$)**:
   $$\hat{\theta}_{p, vastus} = 11.2^\circ + 0.18 \cdot \left(\frac{\text{Girth}_{thigh}}{L_{femur}} \times 100\right) \pm 2.4^\circ$$
3. **Physiological Cross-Sectional Area Proxy ($\text{PCSA}_{proxy}$)**:
   $$\text{PCSA}_{proxy} = \frac{V_{thigh\_muscle} \cdot \cos(\theta_p)}{L_f} \quad [\text{cm}^2]$$
   where $V_{thigh\_muscle}$ is derived from truncated cone anthropometry of thigh girth, femur length, and sub-cutaneous caliper thickness.

### 2.4 Hill-Type Dynamics & Force-Velocity Curves
Linearized lower-limb ballistic profile (Samozino et al., 2012):
$$F(V) = F_0 - S_{fv} \cdot V$$
$$S_{fv} = \frac{F_0}{V_0}$$
$$P(V) = F(V) \cdot V = F_0 \cdot V - S_{fv} \cdot V^2$$
$$P_{max} = \frac{F_0 \cdot V_0}{4}$$
- $F_0$: Theoretical maximum isometric force at zero velocity ($\text{N}$).
- $V_0$: Theoretical maximum unloaded extension velocity ($\text{m/s}$).
- $S_{fv}$: Force-velocity slope ($\text{N} \cdot \text{s} \cdot \text{m}^{-1}$).

### 2.5 Tendon & Fascial Elastic Strain Energy ($U_{elastic}$)
For localized tendon-aponeurosis structures (Achilles and patellar tendon):
$$U_{elastic} = \frac{1}{2} k_{tendon} \cdot (\Delta L)^2 \cdot (1 - \eta_{hysteresis})$$
where $\eta_{hysteresis} \approx 0.08$ (8% viscous dissipation as heat).
- In Countermovement Jump (CMJ), elastic energy contribution is estimated via the pre-stretch augmentation index:
  $$\Delta \text{SSC}_{pot} = \min\left(0.25, \; 0.04 \cdot \frac{k_{tendon}}{k_{reference}} + 0.08 \cdot \text{ArchStiffness}_{norm}\right)$$

---

## 3. Layer 2: Statistical Bayesian Updating & Uncertainty

### 3.1 Prior Distributions from Literature
- **Fascicle Length**: $L_f \sim \mathcal{N}(8.2\text{ cm}, 1.1^2)$
- **Pennation Angle**: $\theta_p \sim \mathcal{N}(16.5^\circ, 2.8^2)$
- **Achilles Moment Arm**: $L_{MA} \sim \mathcal{N}(5.1\text{ cm}, 0.55^2)$
- **Tendon Stiffness**: $k_{tendon} \sim \mathcal{N}(520\text{ N/mm}, 85^2)$

### 3.2 Dynamic Bayesian Updating for Repeat Tests
For an individual athlete $j$ with repeated performance measures $y_{j, 1}, \dots, y_{j, t}$:
- Prior on athlete true parameter: $\theta_j \sim \mathcal{N}(\mu_0, \sigma_0^2)$
- Likelihood of observed test $y_t | \theta_j \sim \mathcal{N}(\theta_j, \sigma_{noise}^2)$
- Analytical conjugate posterior:
  $$\mu_{post} = \frac{\frac{\mu_0}{\sigma_0^2} + \frac{\sum_{i=1}^t y_i}{\sigma_{noise}^2}}{\frac{1}{\sigma_0^2} + \frac{t}{\sigma_{noise}^2}}, \quad \sigma_{post}^2 = \left(\frac{1}{\sigma_0^2} + \frac{t}{\sigma_{noise}^2}\right)^{-1}$$

### 3.3 Prediction Intervals
All sport-specific movement outputs are reported as:
$$[P_{0.05}, \; P_{0.50}, \; P_{0.95}]$$
representing the 90% Bayesian credibility / prediction interval, preventing misleading single-point precision.

---

## 4. Layer 3: Interpretable ML & Transparency Classification

### 4.1 SHAP Attribution
Predictions are decomposed using Shapley additive explanations:
$$f(x) = \phi_0 + \sum_{i=1}^M \phi_i(x)$$
Each anthropometric input is assigned a directional contribution in engineering units (Watts, cm, m/s).

### 4.2 Evidence Level Taxonomy
Every output card in the UI displays a transparency badge:
- **[STRONG EVIDENCE]**: Direct allometric scaling, PCSA-to-force equations, fascicle length to $V_{max}$.
- **[MODERATE EVIDENCE]**: Crural index sprint contribution, Achilles moment arm gear ratio, hallux flexor force transfer.
- **[WEAK EVIDENCE]**: Single-gene ACTN3/ACE associations, indirect TMG fiber-type proxies.
- **[SPECULATIVE / HIGH UNCERTAINTY]**: Global myofascial chain energy transfer, toe-length pattern phenotypes.
