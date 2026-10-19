import os
import time

import psycopg
import requests
from dotenv import load_dotenv


 # CONFIGURATION

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

COMPANY_ADDRESS = "1362 Av. des Platanes, 34970 Lattes, France"

ROUTES_URL = (
    "https://routes.googleapis.com/"
    "directions/v2:computeRoutes"
)

# Sécurité supplémentaire pour éviter une boucle accidentelle.
MAX_API_CALLS = 100


if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError(
        "GOOGLE_MAPS_API_KEY absente du fichier .env"
    )


 # CONNEXION POSTGRESQL
 
connection = psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5433"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)


 # APPEL GOOGLE ROUTES API
 
def get_distance_meters(origin, travel_mode):

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.distanceMeters",
    }

    payload = {
        "origin": {
            "address": origin
        },
        "destination": {
            "address": COMPANY_ADDRESS
        },
        "travelMode": travel_mode,
    }

    response = requests.post(
        ROUTES_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    routes = data.get("routes", [])

    if not routes:
        return None

    return routes[0]["distanceMeters"]


 # RECUPERATION DES SALARIES CONCERNES
 
try:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                employee_id,
                first_name,
                last_name,
                home_address,
                commute_mode
            FROM rh_employees
            WHERE commute_mode IN (
                'Marche/running',
                'Vélo/Trottinette/Autres'
            )
            AND commute_distance_km IS NULL
            ORDER BY employee_id;
            """
        )

        employees = cursor.fetchall()


    print("======= VALIDATION DES TRAJETS =======")
    print(f"Salariés à vérifier : {len(employees)}")
    print()


    api_calls = 0
    validated = 0
    invalid = 0
    errors = 0


    for employee in employees:

        if api_calls >= MAX_API_CALLS:
            print(
                "STOP : limite de sécurité "
                f"de {MAX_API_CALLS} appels atteinte."
            )
            break


        (
            employee_id,
            first_name,
            last_name,
            home_address,
            commute_mode,
        ) = employee


        if commute_mode == "Marche/running":
            travel_mode = "WALK"
            max_distance_km = 15

        elif commute_mode == "Vélo/Trottinette/Autres":
            travel_mode = "BICYCLE"
            max_distance_km = 25

        else:
            continue


        try:

            distance_meters = get_distance_meters(
                home_address,
                travel_mode,
            )

            api_calls += 1


            if distance_meters is None:

                print(
                    f"[ERREUR] {employee_id} - "
                    f"{first_name} {last_name} : "
                    "aucun itinéraire trouvé"
                )

                errors += 1
                continue


            distance_km = distance_meters / 1000

            commute_is_valid = (
                distance_km <= max_distance_km
            )


            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE rh_employees
                    SET
                        commute_distance_km = %s,
                        commute_is_valid = %s
                    WHERE employee_id = %s;
                    """,
                    (
                        round(distance_km, 2),
                        commute_is_valid,
                        employee_id,
                    ),
                )


            connection.commit()


            if commute_is_valid:
                validated += 1
                status = "OK"
            else:
                invalid += 1
                status = "A VERIFIER"


            print(
                f"[{status}] "
                f"{employee_id} - "
                f"{first_name} {last_name} - "
                f"{commute_mode} - "
                f"{distance_km:.2f} km "
                f"(max {max_distance_km} km)"
            )


            # Petit délai volontaire entre deux appels.
            time.sleep(0.2)


        except requests.RequestException as error:

            api_calls += 1
            errors += 1

            print(
                f"[ERREUR API] "
                f"{employee_id} - "
                f"{first_name} {last_name} : "
                f"{error}"
            )


    print()
    print("======= VALIDATION TERMINEE =======")
    print(f"Appels API effectués : {api_calls}")
    print(f"Déclarations valides : {validated}")
    print(f"Déclarations à vérifier : {invalid}")
    print(f"Erreurs API : {errors}")


finally:

    connection.close()
