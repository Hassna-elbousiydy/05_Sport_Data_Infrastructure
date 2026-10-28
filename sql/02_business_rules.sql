CREATE OR REPLACE VIEW vw_employee_benefits AS

WITH activity_counts AS (

    SELECT
        employee_id,
        COUNT(*) AS annual_activity_count

    FROM sport_activities

    WHERE start_date >=
        CURRENT_TIMESTAMP - INTERVAL '12 months'
    AND start_date <= CURRENT_TIMESTAMP

    GROUP BY employee_id
),

params AS (

    SELECT

        MAX(
            CASE
                WHEN parameter_name = 'annual_sport_bonus'
                THEN parameter_value
            END
        ) AS bonus_rate,

        MAX(
            CASE
                WHEN parameter_name = 'wellbeing_min_activities'
                THEN parameter_value
            END
        ) AS min_activities,

        MAX(
            CASE
                WHEN parameter_name = 'wellbeing_days'
                THEN parameter_value
            END
        ) AS wellbeing_days

    FROM poc_parameters
)

SELECT

    e.employee_id,

    e.first_name,

    e.last_name,

    e.business_unit,

    e.annual_gross_salary,

    e.commute_mode,

    e.commute_distance_km,

    e.commute_is_valid,

    s.sport,

    COALESCE(a.annual_activity_count, 0)
        AS annual_activity_count,


    -- Prime sportive
    CASE

        WHEN (e.commute_mode = 'Marche/running'
        OR e.commute_mode LIKE '%Trottinette%')
        AND e.commute_is_valid = TRUE

        THEN TRUE

        ELSE FALSE

    END AS sport_bonus_eligible,


    CASE

        WHEN (e.commute_mode = 'Marche/running'
        OR e.commute_mode LIKE '%Trottinette%')
        AND e.commute_is_valid = TRUE

        THEN ROUND(
            e.annual_gross_salary * p.bonus_rate,
            2
        )

        ELSE 0

    END AS sport_bonus_amount,


    -- Jours bien-être
    CASE

        WHEN COALESCE(
            a.annual_activity_count,
            0
        ) >= p.min_activities

        THEN TRUE

        ELSE FALSE

    END AS wellbeing_eligible,


    CASE

        WHEN COALESCE(
            a.annual_activity_count,
            0
        ) >= p.min_activities

        THEN p.wellbeing_days

        ELSE 0

    END AS wellbeing_days

FROM rh_employees e

LEFT JOIN rh_sport s
    ON e.employee_id = s.employee_id

LEFT JOIN activity_counts a
    ON e.employee_id = a.employee_id

CROSS JOIN params p;


