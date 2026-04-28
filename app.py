import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine, text
from datetime import date

st.set_page_config(page_title="Velocidades Santiago", layout="wide")

# ---------- Conexión ----------
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], pool_pre_ping=True)

# ---------- Catálogos ----------
@st.cache_data(ttl=3600)
def get_comunas():
    with get_engine().connect() as conn:
        result = conn.execute(text(
            "SELECT DISTINCT nombre_com FROM arcos "
            "WHERE nombre_com IS NOT NULL ORDER BY nombre_com"
        ))
        return [r[0] for r in result if r[0] not in ["BUIN","CALERA DE TANGO",
                                                     "LAMPA","PEÑAFLOR","PIRQUE",
                                                     "SAN JOSÉ DE MAIPO"]]

@st.cache_data(ttl=3600)
def get_rango_fechas():
    with get_engine().connect() as conn:
        result = conn.execute(text(
            "SELECT MIN(fecha), MAX(fecha) FROM velocidades_agregadas"
        ))
        return result.fetchone()

# ---------- Query principal ----------
@st.cache_data(ttl=600)
def cargar_datos(comuna, fecha_str, franja):
    query = """
        SELECT a.id_arco, a.nombre, a.nombre_com, a.shape__len,
               a.geometry, v.velocidad_promedio
        FROM arcos a
        JOIN velocidades_agregadas v ON a.id_arco = v.id_arco
        WHERE a.nombre_com = %(comuna)s
          AND v.fecha = %(fecha)s
          AND v.franja = %(franja)s
    """
    return gpd.read_postgis(
        query, get_engine(), geom_col="geometry",
        params={"comuna": comuna, "fecha": fecha_str, "franja": franja}
    )

# ---------- UI ----------
st.title("Velocidades por comuna - Santiago")

col1, col2, col3 = st.columns(3)

with col1:
    comuna = st.selectbox("Comuna", get_comunas())

with col2:
    fecha_min, fecha_max = get_rango_fechas()
    fecha = st.date_input(
        "Fecha",
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max,
    )

with col3:
    franja = st.radio("Franja horaria", ["manana", "tarde"], horizontal=True)

# ---------- Resultado ----------
gdf = cargar_datos(comuna, fecha.isoformat(), franja)

if len(gdf) == 0:
    st.warning("No hay datos para esta combinación.")
    st.stop()

# Velocidad ponderada por largo del arco
largo_total = gdf["shape__len"].sum()
vel_pond = (gdf["velocidad_promedio"] * gdf["shape__len"]).sum() / largo_total

col_a, col_b, col_c = st.columns(3)
col_a.metric("Velocidad ponderada promedio", f"{vel_pond:.2f}")
col_b.metric("N° de arcos", len(gdf))
col_c.metric("Largo total (m)", f"{largo_total:,.0f}")

# ---------- Mapa ----------
# Centro del mapa = centroide del conjunto
centro = gdf.geometry.unary_union.centroid
m = folium.Map(location=[centro.y, centro.x], zoom_start=14, tiles="cartodbpositron")

# Color según velocidad: rojo lento, verde rápido
def color_velocidad(v):
    if v < 0.4:
        return "#d73027"
    elif v < 0.6:
        return "#fc8d59"
    elif v < 0.8:
        return "#fee08b"
    elif v < 1.0:
        return "#d9ef8b"
    else:
        return "#1a9850"

for _, row in gdf.iterrows():
    folium.GeoJson(
        row["geometry"].__geo_interface__,
        style_function=lambda x, v=row["velocidad_promedio"]: {
            "color": color_velocidad(v),
            "weight": 4,
            "opacity": 0.8,
        },
        tooltip=folium.Tooltip(
            f"<b>{row['nombre']}</b><br>"
            f"Velocidad: {row['velocidad_promedio']:.2f}<br>"
            f"Largo: {row['shape__len']:.0f} m"
        ),
    ).add_to(m)

st_folium(m, width=None, height=600, returned_objects=[])