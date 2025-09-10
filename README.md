# Water and Sanitation App

# Development Approach – How our Django Site Works (Team Guide v2.0)

**Note:** Features not included after Iteration 1 or 2 will be shown with ~~strikethrough~~ text.


# Exact Mappings (HTML ↔ Service ↔ View ↔ URL)

- **Home**
  - Template: `water_home.html`
  - Service: `home_service.py`
  - URL: `/`

- **Future & Family Safety**
  - Template: `future_family_safety.html`
  - Service: `future_family_safety_service.py`
  - URL: `/future_family_safety/`

- **For Kids – Learn & Play**
  - Template: `for_kids_learn_play.html`
  - Service: `for_kids_learn_play_service.py`
  - URL: `/for_kids_learn_play/`

- **Explore Water Quality** (future)
  - Template: `explore_water_quality.html`
  - Service: `explore_water_quality_service.py`
  - URL: `/explore_water_quality/`

- **Pollution Sources** (future)
  - Template: `pollution_sources.html`
  - Service: `pollution_sources_service.py`
  - URL: `/pollution_sources/`

- **About Our Water** (future)
  - Template: `about_water_sanitation.html`
  - Service: `about_water_sanitation_service.py`
  - URL: `/about_water_sanitation/`


---

# Proposed Solution

We designed a page specifically for children.  
The objective is to share information and knowledge about water quality and how it affects the environment.

**Solution features**
- Website designed with high accessibility for children  
- Reward system to maintain motivation

---

# Plan for Iteration 3.5 (Epic)

## Epic 3.5 – Prediction Page Improvement

**Must Have**
- Search bar **dropdowns** sorted by suburbs  
- **Auto-suggestions** as the user types  
- Integration of **map-based results** with suburb highlights  
- Minimise heavy analytics on the page (per feedback)

**Benefits**
- Improves usability for families and residents  
- Provides **clear, suburb-specific insights** (not just raw data)  
- Enables proactive planning for outdoor activities  
- Builds trust via more accurate, validated predictions

---

# Plan for Iteration 5 (Epic)

## Epic 5.0 – Kids Interactive Page: Water & Animals

**Must Have**
- Simple, **Grade-4 friendly** cards about water and animals  
- Large icons and animations for accessibility  
- **Fast-loading content (≤ 1.5 s)**  
- Reward system (badges/animations, sea animal card collection)

**Benefits**
- Engages children with **fun, gamified learning**  
- Encourages awareness of **sustainability and conservation**  
- Helps families use the platform together (parents see predictions; kids learn via play)  
- Positions the platform as **fun + predictive**, not just a data portal

---

# Plan for Iteration 6 (Epic)

## Epic 6.0 – Water Body Quality Prediction

**Must Have**
- **Search rivers and lakes** by name  
- Prediction of **ecosystem health** (Safe, Caution, Avoid)  
- **Information & Suggestions** with legends showing normal vs abnormal parameter ranges

**Benefits**
- Great for **camping and swimming** planning  
- Check projections in advance for better planning and awareness  
- Avoid cancellations and reduce risk of health incidents

---

# Iteration 2 Updates

### Prediction Page Improvement (Epic 3.5)
- **Search bar + dropdown** for suburb predictions  
- **Auto-suggestions** while typing  
- Results linked to **interactive map** with suburb highlighting  
- Better datasets and refined forecasting methods

### Kids Interactive Page – Water & Animals (Epic 5.0)
- **Region click** → show water quality (green/yellow/red) and affected animals (platypus, fish, frogs)  
- **Grade-4 friendly** cards (large icons, simple text, animations)  
- **Fast load** (≤ 1.5 s)  
- **Sea Animal Card Collection** rewards

### Water Body Quality Prediction (Epic 6.0)
- **Search rivers and lakes**  
- Cards show **ecosystem health** and **safety guidance** (swim/camp)  
- **Supporting info & suggestions** with legends (normal/abnormal)  
- Helps families and travellers **plan safely** and avoid cancellations

---

# Pages & Services – Simple Table

| Where | What it is (simple) | Main job | What a normal user sees | Iteration |
|-------|----------------------|----------|--------------------------|-----------|
| `main/services/home_service.py` | Data prep for Home | Provide hero text + links | — (backend only) | Iteration 1 |
| `main/templates/water_home.html` | Home page | Entry to maps, charts, kids | Clean landing page | Iteration 1 |
| `main/templates/base.html` | Shared layout | Header/nav/footer, theme, global JS/CSS | Consistent layout | Iteration 1 |
| `main/services/future_family_safety_service.py` | Data for predictions | Use cleaned CSVs + pre-trained models to build 48h forecast, badges, advice | — | Iteration 1 & 2 |
| `main/templates/future_family_safety.html` | Future & Family Safety | Suburb search, forecast card, badges | Prediction card with advice | Iteration 1 & 2 |
| `main/services/for_kids_learn_play_service.py` | Data for kids | Animal cards, water knowledge, collection data | — | Iteration 2 |
| `main/templates/for_kids_learn_play.html` | Kids – Learn & Play | Map + fun facts + rewards | Big icons, animal collection tank | Iteration 2 |
| ~~`main/services/explore_water_quality_service.py`~~ | ~~Data for bubble map~~ | ~~Suburb list, scores, filters~~ | — | Future |
| ~~`main/templates/explore_water_quality.html`~~ | ~~Interactive bubble map~~ | ~~Colored bubbles, click card~~ | ~~Score, trend, safety~~ | Future |
| ~~`main/services/pollution_sources_service.py`~~ | ~~Data for charts~~ | ~~Pie + bar data~~ | — | Future |
| ~~`main/templates/pollution_sources.html`~~ | ~~Pollution Sources~~ | ~~Charts + table~~ | ~~Charts of pollutants~~ | Future |
| ~~`main/services/about_water_sanitation_service.py`~~ | ~~About data~~ | ~~Dataset sources & info~~ | — | Future |
| ~~`main/templates/about_water_sanitation.html`~~ | ~~About Our Water~~ | ~~Info page~~ | ~~Simple info~~ | Future |

---

# Installation & Run Guide

**Repository**  

https://github.com/Kevin951113/water_and_sanitation_django.git

**Installation Documentation**

https://docs.google.com/document/d/1NBP7aYoXnNOZJLZ_d0BYVA41YP_qQBOV



> This notebook contains an overview and setup guide. Run the cells if you'd like to execute commands locally (adjust paths as needed).
