from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="L'électricité dans 12 quartiers", page_icon="⚡", layout="wide")

st.title("L'électricité dans 12 quartiers")
st.caption("Relevés mensuels de janvier 2024 à décembre 2025. Données fictives.")

# Charger le fichier propre avec du cache
@st.cache_data
def charger_donnees():
    return pd.read_csv(DOSSIER / "consommation_propre.csv")

df = charger_donnees()

# Filtres dans la barre latérale
st.sidebar.header("Filtres")

toutes_communes = sorted(df['commune'].unique())
communes_selectionnees = st.sidebar.multiselect(
    "Communes",
    options=toutes_communes,
    default=toutes_communes
)

annees_disponibles = sorted(df['annee'].astype(str).unique())
annee_defaut_idx = annees_disponibles.index("2025") if "2025" in annees_disponibles else 0
annee_selectionnee = st.sidebar.selectbox(
    "Année",
    options=annees_disponibles,
    index=annee_defaut_idx
)

# Filtrage du DataFrame
df_filtre = df[
    (df['commune'].isin(communes_selectionnees)) & 
    (df['annee'].astype(str) == str(annee_selectionnee))
]

# Vérification si aucune commune n'est sélectionnée
if not communes_selectionnees:
    st.warning("Veuillez sélectionner au moins une commune dans la barre latérale.")
else:
    # Trois indicateurs clés (KPIs)
    st.subheader("Indicateurs clés")
    col1, col2, col3 = st.columns(3)
    
    conso_totale = df_filtre['kwh'].sum() / 1e6  # en millions de kWh
    conso_moy_abonne = df_filtre['kwh_par_abonne'].mean() if not df_filtre.empty else 0
    heures_moy = df_filtre['heures_courant'].mean() if not df_filtre.empty else 0
    
    col1.metric("Consommation totale", f"{conso_totale:.2f} M kWh")
    col2.metric("Moyenne par abonné", f"{conso_moy_abonne:.1f} kWh")
    col3.metric("Heures de courant moy.", f"{heures_moy:.1f} h")
    
    st.markdown("---")

    # Onglets d'analyse (parties 4 à 8 du notebook)
    onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs([
        "Quartiers & Types", 
        "Évolution Commune", 
        "Chaleur ou Courant ?", 
        "Coupures", 
        "Top Relevés"
    ])

    with onglet1:
        st.subheader("Consommation par type de quartier")
        if not df_filtre.empty:
            conso_type = df_filtre.groupby('type')['kwh_par_abonne'].mean().reset_index()
            st.bar_chart(conso_type.set_index('type'))
        else:
            st.info("Aucune donnée disponible pour les filtres sélectionnés.")

    with onglet2:
        st.subheader("Évolution mensuelle par commune")
        if not df_filtre.empty:
            pivot_commune = df_filtre.pivot_table(index='mois', columns='commune', values='kwh_par_abonne', aggfunc='mean')
            st.line_chart(pivot_commune)
        else:
            st.info("Aucune donnée disponible.")

    with onglet3:
        st.subheader("Chaleur ou heures de courant ? (Résidentiel)")
        residentiel_filtre = df_filtre[df_filtre['type'] == 'Résidentiel']
        if not residentiel_filtre.empty:
            corr_h = residentiel_filtre['kwh_par_abonne'].corr(residentiel_filtre['heures_courant'])
            corr_t = residentiel_filtre['kwh_par_abonne'].corr(residentiel_filtre['temperature_c'])
            st.write(f"**Corrélation avec les heures de courant :** {corr_h:.2f}")
            st.write(f"**Corrélation avec la température :** {corr_t:.2f}")
        else:
            st.info("Pas de données résidentielles pour ces filtres.")

    with onglet4:
        st.subheader("Analyse des coupures de courant")
        if not df_filtre.empty:
            stats_c = df_filtre.groupby('commune')['heures_courant'].agg(['median', lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)])
            stats_c.columns = ['Médiane', 'Q1', 'Q3']
            st.dataframe(stats_c)
        else:
            st.info("Aucune donnée disponible.")

    with onglet5:
        st.subheader("Les 3 plus grosses consommations")
        top3 = df_filtre.nlargest(3, 'kwh')[['mois', 'quartier', 'type', 'kwh']]
        st.dataframe(top3, hide_index=True)

    # Conclusion et Données filtrées dans un expander
    st.markdown("---")
    st.subheader("Conclusion")
    st.markdown("""
    La consommation électrique montre une forte corrélation positive avec les heures de courant (0.76) 
    et une corrélation légèrement négative avec la température (-0.15). Cependant, rappelons qu'une corrélation 
    statistique ne permet pas de conclure hâtivement à une relation de cause à effet directe sans analyse approfondie.
    """)

    with st.expander("Voir le tableau complet des données filtrées"):
        st.dataframe(df_filtre, hide_index=True)