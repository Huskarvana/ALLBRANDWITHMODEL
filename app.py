import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Veille Marques Auto", layout="wide")
st.title("🚗 Agent de Veille – Marques Concurrentes (version légère)")

API_KEY_NEWSDATA = st.secrets["API_KEY_NEWSDATA"]
MEDIASTACK_API_KEY = st.secrets["MEDIASTACK_API_KEY"]

MARQUES = [
    "DS Automobiles", "Volvo", "BMW", "Audi", "Mercedes-Benz",
    "Peugeot", "Renault", "Citroën", "Lexus", "Jaguar", "Tesla"
]

MODELES_PAR_MARQUE = {
    "DS Automobiles": ["DS3", "DS4", "DS7", "DS9", "Jules Verne", "N°4", "Numero 4", "N4"],
    "BMW": ["iX", "X1", "X3", "X5"],
    "Audi": ["Q3", "Q5", "Q7", "A3", "A4"],
    "Mercedes-Benz": ["EQB", "GLA", "GLC", "Classe A"],
    "Volvo": ["XC40", "XC60", "EX30", "EX90"],
    "Peugeot": ["2008", "3008", "508"],
    "Renault": ["Austral", "Megane E-Tech", "Scenic", "Captur"],
    "Citroën": ["C3", "C4", "C5", "Ami"],
    "Lexus": ["UX", "NX", "RX"],
    "Jaguar": ["E-PACE", "F-PACE", "I-PACE"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X"]
}

LANGUES_DISPONIBLES = ["all", "fr", "en", "de", "es", "it", "pt", "nl"]

def fetch_newsdata_articles(query, max_results=5, lang=None):
    params = {"apikey": API_KEY_NEWSDATA, "q": query}
    if lang and lang != "all":
        params["language"] = lang
    try:
        response = requests.get("https://newsdata.io/api/1/news", params=params)
        data = response.json()
        return [{
            "date": item.get("pubDate", ""),
            "titre": item.get("title", ""),
            "contenu": item.get("description", ""),
            "source": item.get("source_id", ""),
            "lien": item.get("link", "")
        } for item in data.get("results", [])[:max_results]]
    except:
        return []

def fetch_mediastack_articles(query, max_results=5, lang=None):
    params = {"access_key": MEDIASTACK_API_KEY, "keywords": query}
    if lang and lang != "all":
        params["languages"] = lang
    try:
        response = requests.get("http://api.mediastack.com/v1/news", params=params)
        data = response.json()
        return [{
            "date": item.get("published_at", ""),
            "titre": item.get("title", ""),
            "contenu": item.get("description", ""),
            "source": item.get("source", ""),
            "lien": item.get("url", "")
        } for item in data.get("data", [])[:max_results]]
    except:
        return []

def detecter_modele(titre, marque):
    if marque in MODELES_PAR_MARQUE:
        for modele in MODELES_PAR_MARQUE[marque]:
            if modele.lower() in titre.lower():
                return modele
    return "Global"

# --- INTERFACE UTILISATEUR ---
st.sidebar.title("Filtres de veille")
filtre_marque = st.sidebar.selectbox("Choisir la marque à surveiller", MARQUES)
filtre_modele = st.sidebar.selectbox("Filtrer par modèle", ["Tous"] + MODELES_PAR_MARQUE.get(filtre_marque, []))
nb_articles = st.sidebar.slider("Nombre d'articles par source", 5, 30, 10)
filtre_langue = st.sidebar.selectbox("Filtrer par langue", LANGUES_DISPONIBLES)

if st.button("🔍 Lancer la veille"):
    lang = None if filtre_langue == "all" else filtre_langue
    newsdata = fetch_newsdata_articles(filtre_marque, nb_articles, lang)
    mediastack = fetch_mediastack_articles(filtre_marque, nb_articles, lang)

    articles = pd.DataFrame(newsdata + mediastack)

    if not articles.empty:
        articles['modèle'] = articles['titre'].apply(lambda t: detecter_modele(t, filtre_marque))
        articles['date'] = pd.to_datetime(articles['date'], errors='coerce')
        articles = articles.sort_values(by='date', ascending=False)

        if filtre_modele != "Tous":
            articles = articles[articles['modèle'] == filtre_modele]

        st.dataframe(articles[['date', 'titre', 'modèle', 'contenu', 'source', 'lien']])
    else:
        st.warning("Aucun article trouvé.")