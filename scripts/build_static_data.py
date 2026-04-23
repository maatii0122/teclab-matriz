from __future__ import annotations

import json
import shutil
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Matriz general IPP completa actualizada.xlsx"
CLEAN_XLSX = ROOT / "Matriz limpia.xlsx"
PUBLIC_DATA = ROOT / "public" / "data" / "matriz.json"
PUBLIC_XLSX = ROOT / "public" / "Matriz limpia.xlsx"

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

MULTI_VALUE_COLUMNS = {
    "CÓDIGO",
    "PERIODO",
    "CAMPO DE FORMACIÓN",
    "PRODUCCIÓN DE CONTENIDOS",
    "CARRERAS",
    "AÑO",
    "ENUNCIADOS",
    "PRODUCCIÓN DE CONTENIDOS DE LA MATERIA",
    "IMPLEMENTACIÓN REDISEÑO",
    "TIPO DE REDISEÑO",
    "ACTUALIZACIÓN",
    "PERIODO DE IMPACTO",
}

SPLIT_VALUE_COLUMNS = {
    "CÓDIGO",
    "PERIODO",
    "CAMPO DE FORMACIÓN",
    "CARRERAS",
    "AÑO",
    "IMPLEMENTACIÓN REDISEÑO",
    "TIPO DE REDISEÑO",
    "ACTUALIZACIÓN",
    "PERIODO DE IMPACTO",
}


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


def join_unique(values, split: bool = False) -> str | None:
    items = unique_values(values, split=split)
    return ", ".join(items) if items else None


def first_non_empty(values) -> str | None:
    for value in values:
        text = clean_value(value)
        if text:
            return text
    return None


def sort_text(value) -> str:
    text = clean_value(value) or ""
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char)).upper()


def build_subject_view(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in data.groupby("MATERIA", dropna=False, sort=False):
        row = {}
        for column in data.columns:
            if column == "MATERIA":
                row[column] = first_non_empty(group[column])
            elif column in MULTI_VALUE_COLUMNS:
                row[column] = join_unique(group[column], split=column in SPLIT_VALUE_COLUMNS)
            else:
                row[column] = first_non_empty(group[column])
        rows.append(row)

    subject_view = pd.DataFrame(rows, columns=data.columns)
    return subject_view.sort_values("MATERIA", key=lambda values: values.map(sort_text), kind="mergesort")


def records(data: pd.DataFrame) -> list[dict[str, str]]:
    normalized = data.fillna("")
    return normalized.to_dict(orient="records")


def metrics(data: pd.DataFrame) -> list[dict[str, str | int]]:
    total = len(data)
    result = []
    for field in FIELDS:
        filled = int(data[field].notna().sum())
        missing = total - filled
        percent = f"{((filled / total) * 100 if total else 0):.1f}%"
        result.append({"field": field, "filled": filled, "missing": missing, "percent": percent})
    return result


def main() -> None:
    raw = pd.read_excel(SOURCE, engine="openpyxl")
    clean = build_subject_view(raw)

    PUBLIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "columns": list(raw.columns),
        "fields": FIELDS,
        "rawRows": records(raw),
        "cleanRows": records(clean),
        "metrics": metrics(clean),
        "stats": {
            "rawRows": len(raw),
            "cleanRows": len(clean),
            "careers": len(unique_values(raw["CARRERAS"], split=True)),
            "periods": len(unique_values(raw["PERIODO"], split=True)),
        },
    }

    PUBLIC_DATA.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    clean.to_excel(CLEAN_XLSX, index=False)
    shutil.copyfile(CLEAN_XLSX, PUBLIC_XLSX)

    print(f"Wrote {PUBLIC_DATA.relative_to(ROOT)}")
    print(f"Wrote {CLEAN_XLSX.name}")
    print(f"Wrote {PUBLIC_XLSX.relative_to(ROOT)}")
    print(f"Rows: {len(raw)} raw -> {len(clean)} clean")


if __name__ == "__main__":
    main()
