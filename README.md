# Water and Sanitation App

# Development Approach – How our Django Site Works (v2.0)


<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1JD3NYBU6dElmMshxYhPH2gNuNlkW8GiT"  width="800"/>
</p>

---

# Pages & Services – Table

| Where | What it is (simple) | Main job | What a normal user sees | Iteration |
|-------|----------------------|----------|--------------------------|-----------|
| `main/services/home_service.py` | Data prep for Home | Provide hero text + links | — (backend only) | Iteration 1 |
| `main/templates/water_home.html` | Home page | Entry to maps, charts, kids | Clean landing page | Iteration 1 |
| `main/templates/base.html` | Shared layout | Header/nav/footer, theme, global JS/CSS | Consistent layout | Iteration 1 |
| `main/services/future_family_safety_service.py` | Data for predictions | Use cleaned CSVs + pre-trained models to build 48h forecast, badges, chemistry level in water | — | Iteration 1 & 2 |
| `main/templates/future_family_safety.html` | Future & Family Safety | Provide views with suburb search, forecast water QA scores, badges | Prediction scores, chemistry level in water and 48h forecast Visualisation  | Iteration 1 & 2 |
| `main/services/for_kids_learn_play_service.py` | Data for kids | Animal cards, water knowledge, collection data from AWS RDS| — | Iteration 2 |
| `main/templates/for_kids_learn_play.html` | Kids – Learn & Play | Knowledge Cards + fun facts + rewards | Big icons, sea animal pixel animation, water knowledge, animal cards collection | Iteration 2 |


---

# Iteration 2 Updates

### Prediction Page Improvement (Epic 3.5)
- **Search bar + dropdown** for suburb predictions  
- **Auto-suggestions** while typing  
- Results linked to **interactive map** with suburb highlighting (After we sort out the dataset)
- Better datasets and refined forecasting methods

**Demo picture**

<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1sOD0L-yKZpVoNiLnfPuEJ6tDgOJOQYRF"  width="800"/>
</p>

<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1L6bkzJXG1YVuAiFx58tyXVk1OPFu783C"  width="800"/>
</p>


<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1FvMaQwbMFIoz7kppb1rtvOzSiZ8QsBUS"  width="800"/>
</p>

<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1BQykqUsMV9UgnpqdAJ2hIfGu2dKoz6ST"  width="800"/>
</p>



### Kids Interactive Page – Water & Animals (Epic 5.0)
- **Card click** → show water knowledge and affected animals animation (platypus, fish?)  
- **Grade-4 friendly** cards (large icons, simple text, animations)  
- **Fast load** (≤ 1.5 s)  
- **Sea Animal Card Collection** rewards


**Demo picture**

<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1qXxjJXVchuXXagiaETnuqYM5esEt0lvm"  width="500"/>
</p>


<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1wEjORePSB392jxjezeeh0iEzfoNMSBnE"  width="800"/>
</p>


<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=1YYNk9BE_uCU2Gbqk1xvRdsMlFpS2k5RG"  width="800"/>
</p>


<p align="left">
  <img src="https://drive.google.com/uc?export=view&id=11HRoeno1leTjpU6RRd8DXMjFbVGCLtRB"  width="800"/>
</p>


### Water Body Quality Prediction (Epic 6.0)
- **Search rivers and lakes**  
- Cards show **ecosystem health** and **safety guidance** (swim/camp)  
- **Supporting info & suggestions** with legends (normal/abnormal)  
- Helps families and travellers **plan safely** and avoid cancellations




---



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


Framework

```
WATER_AND_SANITATION_DJANGO/
│
├─ artifacts/                    # ML prediction data & pretrained models
│  ├─ clean/                     # Cleaned CSVs for charts & model input
│  │   ├─ field_chemistry_clean.csv
│  │   ├─ field_unparsed_datetimes.csv
│  │   ├─ lab_chemistry_clean_long.csv
│  │   ├─ lab_chemistry_clean_wide.csv
│  │   └─ output.csv
│  └─ models/                    # Model shards per parameter
│      ├─ DO_mg_L/               # Dissolved Oxygen (DO)
│      │   ├─ __GLOBAL__.joblib  # Global scaler, thresholds, meta
│      │   └─ *.joblib           # Site-specific models (e.g. 14.joblib)
│      ├─ EC_uS_cm/              # Electrical Conductivity
│      ├─ pH/                    # pH level models
│      └─ redox_mV/              # Redox potential models
│
├─ config/                       # ⚙️ Django settings, env config, thresholds.yml
│
├─ main/                         # Core Django app
│  ├─ services/                  # Backend logic for feature modules
│  │   ├─ future_family_safety_service.py
│  │   ├─ explore_water_quality_service.py
│  │   ├─ for_kids_learn_play_service.py
│  │   ├─ pollution_sources_service.py
│  │   ├─ home_service.py
│  │   └─ about_water_sanitation_service.py
│  ├─ templates/                 # HTML templates (extends base.html)
│  │   ├─ base.html
│  │   ├─ future_family_safety.html
│  │   ├─ explore_water_quality.html
│  │   ├─ for_kids_learn_play.html
│  │   ├─ pollution_sources.html
│  │   ├─ about_water_sanitation.html
│  │   └─ water_home.html
│  ├─ static/                    # 📁 Static assets (CSS / JS / Images)
│  ├─ urls.py                    # URL routing
│  ├─ views.py                   # View functions
│  ├─ models.py                  # ORM models (future DB)
│  ├─ migrations/                # DB migration files
│  └─ tests.py                   # Unit tests
│
├─ Dockerfile                    # 🐳 Docker build script
├─ requirements.txt              # 📦 Python dependencies
├─ manage.py                     # 🧩 Django CLI
├─ db.sqlite3                    # Dev DB (can be swapped out)
└─ README.md                     # Project documentation
```

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
- Reward system (knowledge/animations, sea animal card collection)

**Benefits**
- Engages children with **fun, gamified learning**  
- Encourages awareness of **sustainability and conservation**  
- Helps families use the platform together (kids learn via play)  
- Positions the platform as **fun**, not just a data portal

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

**Note:** Features not included after Iteration 1 or 2 will be shown with ~~strikethrough~~ text.

# Backlog features – Table

| Where | What it is (simple) | Main job | What a normal user sees | Iteration |
|-------|----------------------|----------|--------------------------|-----------|
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
