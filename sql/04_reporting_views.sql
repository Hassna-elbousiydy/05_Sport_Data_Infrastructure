CREATE OR REPLACE VIEW vw_activity_reporting AS
SELECT
    a.activity_id,
    a.employee_id,
    e.first_name,
    e.last_name,
    e.business_unit,
    a.start_date,
    a.end_date,
    a.sport_type,
    ROUND(a.distance_meters / 1000.0, 2) AS distance_km,
    ROUND(
        EXTRACT(EPOCH FROM (a.end_date - a.start_date)) / 60.0,
        2
    ) AS duration_minutes,
    a.comment,
    a.source
FROM sport_activities a
JOIN rh_employees e
    ON a.employee_id = e.employee_id;


CREATE OR REPLACE VIEW vw_kpi_summary AS
SELECT
    (SELECT COUNT(*) FROM rh_employees)
        AS total_employees,

    (SELECT COUNT(*)
     FROM rh_sport
     WHERE sport IS NOT NULL)
        AS sporting_employees,

    (SELECT COUNT(*)
     FROM vw_employee_benefits
     WHERE sport_bonus_eligible = TRUE)
        AS bonus_eligible_employees,

    (SELECT ROUND(SUM(sport_bonus_amount), 2)
     FROM vw_employee_benefits)
        AS total_bonus_cost,

    (SELECT COUNT(*)
     FROM vw_employee_benefits
     WHERE wellbeing_eligible = TRUE)
        AS wellbeing_eligible_employees,

    (SELECT SUM(wellbeing_days)
     FROM vw_employee_benefits)
        AS total_wellbeing_days,

    (SELECT COUNT(*)
     FROM sport_activities)
        AS total_activities,

    (SELECT COUNT(*)
     FROM sport_activities
     WHERE source = 'live')
        AS live_activities;
