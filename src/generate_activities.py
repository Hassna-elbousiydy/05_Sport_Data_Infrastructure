from datetime import datetime, timedelta
import os
import random

import psycopg
from dotenv import load_dotenv


 # CONFIGURATION
 
load_dotenv()

# Seed fixe pour pouvoir reproduire la même simulation.
random.seed(42)

END_DATE = datetime(2026, 10, 19, 23, 59, 59)
START_DATE = END_DATE - timedelta(days=365)


 # PARAMETRES PAR SPORT
 
SPORT_RULES = {
    "Running": {
        "duration": (20, 120),
        "distance": (3000, 20000),
    },
    "Randonnée": {
        "duration": (60, 360),
        "distance": (5000, 30000),
    },
    "Natation": {
        "duration": (30, 120),
        "distance": (500, 5000),
    },
    "Triathlon": {
        "duration": (60, 300),
        "distance": (10000, 60000),
    },

    # Pour ces sports, une distance n'est pas pertinente.
    "Tennis": {
        "duration": (45, 150),
        "distance": None,
    },
    "Football": {
        "duration": (45, 120),
        "distance": None,
    },
    "Rugby": {
        "duration": (45, 120),
        "distance": None,
    },
    "Badminton": {
        "duration": (30, 120),
        "distance": None,
    },
    "Voile": {
        "duration": (60, 300),
        "distance": None,
    },
    "Judo": {
        "duration": (45, 120),
        "distance": None,
    },
    "Boxe": {
        "duration": (30, 120),
        "distance": None,
    },
    "Escalade": {
        "duration": (60, 240),
        "distance": None,
    },
    "Équitation": {
        "duration": (45, 180),
        "distance": None,
    },
    "Tennis de table": {
        "duration": (30, 120),
        "distance": None,
    },
    "Basketball": {
        "duration": (45, 120),
        "distance": None,
    },
}


COMMENTS = [
    None,
    None,
    None,
    "Bonne séance",
    "Entraînement du jour",
    "Sortie entre collègues",
    "Reprise du sport :)",
]


 # FONCTIONS
 
def random_datetime():
    total_seconds = int(
        (END_DATE - START_DATE).total_seconds()
    )

    offset = random.randint(0, total_seconds)

    return START_DATE + timedelta(seconds=offset)


def create_activity(employee_id, sport):

    rule = SPORT_RULES[sport]

    start_date = random_datetime()

    duration_minutes = random.randint(
        rule["duration"][0],
        rule["duration"][1],
    )

    end_date = start_date + timedelta(
        minutes=duration_minutes
    )

    if rule["distance"] is None:
        distance = None
    else:
        distance = random.randint(
            rule["distance"][0],
            rule["distance"][1],
        )

    comment = random.choice(COMMENTS)

    return (
        employee_id,
        start_date,
        sport,
        distance,
        end_date,
        comment,
    )


 # CONNEXION POSTGRESQL
 
connection = psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5433"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)


try:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                employee_id,
                sport
            FROM rh_sport
            WHERE sport IS NOT NULL
            ORDER BY employee_id;
            """
        )

        athletes = cursor.fetchall()


    print("======= GENERATION DES ACTIVITES =======")
    print(f"Salariés sportifs : {len(athletes)}")


    activities = []


    for employee_id, sport in athletes:

        if sport not in SPORT_RULES:
            raise ValueError(
                f"Sport non pris en charge : {sport}"
            )

        # Environ 30 % des salariés restent sous le seuil
        # des 15 activités annuelles.
        if random.random() < 0.30:
            activity_count = random.randint(6, 14)

        # Les autres ont une pratique plus régulière.
        else:
            activity_count = random.randint(25, 40)


        for _ in range(activity_count):

            activities.append(
                create_activity(
                    employee_id,
                    sport,
                )
            )


    # On trie chronologiquement les activités.
    activities.sort(
        key=lambda activity: activity[1]
    )


    # ========================================================
    # INSERTION
    # ========================================================

    with connection.cursor() as cursor:

        # Cette table contient uniquement notre historique
        # simulé pour le moment.
        cursor.execute(
            """
            TRUNCATE TABLE sport_activities
            RESTART IDENTITY;
            """
        )


        cursor.executemany(
            """
            INSERT INTO sport_activities (
                employee_id,
                start_date,
                sport_type,
                distance_meters,
                end_date,
                comment
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            activities,
        )


    connection.commit()


    # ========================================================
    # CONTROLES
    # ========================================================

    with connection.cursor() as cursor:

        cursor.execute(
            "SELECT COUNT(*) FROM sport_activities;"
        )

        total = cursor.fetchone()[0]


        cursor.execute(
            """
            SELECT COUNT(DISTINCT employee_id)
            FROM sport_activities;
            """
        )

        employees = cursor.fetchone()[0]


        cursor.execute(
            """
            SELECT MIN(start_date), MAX(start_date)
            FROM sport_activities;
            """
        )

        min_date, max_date = cursor.fetchone()


    print()
    print("======= GENERATION TERMINEE =======")
    print(f"Activités générées : {total}")
    print(f"Salariés concernés : {employees}")
    print(f"Première activité : {min_date}")
    print(f"Dernière activité : {max_date}")


finally:

    connection.close()
