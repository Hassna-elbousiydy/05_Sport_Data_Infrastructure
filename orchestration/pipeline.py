from pathlib import Path
import os
import subprocess
import sys

import psycopg
from dotenv import load_dotenv
from prefect import flow, get_run_logger, task


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")


# ============================================================
# CONNEXION POSTGRESQL
# ============================================================

def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


# ============================================================
# EXECUTION DES SCRIPTS PYTHON
# ============================================================

@task(retries=1, retry_delay_seconds=5)
def run_python_script(script_path: str):

    logger = get_run_logger()

    command = [
        sys.executable,
        str(ROOT / script_path),
    ]

    logger.info(
        "Execution : %s",
        script_path,
    )

    # Force UTF-8 dans les sous-processus Windows.
    subprocess_env = os.environ.copy()
    subprocess_env["PYTHONIOENCODING"] = "utf-8"
    subprocess_env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=subprocess_env,
    )

    if result.stdout:
        logger.info(result.stdout)

    if result.returncode != 0:

        if result.stderr:
            logger.error(result.stderr)

        raise RuntimeError(
            f"Echec du script {script_path}"
        )


# ============================================================
# REGLES METIER
# ============================================================

@task(retries=1, retry_delay_seconds=5)
def apply_business_rules():

    logger = get_run_logger()

    sql_file = (
        ROOT
        / "sql"
        / "02_business_rules.sql"
    )

    sql = sql_file.read_text(
        encoding="utf-8-sig"
    )

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(sql)

        connection.commit()

    logger.info(
        "Vue métier vw_employee_benefits mise à jour."
    )


# ============================================================
# TESTS DE QUALITE
# ============================================================

@task
def run_quality_tests():

    logger = get_run_logger()

    # Force UTF-8 également pour pytest.
    subprocess_env = os.environ.copy()
    subprocess_env["PYTHONIOENCODING"] = "utf-8"
    subprocess_env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_data_quality.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=subprocess_env,
    )

    if result.stdout:
        logger.info(result.stdout)

    if result.returncode != 0:

        if result.stderr:
            logger.error(result.stderr)

        raise RuntimeError(
            "Les tests de qualité ont échoué."
        )

    logger.info(
        "Tous les tests de qualité sont valides."
    )


# ============================================================
# MONITORING DES VOLUMES
# ============================================================

@task
def monitor_volumes():

    logger = get_run_logger()

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM rh_employees;
                """
            )

            employees = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM sport_activities;
                """
            )

            activities = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM vw_employee_benefits
                WHERE sport_bonus_eligible = TRUE;
                """
            )

            bonus_eligible = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM vw_employee_benefits
                WHERE wellbeing_eligible = TRUE;
                """
            )

            wellbeing_eligible = (
                cursor.fetchone()[0]
            )

    logger.info(
        "Volumétrie : %s salariés",
        employees,
    )

    logger.info(
        "Volumétrie : %s activités",
        activities,
    )

    logger.info(
        "Prime sportive : %s salariés éligibles",
        bonus_eligible,
    )

    logger.info(
        "Jours bien-être : %s salariés éligibles",
        wellbeing_eligible,
    )

    return {
        "employees": employees,
        "activities": activities,
        "bonus_eligible": bonus_eligible,
        "wellbeing_eligible": wellbeing_eligible,
    }


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

@flow(
    name="sport-data-pipeline",
    log_prints=True,
)
def sport_data_pipeline():

    print(
        "======= SPORT DATA PIPELINE ======="
    )

    # 1. Audit des sources
    run_python_script(
        "src/audit_data.py"
    )

    # 2. Nettoyage
    run_python_script(
        "src/clean_data.py"
    )

    # 3. Chargement PostgreSQL
    run_python_script(
        "src/load_data.py"
    )

    # 4. Validation des trajets
    run_python_script(
        "src/validate_commutes.py"
    )

    # 5. Simulation des activités
    run_python_script(
        "src/generate_activities.py"
    )

    # 6. Calcul des avantages
    apply_business_rules()

    # 7. Contrôles qualité
    run_quality_tests()

    # 8. Monitoring
    metrics = monitor_volumes()

    print(
        "======= PIPELINE TERMINE ======="
    )

    return metrics


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    sport_data_pipeline()