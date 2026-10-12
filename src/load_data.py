from pathlib import Path
import os

import pandas as pd
import psycopg
from dotenv import load_dotenv


# 1- Configuration

load_dotenv()

PROCESSED_DIR = Path("data/processed")

RH_FILE = PROCESSED_DIR / "rh_clean.csv"
SPORT_FILE = PROCESSED_DIR / "sport_clean.csv"


# 2- Lecture des donées nettoyées

print("============= CHARGEMENT DES DONNEES =============")

rh = pd.read_csv(RH_FILE)
sport = pd.read_csv(SPORT_FILE)


# Conversion des dates

rh["Date de naissance"] = pd.to_datetime(
    rh["Date de naissance"]
).dt.date

rh["Date d'embauche"] = pd.to_datetime(
    rh["Date d'embauche"]
).dt.date


# 3- Connexion PostgresSQL

connection = psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5433"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)


try:

    with connection.cursor() as cursor:

        # Chargement RH

        rh_rows = [
            (
                int(row["ID salarié"]),
                row["Nom"],
                row["Prénom"],
                row["Date de naissance"],
                row["BU"],
                row["Date d'embauche"],
                float(row["Salaire brut"]),
                row["Type de contrat"],
                float(row["Nombre de jours de CP"]),
                row["Adresse du domicile"],
                row["Moyen de déplacement"],
            )
            for _, row in rh.iterrows()
        ]

        cursor.executemany(
            """
            INSERT INTO rh_employees (
                employee_id,
                last_name,
                first_name,
                birth_date,
                business_unit,
                hire_date,
                annual_gross_salary,
                contract_type,
                paid_leave_days,
                home_address,
                commute_mode
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (employee_id)
            DO UPDATE SET
                last_name = EXCLUDED.last_name,
                first_name = EXCLUDED.first_name,
                birth_date = EXCLUDED.birth_date,
                business_unit = EXCLUDED.business_unit,
                hire_date = EXCLUDED.hire_date,
                annual_gross_salary = EXCLUDED.annual_gross_salary,
                contract_type = EXCLUDED.contract_type,
                paid_leave_days = EXCLUDED.paid_leave_days,
                home_address = EXCLUDED.home_address,
                commute_mode = EXCLUDED.commute_mode;
            """,
            rh_rows,
        )


        # Chargement Sport

        sport_rows = []

        for _, row in sport.iterrows():

            sport_value = row["Pratique d'un sport"]

            if pd.isna(sport_value):
                sport_value = None

            sport_rows.append(
                (
                    int(row["ID salarié"]),
                    sport_value,
                )
            )


        cursor.executemany(
            """
            INSERT INTO rh_sport (
                employee_id,
                sport
            )
            VALUES (%s, %s)
            ON CONFLICT (employee_id)
            DO UPDATE SET
                sport = EXCLUDED.sport;
            """,
            sport_rows,
        )


    connection.commit()


    # 4- Vérification

    with connection.cursor() as cursor:

        cursor.execute(
            "SELECT COUNT(*) FROM rh_employees;"
        )
        employee_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM rh_sport;"
        )
        sport_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM rh_sport
            WHERE sport IS NOT NULL;
            """
        )
        employees_with_sport = cursor.fetchone()[0]


    print()
    print("============== CHARGEMENT TERMINE ===============")
    print(f"rh_employees : {employee_count} lignes")
    print(f"rh_sport     : {sport_count} lignes")
    print(
        f"Salariés avec un sport : "
        f"{employees_with_sport}"
    )


finally:

    connection.close()
