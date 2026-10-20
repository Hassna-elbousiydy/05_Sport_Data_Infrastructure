# Data Quality Tests

## Objective

The data quality layer validates the integrity and business consistency
of the Sport Data Solution POC before data is exposed to Slack or Power BI.

## Tool

Tests are implemented with pytest and PostgreSQL assertions.

This lightweight approach was selected because the POC contains a limited
number of controlled PostgreSQL tables and the tests can later be executed
automatically by the orchestration pipeline.

## Tests

### Employee identifiers

Employee identifiers in `rh_employees` must be unique.

### Salary

Annual gross salaries must be strictly positive.

### Commute distances

Calculated commute distances cannot be negative.

Every employee declaring an active commute must have a calculated distance
and a validation result.

### Activity dates

The activity end date must always be later than the activity start date.

### Activity distance

When a distance is available, it cannot be negative.

A null distance is accepted for sports where distance is not relevant,
such as climbing.

### Activity volume

The simulated twelve-month history must contain at least 2,000 activities.

### Referential integrity

Every activity must be associated with an existing employee.

### Wellbeing eligibility

The value of `wellbeing_eligible` must correspond to the configurable
minimum annual activity threshold stored in `poc_parameters`.

### Sport bonus

The sport bonus amount must correspond to the configured bonus percentage
of the employee annual gross salary.

Employees who are not eligible must receive a bonus amount of zero.

## Execution

Run:

pytest -v tests/test_data_quality.py
