# Observatorio de Velocidades — RM y V Región

An interactive Streamlit dashboard for visualizing aggregated traffic speeds across road segments ("arcos") in communes of Santiago (Región Metropolitana) and the V Región. Select a commune, date, and time band to explore color-coded speed maps backed by a PostgreSQL/PostGIS spatial database.

[Streamlit App](https://89luw7kknqmcxumoregbbh.streamlit.app/)

---

## Features

- **Interactive map** — Road segments rendered as color-coded lines on a Folium map, centered automatically on the selected commune
- **Speed visualization** — Five-level color scale from congested (red) to free-flow (green), based on normalized speed relative to maximum
- **Segment tooltips** — Hover over any road segment to see its name, average speed, and length
- **Time band filter** — Morning (7:00–10:00) and afternoon (17:00–20:00) peak hour analysis
- **Summary metrics** — Length-weighted average speed, arc count, and total network length displayed as KPI cards
- **Efficient caching** — SQLAlchemy engine cached for the app lifetime; catalog and spatial queries cached with TTL to minimize DB load

---

## Tech Stack

| Package | Role |
|---|---|
| `streamlit` | Web UI, layout, caching, and widget controls |
| `geopandas` | Spatial queries via `read_postgis`, GeoDataFrame handling |
| `sqlalchemy` | Database engine and parameterized SQL execution |
| `psycopg2-binary` | PostgreSQL driver |
| `folium` | Interactive map creation and GeoJSON layer styling |
| `streamlit-folium` | Embedding Folium maps inside Streamlit |
| `shapely` | Geometry backend for GeoPandas |

---

## Project Structure

```
.
├── app.py              # Single-file Streamlit application
├── Dockerfile          # Containerized deployment
└── requirements.txt    # Python dependencies
```

---

## Architecture

The application is a single-page Streamlit app with three layers:

```
User browser
  └── Streamlit app.py
        ├── UI controls          (commune, date, time band)
        ├── Data access layer    (SQLAlchemy → PostgreSQL/PostGIS → GeoPandas)
        └── Visualization layer  (Folium map + st.metric cards)
```

### Caching Strategy

| Function | Cache type | TTL | Purpose |
|---|---|---|---|
| `get_engine()` | `st.cache_resource` | lifetime | Single shared SQLAlchemy engine with `pool_pre_ping` |
| `get_comunas()` | `st.cache_data` | 1 hour | List of available communes |
| `get_rango_fechas()` | `st.cache_data` | 1 hour | Min/max date range from `velocidades_agregadas` |
| `cargar_datos()` | `st.cache_data` | 10 min | Spatial join of `arcos` + `velocidades_agregadas` |

---

## Database

The app connects to a **PostgreSQL/PostGIS** database via `DATABASE_URL` stored in Streamlit secrets. Two main tables are used:

| Table | Description |
|---|---|
| `arcos` | Road segment geometries with `id_arco`, `nombre`, `nombre_com`, `shape__len`, `geometry` |
| `velocidades_agregadas` | Aggregated speeds per segment, date, and time band (`velocidad_promedio`, `fecha`, `franja`) |

The core query joins both tables on `id_arco` and filters by commune, date, and time band.

---

## Speed Color Scale

Speeds are expressed as a fraction of the maximum speed for each segment:

| Speed range | Color | Meaning |
|---|---|---|
| < 0.4 | 🔴 `#d73027` | Congested |
| 0.4 – 0.6 | 🟠 `#fc8d59` | Moderately slow |
| 0.6 – 0.8 | 🟡 `#fee08b` | Medium |
| 0.8 – 1.0 | 🟢 `#d9ef8b` | Near free-flow |
| ≥ 1.0 | 🟢 `#1a9850` | Free-flow |

---

## Installation

**Requirements:** Python 3.11+

```bash
git clone https://github.com/mmatthieu1290/observatorio_velocidades_RM_Vregion.git
cd observatorio_velocidades_RM_Vregion
pip install -r requirements.txt
```

### System dependencies (required for GeoPandas + PostGIS)

On Debian/Ubuntu:
```bash
apt-get install libpq-dev gdal-bin libgdal-dev
```

Or use the provided Dockerfile (see below).

---

## Configuration

Create a `.streamlit/secrets.toml` file with your database connection string:

```toml
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
```

---

## Running the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Docker

A Dockerfile is included for containerized deployment:

```bash
docker build -t observatorio-velocidades .
docker run -p 8501:8501 observatorio-velocidades
```

The image is based on `python:3.11-slim` and installs all required system libraries (GDAL, libpq) before Python dependencies.

---

## License

This project is not currently under an open-source license. All rights reserved.
