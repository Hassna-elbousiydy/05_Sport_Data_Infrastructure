from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def main():
    print("=== Modification du taux de prime ===")

    value = input(
        "Nouveau taux de prime en % : "
    ).strip().replace(",", ".")

    try:
        percentage = float(value)
    except ValueError:
        print("ERREUR : entre un nombre, par exemple 5 ou 8.")
        return

    if percentage < 0 or percentage > 100:
        print("ERREUR : le taux doit etre compris entre 0 et 100.")
        return

    new_rate = percentage / 100

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT parameter_value
                FROM poc_parameters
                WHERE parameter_name = 'annual_sport_bonus';
                """
            )

            old_rate = cursor.fetchone()[0]

            cursor.execute(
                """
                UPDATE poc_parameters
                SET parameter_value = %s
                WHERE parameter_name = 'annual_sport_bonus';
                """,
                (new_rate,),
            )

        connection.commit()

    print()
    print(f"Ancien taux : {float(old_rate) * 100:.2f} %")
    print(f"Nouveau taux : {percentage:.2f} %")
    print("Parametre mis a jour avec succes.")
    print("Actualise maintenant Power BI.")


if __name__ == "__main__":
    main()
