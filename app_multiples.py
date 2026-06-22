import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- Translations ----------
TRANSLATIONS = {
    "de": {
        "page_title": "Peergruppen – Marktansatz",
        "title": "Peergruppen im Marktansatz",
        "filter_header": "Filter",
        "result_header": "Ergebnis",
        "no_results": "Keine Unternehmen entsprechen den gewählten Filtern.",
        "source": "Quelle: Yahoo Finance",
        "summary": (
            "Der durchschnittliche EV/EBITDA-Multiplikator dieser Peergruppe beträgt {avg:.1f}x. "
            "Daraus folgt ein Unternehmenswert der WholeFood AI AG von CHF {value:.0f} Mio."
        ),
        "col_labels": {
            "Unternehmen": "Unternehmen",
            "Standort": "Standort",
            "Branche": "Branche",
            "Grösse": "Grösse",
            "EV/EBITDA": "EV/EBITDA",
        },
        "filter_labels": {
            "Standort": "Standort",
            "Branche": "Branche",
            "Grösse": "Grösse",
        },
    },
    "en": {
        "page_title": "Peer Groups – Market Approach",
        "title": "Peer Groups in the Market Approach",
        "filter_header": "Filters",
        "result_header": "Results",
        "no_results": "No companies match the selected filters.",
        "source": "Source: Yahoo Finance",
        "summary": (
            "The average EV/EBITDA multiple of this peer group is {avg:.1f}x. "
            "This implies an enterprise value of WholeFood AI AG of CHF {value:.0f}m."
        ),
        "col_labels": {
            "Unternehmen": "Company",
            "Standort": "Location",
            "Branche": "Industry",
            "Grösse": "Size",
            "EV/EBITDA": "EV/EBITDA",
        },
        "filter_labels": {
            "Standort": "Location",
            "Branche": "Industry",
            "Grösse": "Size",
        },
    },
    "fr": {
        "page_title": "Groupes de pairs – Approche de marché",
        "title": "Groupes de pairs dans l'approche de marché",
        "filter_header": "Filtres",
        "result_header": "Résultats",
        "no_results": "Aucune entreprise ne correspond aux filtres sélectionnés.",
        "source": "Source : Yahoo Finance",
        "summary": (
            "Le multiple EV/EBITDA moyen de ce groupe de pairs est de {avg:.1f}x. "
            "Cela implique une valeur d'entreprise de WholeFood AI AG de CHF {value:.0f} Mio."
        ),
        "col_labels": {
            "Unternehmen": "Entreprise",
            "Standort": "Localisation",
            "Branche": "Secteur",
            "Grösse": "Taille",
            "EV/EBITDA": "EV/EBITDA",
        },
        "filter_labels": {
            "Standort": "Localisation",
            "Branche": "Secteur",
            "Grösse": "Taille",
        },
    },
}

SUPPORTED_LANGS = list(TRANSLATIONS.keys())
LANG_NAMES = {"de": "Deutsch", "en": "English", "fr": "Français"}

# ---------- Value translations (exact values from the Excel) ----------
VALUE_MAPS = {
    "en": {
        "Standort": {
            "Asien":          "Asia",
            "Europa":         "Europe",
            "Lateinamerika":  "Latin America",
            "Nordamerika":    "North America",
            "Schweiz":        "Switzerland",
        },
        "Branche": {
            "Food-Tech":               "Food Tech",
            "KI & Technologie":        "AI & Technology",
            "Lebensmittelverarbeiter": "Food Processors",
        },
        "Grösse": {
            "Gross":           "Large",
            "Klein bis Mittel": "Small to Medium",
        },
    },
    "fr": {
        "Standort": {
            "Asien":          "Asie",
            "Europa":         "Europe",
            "Lateinamerika":  "Amérique latine",
            "Nordamerika":    "Amérique du Nord",
            "Schweiz":        "Suisse",
        },
        "Branche": {
            "Food-Tech":               "Food Tech",
            "KI & Technologie":        "IA & Technologie",
            "Lebensmittelverarbeiter": "Transformateurs alimentaires",
        },
        "Grösse": {
            "Gross":           "Grande",
            "Klein bis Mittel": "Petite à moyenne",
        },
    },
}


def translate_values(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    if lang == "de" or lang not in VALUE_MAPS:
        return df
    df = df.copy()
    col_maps = VALUE_MAPS[lang]
    for col, mapping in col_maps.items():
        if col in df.columns:
            df[col] = df[col].map(lambda v: mapping.get(v, v))
    return df


# ---------- Language detection ----------
# Priority: URL query param ?lang=xx  →  sidebar selector
query_lang = st.query_params.get("lang", "").lower()
if query_lang not in SUPPORTED_LANGS:
    query_lang = None

if query_lang is None:
    with st.sidebar:
        lang = st.selectbox(
            "Language / Sprache / Langue",
            options=SUPPORTED_LANGS,
            format_func=lambda x: LANG_NAMES[x],
            index=0,
        )
else:
    lang = query_lang

t = TRANSLATIONS[lang]

# ---------- Page config ----------
st.set_page_config(page_title=t["page_title"], layout="centered")
st.title(t["title"])

# ---------- Load & translate data ----------
EXCEL_FILE = Path(__file__).parent / "Peergruppen_Uebersicht_Input_streamlit.xlsx"
FILTER_COLS = ["Standort", "Branche", "Grösse"]


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["EV/EBITDA"] = pd.to_numeric(df["EV/EBITDA"], errors="coerce")
    df = df.dropna(subset=["Unternehmen", "EV/EBITDA"])
    return df


df = translate_values(load_data(EXCEL_FILE), lang)

# ---------- Filters ----------
st.subheader(t["filter_header"])
filters = {}
cols = st.columns(len(FILTER_COLS))

for col_widget, col_name in zip(cols, FILTER_COLS):
    with col_widget:
        label = t["filter_labels"][col_name]
        options = sorted(df[col_name].dropna().unique().tolist())
        selected = st.multiselect(label, options=options, default=[])
        filters[col_name] = selected

# ---------- Filter data ----------
filtered = df.copy()
for col_name, selected in filters.items():
    if selected:
        filtered = filtered[filtered[col_name].isin(selected)]

# ---------- Output ----------
st.subheader(t["result_header"])

if filtered.empty:
    st.info(t["no_results"])
else:
    display_cols = ["Unternehmen", "Standort", "Branche", "Grösse", "EV/EBITDA"]
    out = filtered[display_cols].reset_index(drop=True)

    out = out.rename(columns=t["col_labels"])
    ev_col = t["col_labels"]["EV/EBITDA"]

    styled = out.style.format({ev_col: "{:.1f}x"}).hide(axis="index")
    st.dataframe(styled, use_container_width=True)
    st.caption(t["source"])

    avg = filtered["EV/EBITDA"].mean()
    st.markdown(f"**{t['summary'].format(avg=avg, value=avg * 100)}**")
