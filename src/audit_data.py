from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")

# On cherche automatiquement les deux fichiers qui existe que dans notre PC Excel.
rh_path = next(RAW_DIR.glob("*RH.xlsx"))
sport_path = next(RAW_DIR.glob("*Sportive.xlsx"))

print("=== FICHIERS TROUVES ===")
print(f"RH     : {rh_path}")
print(f"Sport  : {sport_path}")

# Lecture des fichiers Excel
rh = pd.read_excel(rh_path)
sport = pd.read_excel(sport_path)


def audit_dataframe(name, df):
    
    print(f"\n{'=' * 50}")
    print(f"AUDIT : {name}")
    print("=" * 50)
    
    print(f"Nombre de lignes   : {len(df)}")
    print(f"Nombre de colonnes : {len(df.columns)}")

    print("\nColonnes :")
    for column in df.columns:
        print(f"- {column}")

    print("\nValeurs manquantes :")
    print(df.isna().sum())

    print("\nNombre de lignes dupliquees :")
    print(df.duplicated().sum())


audit_dataframe("DONNEES RH", rh)
audit_dataframe("DONNEES SPORTIVES", sport)

# Vérification des identifiants salariés
rh_ids = set(rh["ID salarié"])
sport_ids = set(sport["ID salarié"])

print("\n" + "=" * 50)
print("CONTROLE DES ID SALARIES")
print("=" * 50)

print(f"ID RH uniques      : {len(rh_ids)}")
print(f"ID Sport uniques   : {len(sport_ids)}")

print(f"ID présents uniquement dans RH : {rh_ids - sport_ids}")
print(f"ID présents uniquement dans Sport : {sport_ids - rh_ids}")

if rh_ids == sport_ids:
    print("OK : les deux fichiers contiennent les mêmes salariés.")
else:
    print("ATTENTION : les salariés ne correspondent pas exactement.")

print("\n" + "=" * 50)
print("MOYENS DE DEPLACEMENT")
print("=" * 50)
print(rh["Moyen de déplacement"].value_counts(dropna=False))

print("\n" + "=" * 50)
print("PRATIQUES SPORTIVES")
print("=" * 50)
print(sport["Pratique d'un sport"].value_counts(dropna=False))
