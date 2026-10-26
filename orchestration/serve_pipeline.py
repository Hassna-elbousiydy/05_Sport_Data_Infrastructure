from pipeline import sport_data_pipeline


if __name__ == "__main__":
    sport_data_pipeline.serve(
        name="daily-sport-data-pipeline",
        interval=86400,
        tags=["sport-data", "option-b"],
        description="Execution automatique quotidienne du pipeline Sport Data.",
    )
