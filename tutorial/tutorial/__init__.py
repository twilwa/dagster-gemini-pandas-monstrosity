from dagster import Definitions, load_assets_from_modules, AssetSelection, define_asset_job, ScheduleDefinition, EnvVar
from .resources import DataGeneratorResource
from . import assets

all_assets = load_assets_from_modules([assets])

#Addition: define a job that will materialize the assets
reddit_job = define_asset_job("reddit_job", selection=AssetSelection.all())

#Addition: a ScheduleDefinition the job it should run and a cron schedule of how frequently to run it
reddit_schedule = ScheduleDefinition(
    job=reddit_job,
    cron_schedule="0 * * * *",
    )

datagen = DataGeneratorResource(num_days=EnvVar.int("REDDIT_NUM_DAYS_WINDOW"),
                                )


defs = Definitions(
    assets=all_assets,
    schedules = [reddit_schedule],
    resources = {
        "reddit_api": datagen
        }
)    


