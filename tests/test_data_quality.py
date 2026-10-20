import os

import psycopg
import pytest
from dotenv import load_dotenv


load_dotenv()


@pytest.fixture(scope="module")
def db():
    connection = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

    yield connection
    connection.close()


def scalar(db, query):
    with db.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchone()[0]


def test_employee_ids_are_unique(db):
    total = scalar(
        db,
        "SELECT COUNT(*) FROM rh_employees;"
    )

    unique_ids = scalar(
        db,
        """
        SELECT COUNT(DISTINCT employee_id)
        FROM rh_employees;
        """
    )

    assert total == unique_ids


def test_salaries_are_positive(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM rh_employees
        WHERE annual_gross_salary <= 0;
        """
    )

    assert invalid == 0


def test_commute_distances_are_not_negative(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM rh_employees
        WHERE commute_distance_km < 0;
        """
    )

    assert invalid == 0


def test_active_commutes_have_been_validated(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM rh_employees
        WHERE (
            commute_mode = 'Marche/running'
            OR commute_mode LIKE '%Trottinette%'
        )
        AND (
            commute_distance_km IS NULL
            OR commute_is_valid IS NULL
        );
        """
    )

    assert invalid == 0


def test_activity_dates_are_valid(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM sport_activities
        WHERE end_date <= start_date;
        """
    )

    assert invalid == 0


def test_activity_distances_are_not_negative(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM sport_activities
        WHERE distance_meters < 0;
        """
    )

    assert invalid == 0


def test_activity_history_contains_thousands_of_rows(db):
    total = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM sport_activities;
        """
    )

    assert total >= 2000


def test_all_activity_employees_exist(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM sport_activities a
        LEFT JOIN rh_employees e
            ON a.employee_id = e.employee_id
        WHERE e.employee_id IS NULL;
        """
    )

    assert invalid == 0


def test_wellbeing_rule_is_consistent(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM vw_employee_benefits v
        CROSS JOIN (
            SELECT parameter_value AS threshold
            FROM poc_parameters
            WHERE parameter_name =
                'wellbeing_min_activities'
        ) p
        WHERE
            (
                v.annual_activity_count >= p.threshold
                AND v.wellbeing_eligible = FALSE
            )
            OR
            (
                v.annual_activity_count < p.threshold
                AND v.wellbeing_eligible = TRUE
            );
        """
    )

    assert invalid == 0


def test_bonus_amount_matches_parameter(db):
    invalid = scalar(
        db,
        """
        SELECT COUNT(*)

        FROM vw_employee_benefits v

        CROSS JOIN (
            SELECT parameter_value AS bonus_rate
            FROM poc_parameters
            WHERE parameter_name =
                'annual_sport_bonus'
        ) p

        WHERE
            (
                v.sport_bonus_eligible = TRUE
                AND v.sport_bonus_amount
                    <> ROUND(
                        v.annual_gross_salary
                        * p.bonus_rate,
                        2
                    )
            )
            OR
            (
                v.sport_bonus_eligible = FALSE
                AND v.sport_bonus_amount <> 0
            );
        """
    )

    assert invalid == 0
