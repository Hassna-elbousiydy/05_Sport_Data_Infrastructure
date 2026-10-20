import argparse
import os
from datetime import datetime, timedelta

import psycopg
import requests
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def send_slack_message(webhook_url, message):
    response = requests.post(
        webhook_url,
        json={"text": message},
        timeout=15,
    )

    response.raise_for_status()


def build_message(
    first_name,
    last_name,
    sport_type,
    distance_meters,
    duration_minutes,
    comment,
):
    full_name = f"{first_name} {last_name}"

    if distance_meters is not None:
        distance_km = distance_meters / 1000

        message = (
            f"Bravo {full_name} ! "
            f"Tu viens de terminer une activité {sport_type} "
            f"de {distance_km:.1f} km "
            f"en {duration_minutes} min ! "
        )
    else:
        message = (
            f"Bravo {full_name} ! "
            f"Tu viens de terminer une activité {sport_type} "
            f"de {duration_minutes} min ! "
        )

    if comment:
        message += f'\n "{comment}"'

    return message


def main():
    parser = argparse.ArgumentParser(
        description="Ajouter une activité live et envoyer un message Slack."
    )

    parser.add_argument(
        "--employee-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--sport",
        required=True,
    )

    parser.add_argument(
        "--distance",
        type=float,
        default=None,
        help="Distance en mètres.",
    )

    parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Durée en minutes.",
    )

    parser.add_argument(
        "--comment",
        default=None,
    )

    args = parser.parse_args()

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError(
            "SLACK_WEBHOOK_URL absente du fichier .env"
        )

    start_date = datetime.now()
    end_date = start_date + timedelta(
        minutes=args.duration
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT first_name, last_name
                FROM rh_employees
                WHERE employee_id = %s;
                """,
                (args.employee_id,),
            )

            employee = cursor.fetchone()

            if employee is None:
                raise ValueError(
                    f"Salarié {args.employee_id} introuvable."
                )

            first_name, last_name = employee

            cursor.execute(
                """
                INSERT INTO sport_activities (
                    employee_id,
                    start_date,
                    sport_type,
                    distance_meters,
                    end_date,
                    comment,
                    source
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'live'
                )
                RETURNING activity_id;
                """,
                (
                    args.employee_id,
                    start_date,
                    args.sport,
                    args.distance,
                    end_date,
                    args.comment,
                ),
            )

            activity_id = cursor.fetchone()[0]

            message = build_message(
                first_name,
                last_name,
                args.sport,
                args.distance,
                args.duration,
                args.comment,
            )

            send_slack_message(
                webhook_url,
                message,
            )

            connection.commit()

            print("======= ACTIVITE LIVE AJOUTEE =======")
            print(f"Activity ID : {activity_id}")
            print(f"Salarié     : {first_name} {last_name}")
            print(f"Sport       : {args.sport}")
            print(f"Source      : live")
            print("Slack       : message envoyé")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
