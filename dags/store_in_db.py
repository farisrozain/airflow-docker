from sqlalchemy import create_engine
import pandas as pd
import os

airflow_home = os.getenv('AIRFLOW_HOME')
transformed_path = airflow_home + '/data/transformed.csv'

def store_in_db(*args, **kwargs):
    transformed_readings = pd.read_csv(transformed_path)

    engine = create_engine(
        'postgresql://airflow:airflow@postgres/postgres')

    transformed_readings.to_sql("test_readings",
                                engine,
                                if_exists='append',
                                chunksize=500,
                                index=False
                                )