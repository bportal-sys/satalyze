# Satalyze

Welcome to Satalyze! This library provides an end-to-end automated pipeline for downloading cloud satellite imagery, processing it via computer vision, combining financial metrics insights, and generating vehicle tracking telemetry logs.

---

```mermaid
graph TD
%% Elements
User([User])
UI[Shiny App UI]
Pipe[Pipeline Controller <br>Abstract Classes / Plug-and-Play]

    subgraph Data Layer ["Relational Storage & Cache (SQLite)"]
        DB[(SQLite Database <br>Car Count and Financials)]
        ImgCache[Local Image Cache <br>Raw & Labeled]
    end

    subgraph External Ingestion ["Data Ingestion Architecture"]
        GEE[Google Earth Engine API <br> NAIP images 0.6m]
        YF[yfinance API <br>Market & Ticker Metrics]

    end

    subgraph ML ["ML Inference Layer"]
        YOLO[Custom YOLO OBB Model <br>4k+ Instances <br> mAP50: 0.751]
    end


    %% Flow / Connections
    User -->|Queries Dashboard| UI
    UI -->|Triggers Pipeline| Pipe

    %% Cache Checks
    Pipe -->|1. Check Cache| ImgCache


    %% Conditionals & Ingestion Flow
    Pipe -->|Condition 1: Full Cache Hit| UI
    Pipe -->|Condition 2: Missing Labels| YOLO
    Pipe -->|Condition 3: Complete Cache Miss| GEE
    Pipe -->|Fetch Financial Context| YF

    GEE --> YOLO
    Pipe -->|Condition 4: Force Refresh| GEE

    %% Storage Synchronization
    YOLO -->|Process & Count Cars/Trucks| DB
    YOLO -->|Save Annotated Image| ImgCache
    YF -->|Write Historical Market Data| DB

    %% UI Presentation
    DB -->|Query Joined Metrics| UI
    UI -->|Render Financial Analytics + Plotter| User

    Pipe -->|1. Check Database Cache| DB

    %% Styling & Class Assignments
    classDef user fill:#238636,stroke:#fff,stroke-width:2px,color:#fff;
    classDef ui fill:#1f6feb,stroke:#fff,stroke-width:2px,color:#fff;
    classDef core fill:#8957e5,stroke:#fff,stroke-width:2px,color:#fff;
    classDef data fill:#da70d6,stroke:#fff,stroke-width:2px,color:#fff;
    classDef ml fill:#d29922,stroke:#fff,stroke-width:2px,color:#fff;

    class User user;
    class UI ui;
    class Pipe,GEE,YF core;
    class DB,ImgCache data;
    class YOLO ml;

```

## Installation

You can install the library directly from your terminal:

```bash
pip install satalyze
```

---

## How to Use

There are **two ways** to interact with this pipeline depending on your workflow.

### 1. The Code Pipeline (For Developers)

Import the core orchestrator class directly into your scripts or Jupyter Notebooks to run automated batches:

```python
from satalyze import SatelliteTrafficPipeline

# Initialize the pipeline
traffic_pipeline = SatelliteTrafficPipeline(project_id="satalyze") # REPLACE 'satalyze' with your project ID.

# Run analysis on a target location (Example: King of Prussia Mall Parking Lot)
traffic_pipeline.run(
    center_coordinates=[-75.3947, 40.0890], # [Longitude, Latitude] # Location of your parking lot
    start_date="2018-01-01", # start date of when you want to see images (NAIP data runs every 2-3 years on average)
    end_date="2022-12-31", # End date, unless there is recent NAIP data most recent dates wil be from 2023, important to manage your time window
    limit=2 # how many images you want from this place and timeframe
)
```

### 2. The Interactive App UI (For Visual Navigation)

If you prefer a visual interface, launch the built-in Streamlit dashboard. It includes an interactive map with an integrated address search bar, date pickers, and visual counters:

```python

# Launch the visual dashboard interface
satalyze-start
```

---

## Features

- **Google Earth Engine Integration**: Automatic spatial patch downloads.
- **YOLO + SAHI Machine Learning Layers**: Sliced object detection for ultra-high-resolution targets.
- **Interactive Geocoder Map**: Search for addresses or click anywhere on the globe to grab raw coordinates.
- **Auto-Generating Analytics**: Renders live data tables and futuristic timeline graphics instantly.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.
