import pandas as pd
import streamlit as st
from io import BytesIO
import unicodedata
import re

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
    "white": "#ffffff",
    "border": "#d9e7ec",
}

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #ffffff 0%, {TECLAB_COLORS['soft_gray']} 100%);
        color: {TECLAB_COLORS['dark_gray']};
    }}
    h1, h2, h3 {{
        color: {TECLAB_COLORS['deep_teal']};
    }}
    h1 {{
        border-left: 8px solid {TECLAB_COLORS['magenta']};
        padding-left: 16px;
    }}
    section[data-testid="stSidebar"] {{
        background: {TECLAB_COLORS['deep_teal']};
    }}
    section[data-testid="stSidebar"] * {{
        color: {TECLAB_COLORS['white']} !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] div {{
        color: {TECLAB_COLORS['dark_gray']} !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="tag"] {{
        background: {TECLAB_COLORS['teal']} !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="radio"] div[aria-checked="true"] {{
        border-color: {TECLAB_COLORS['magenta']} !important;
    }}
    div[data-testid="stMetric"] {{
        background: {TECLAB_COLORS['white']};
        border: 1px solid {TECLAB_COLORS['border']};
        border-left: 6px solid {TECLAB_COLORS['teal']};
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 8px 20px rgba(3, 50, 61, 0.08);
    }}
    div[data-testid="stMetric"] label {{
        color: {TECLAB_COLORS['deep_teal']} !important;
        font-weight: 700;
    }}
    div[data-testid="stMetricValue"] {{
        color: {TECLAB_COLORS['magenta']};
    }}
    .teclab-panel {{
        background: {TECLAB_COLORS['white']};
        border: 1px solid {TECLAB_COLORS['border']};
        border-left: 6px solid {TECLAB_COLORS['magenta']};
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 8px 20px rgba(3, 50, 61, 0.08);
    }}
    .teclab-panel strong {{
        color: {TECLAB_COLORS['magenta']};
    }}
    .stButton > button, .stDownloadButton > button {{
        background: {TECLAB_COLORS['magenta']};
        border: 1px solid {TECLAB_COLORS['magenta']};
        color: {TECLAB_COLORS['white']};
        border-radius: 8px;
        font-weight: 700;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: {TECLAB_COLORS['deep_teal']};
        border-color: {TECLAB_COLORS['deep_teal']};
        color: {TECLAB_COLORS['white']};
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {TECLAB_COLORS['border']};
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(3, 50, 61, 0.06);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    return normalize_data(df)

def clean_value(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).replace("\xa0", " ").strip()
    return text or None


def split_values(value) -> list[str]:
    text = clean_value(value)
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def normalize_period(value) -> str | None:
    text = clean_value(value)
    if not text:
        return None
    compact = re.sub(r"\s+", "", text.upper())
    match = re.fullmatch(r"(\d)A/B", compact)
    if match:
        number = match.group(1)
        return f"{number}A / {number}B"
    match = re.fullmatch(r"(\d)([AB])", compact)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return text


def period_values(value) -> list[str]:
    text = normalize_period(value)
    if not text:
        return []
    match = re.fullmatch(r"(\d)A\s*/\s*(\d)?B", text.upper())
    if match:
        number = match.group(1)
        return [f"{number}A", f"{number}B"]
    return split_values(text)


def normalize_data(data: pd.DataFrame) -> pd.DataFrame:
    normalized = data.copy()
    normalized["PERIODO"] = normalized["PERIODO"].apply(normalize_period)
    return normalized


def unique_values(values, split: bool = False) -> list[str]:
    seen = set()
    result = []
    for value in values:
        parts = split_values(value) if split else [clean_value(value)]
        for part in parts:
            if part and part not in seen:
                seen.add(part)
                result.append(part)
    return result


def filter_options(data: pd.DataFrame, column: str) -> list[str]:
    return sorted(unique_values(data[column], split=True))


def period_filter_options(data: pd.DataFrame) -> list[str]:
    return sorted(unique_values(data["PERIODO"].apply(period_values).explode(), split=False))


def matches_any(value, selected: list[str]) -> bool:
    return bool(set(split_values(value)) & set(selected))


def matches_period(value, selected: list[str]) -> bool:
    return bool(set(period_values(value)) & set(selected))


def sort_text(value) -> str:
    text = clean_value(value) or ""
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char)).upper()


def build_clean_matrix(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data.copy()

    return data.sort_values("MATERIA", key=lambda values: values.map(sort_text), kind="mergesort")


def build_metrics(data: pd.DataFrame) -> list[tuple[str, int, int, str]]:
    total_rows = len(data)
    metrics = []
    for label in FIELDS:
        filled = data[label].notna().sum()
        percent = (filled / total_rows) * 100 if total_rows else 0
        metrics.append((label, filled, total_rows - filled, f"{percent:.1f}%"))
    return metrics


def render_metrics(metrics: list[tuple[str, int, int, str]]) -> None:
    metric_cols = st.columns(4)
    for idx, (label, filled, missing, percent) in enumerate(metrics):
        col = metric_cols[idx % 4]
        col.metric(
            label,
            f"{percent}",
            f"{filled} completados / {missing} faltantes",
            delta_color="inverse",
        )


@st.cache_data
def to_excel(data: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    data.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

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
    La matriz limpia conserva las filas originales y solo las ordena por materia, sin combinar información entre registros.</p>
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

clean_matrix = build_clean_matrix(df)
metrics = build_metrics(clean_matrix)
page = st.sidebar.radio("Página", ["Matriz", "Info"])

if page == "Matriz":
    st.markdown("### Cobertura de campos clave")
    render_metrics(metrics)

    st.sidebar.header("Filtros rápidos")
    carrera_filter = st.sidebar.multiselect(
        "Carrera",
        filter_options(df, "CARRERAS"),
    )
    año_filter = st.sidebar.multiselect("Año", filter_options(df, "AÑO"))
    periodo_filter = st.sidebar.multiselect("Periodo", period_filter_options(df))

    filtered = df.copy()
    if carrera_filter:
        filtered = filtered[filtered["CARRERAS"].apply(lambda value: matches_any(value, carrera_filter))]
    if año_filter:
        filtered = filtered[filtered["AÑO"].apply(lambda value: matches_any(value, año_filter))]
    if periodo_filter:
        filtered = filtered[filtered["PERIODO"].apply(lambda value: matches_period(value, periodo_filter))]

    matrix_view = build_clean_matrix(filtered)
    unique_subjects = matrix_view["MATERIA"].nunique(dropna=True)

    st.subheader("Matriz filtrada")
    st.markdown(
        "<div class='teclab-panel'>"
        f"<strong>{len(matrix_view):,}</strong> filas cumplen con los filtros seleccionados "
        f"({unique_subjects:,} materias, sin mezclar información entre filas).</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(matrix_view, width="stretch")

    st.download_button(
        label="Descargar matriz filtrada",
        data=to_excel(matrix_view),
        file_name="matriz-ipp-filtrada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.subheader("Info")

    info_cols = st.columns(4)
    info_cols[0].metric("Filas originales", f"{len(df):,}")
    info_cols[1].metric("Materias únicas", f"{df['MATERIA'].nunique(dropna=True):,}")
    info_cols[2].metric("Carreras", f"{len(filter_options(df, 'CARRERAS')):,}")
    info_cols[3].metric("Períodos", f"{len(period_filter_options(df)):,}")

    st.markdown("### Lógica de limpieza")
    st.markdown(
        """
        <div class='teclab-panel'>
        La matriz limpia no mezcla filas. Mantiene cada registro original de la matriz general completa y
        solamente ordena por `MATERIA`. Si una materia tiene 1, 2, 3 o más filas, esas filas se muestran juntas
        para conservar su carrera, período, año, campo y demás información exactamente en su propia fila.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Cobertura global")
    render_metrics(metrics)

    st.markdown("### Campos auditados")
    dashboard = pd.DataFrame(
        metrics,
        columns=["Campo", "Completados", "Faltantes", "% Completado"],
    )
    st.dataframe(dashboard, width="stretch", hide_index=True)
    st.bar_chart(data=dashboard.set_index("Campo"))

    st.markdown("### Matriz limpia")
    st.dataframe(clean_matrix, width="stretch")
    st.download_button(
        label="Descargar matriz limpia",
        data=to_excel(clean_matrix),
        file_name="matriz-limpia.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
