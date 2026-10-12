from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Recherche des fichiers sources
rh_path = next(RAW_DIR.glob("*RH.xlsx"))
sport_path = next(RAW_DIR.glob("*Sportive.xlsx"))

# Lecture des fichiers
rh = pd.read_excel(rh_path)
sport = pd.read_excel(sport_path)

print("======= DEBUT DU NETTOYAGE =======")


# 1- Nettoyage des noms de colonnes

rh.columns = rh.columns.str.strip()
sport.columns = sport.columns.str.strip()


# 2- Nettoyage des textes

for dataframe in [rh, sport]:
    text_columns = dataframe.select_dtypes(
    include=["object", "string"]).columns   

    for column in text_columns:
        dataframe[column] = dataframe[column].str.strip()


# 3- Vérification des identifiants salariés

rh["ID salarié"] = pd.to_numeric(
    rh["ID salarié"],
    errors="raise"
).astype(int)

sport["ID salarié"] = pd.to_numeric(
    sport["ID salarié"],
    errors="raise"
).astype(int)


# 4- Conversion des dates RH

rh["Date de naissance"] = pd.to_datetime(
    rh["Date de naissance"],
    errors="raise"
)

rh["Date d'embauche"] = pd.to_datetime(
    rh["Date d'embauche"],
    errors="raise"
)


# 5- Vérification des valeurs numériques

rh["Salaire brut"] = pd.to_numeric(
    rh["Salaire brut"],
    errors="raise"
)

rh["Nombre de jours de CP"] = pd.to_numeric(
    rh["Nombre de jours de CP"],
    errors="raise"
)


# 6- Correction du sport mal écrit

sport["Pratique d'un sport"] = sport[
    "Pratique d'un sport"
].replace({
    "Runing": "Running"
})


# 7- Le reste des contrôles

assert rh["ID salarié"].is_unique, \
    "Erreur : ID salarié dupliqué dans RH"

assert sport["ID salarié"].is_unique, \
    "Erreur : ID salarié dupliqué dans Sport"

assert set(rh["ID salarié"]) == set(sport["ID salarié"]), \
    "Erreur : les salariés RH et Sport ne correspondent pas"

assert (rh["Salaire brut"] >= 0).all(), \
    "Erreur : salaire négatif détecté"


# 8- Sauvegarde des données nettoyées

rh_output = PROCESSED_DIR / "rh_clean.csv"
sport_output = PROCESSED_DIR / "sport_clean.csv"

rh.to_csv(
    rh_output,
    index=False,
    encoding="utf-8-sig"
)

sport.to_csv(
    sport_output,
    index=False,
    encoding="utf-8-sig"
)


# 9- Résumé

print()
print("======= NETTOYAGE TERMINE =======")
print(f"RH : {len(rh)} lignes")
print(f"Sport : {len(sport)} lignes")

print()
print("Fichiers créés :")
print(rh_output)
print(sport_output)

print()
print("Sports après nettoyage :")
print(sport["Pratique d'un sport"].value_counts(dropna=False))
