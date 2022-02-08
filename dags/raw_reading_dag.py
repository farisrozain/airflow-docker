import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator

from transform import transform
from store_in_db import store_in_db

default_args = {
    "owner": "airflow",
    "start_date": datetime(2022,1,1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}


with DAG(dag_id="raw_reading_dag",
         schedule_interval="@daily",
         default_args=default_args,
         template_searchpath=[f"{os.environ['AIRFLOW_HOME']}"],
         catchup=False) as dag:

    # This file could come in S3 from our ecommerce application
    is_new_data_available = FileSensor(
        task_id="is_new_data_available",
        fs_conn_id="data_path",
        filepath="raw_reading.csv",
        poke_interval=5,
        timeout=20
    )

    transform_data = PythonOperator(
        task_id="transform_data",
        python_callable=transform
    )

    create_table = PostgresOperator(
        task_id="create_table",
        sql='''CREATE TABLE IF NOT EXISTS test_readings (
                id bigint NOT NULL,
                data text NOT NULL,
                timestamp text NOT NULL,
                local_time DATE NOT NULL
                );''',
        postgres_conn_id='postgres',
        database='postgres'
    )

    save_into_db = PythonOperator(
        task_id='save_into_db',
        python_callable=store_in_db
    )


    is_new_data_available >> transform_data
    transform_data >> create_table >> save_into_db
