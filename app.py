import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(
    page_title="Matriz general IPP",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

TECLAB_COLORS = {
    "deep_teal": "#03323d",
    "teal": "#00b7c2",
    "magenta": "#d70f64",
    "soft_gray": "#f2f6f9",
    "dark_gray": "#2d2d2d",
}

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #ffffff 0%, {TECLAB_COLORS['soft_gray']} 100%);
        color: {TECLAB_COLORS['dark_gray']};
    }}
    .stHeader h1 {{
        color: {TECLAB_COLORS['deep_teal']};
    }}
    .metrics-row {{
        background: #fff;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 0 16px rgba(0, 0, 0, 0.08);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    return df

DATA_PATH = "Matriz general IPP completa actualizada.xlsx"
try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"No se encuentra el archivo '{DATA_PATH}'. Asegurate de ejecutarlo desde la carpeta que contiene el .xlsx.")
    st.stop()

st.title("Matriz general IPP")
st.markdown(
    """
    <p style='color:#555;'>Esta versión interactiva replica la paleta Teclab y permite explorar la matriz por carrera, año y campo de formación.
    El dashboard en la parte inferior muestra qué campos ya están documentados y qué falta completar.</p>
    """,
    unsafe_allow_html=True,
)

FIELDS = [
    "PERIODO",
    "CAMPO DE FORMACIÓN",
    "CARGA HORARIA",
    "OBJETIVOS DE LA MATERIA",
    "CONTENIDOS MÍNIMOS",
    "BIBLIOGRAFÍA DE CONSULTA",
    "PRODUCCIÓN DE CONTENIDOS",
    "CARRERAS",
    "AÑO",
]

total_rows = len(df)
metrics = []
for label in FIELDS:
    filled = df[label].notna().sum()
    percent = (filled / total_rows) * 100 if total_rows else 0
    metrics.append((label, filled, total_rows - filled, f"{percent:.1f}%"))

st.markdown("### Cobertura de campos clave")
metric_cols = st.columns(4)
for idx, (label, filled, missing, percent) in enumerate(metrics):
    col = metric_cols[idx % 4]
    col.metric(
        label,
        f"{percent}",
        f"{filled} completados / {missing} faltantes",
        delta_color="inverse",
    )

st.sidebar.header("Filtros rápidos")
carrera_filter = st.sidebar.multiselect(
    "Carrera",
    sorted(df["CARRERAS"].dropna().unique()),
)
año_filter = st.sidebar.multiselect("Año", sorted(df["AÑO"].dropna().unique()))
periodo_filter = st.sidebar.multiselect("Periodo", sorted(df["PERIODO"].dropna().unique()))

filtered = df.copy()
if carrera_filter:
    filtered = filtered[filtered["CARRERAS"].isin(carrera_filter)]
if año_filter:
    filtered = filtered[filtered["AÑO"].isin(año_filter)]
if periodo_filter:
    filtered = filtered[filtered["PERIODO"].isin(periodo_filter)]

st.subheader("Matriz filtrada")
st.markdown(
    "<div style='border:1px solid #e0e0e0;padding:12px;border-radius:12px;background:#fff'>"
    f"<strong>{len(filtered):,}</strong> filas cumplen con los filtros seleccionados.</div>",
    unsafe_allow_html=True,
)
st.dataframe(filtered, use_container_width=True)

@st.cache_data
def to_excel(data: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    data.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

st.download_button(
    label="Descargar matriz filtrada",
    data=to_excel(filtered),
    file_name="matriz-ipp-filtrada.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")
st.subheader("Dashboard de faltantes")
st.markdown(
    "<p style='color:#555;'>Estos valores ayudan a monitorear cuánto falta completar antes de subir la matriz oficial.</p>",
    unsafe_allow_html=True,
)
dashboard = pd.DataFrame(
    metrics,
    columns=["Campo", "Completados", "Faltantes", "% Completado"],
)
st.bar_chart(data=dashboard.set_index("Campo"))
