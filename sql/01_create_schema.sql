CREATE TABLE IF NOT EXISTS rh_employees (
    employee_id INTEGER PRIMARY KEY,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    birth_date DATE NOT NULL,
    business_unit TEXT NOT NULL,
    hire_date DATE NOT NULL,
    annual_gross_salary NUMERIC(12,2) NOT NULL,
    contract_type TEXT NOT NULL,
    paid_leave_days NUMERIC(6,2) NOT NULL,
    home_address TEXT NOT NULL,
    commute_mode TEXT NOT NULL,
    commute_distance_km NUMERIC(8,2),
    commute_is_valid BOOLEAN
);

CREATE TABLE IF NOT EXISTS rh_sport (
    employee_id INTEGER PRIMARY KEY,
    sport TEXT,
    CONSTRAINT fk_rh_sport_employee
        FOREIGN KEY (employee_id)
        REFERENCES rh_employees(employee_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sport_activities (
    activity_id BIGSERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL,
    sport_type TEXT NOT NULL,
    distance_meters NUMERIC(12,2),
    end_date TIMESTAMP NOT NULL,
    comment TEXT,
    source TEXT NOT NULL DEFAULT 'simulated',
    CONSTRAINT fk_sport_activity_employee
        FOREIGN KEY (employee_id)
        REFERENCES rh_employees(employee_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS poc_parameters (
    parameter_name TEXT PRIMARY KEY,
    parameter_value NUMERIC(12,4) NOT NULL,
    description TEXT
);

INSERT INTO poc_parameters
    (parameter_name, parameter_value, description)
VALUES
    ('annual_sport_bonus', 0.05, 'Taux de la prime sportive'),
    ('wellbeing_min_activities', 15, 'Nombre minimum d activites annuelles'),
    ('wellbeing_days', 5, 'Nombre de jours bien-etre accordes'),
    ('walking_running_max_km', 15, 'Distance maximum Marche/Running'),
    ('bike_other_max_km', 25, 'Distance maximum Velo/Trottinette/Autres')
ON CONFLICT (parameter_name) DO NOTHING;

