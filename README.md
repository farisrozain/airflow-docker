# Airflow-Docker

### Requirements

```
1. Install Docker (with Docker Desktop - check WSL2 Installation)
2. Install Docker-compose
```

### Airflow + Postgres Installation

Create a docker-compose.yml file and copy configuration below.
```
version: '2.1'
services:
    postgres:
        image: postgres:9.6
        restart: always
        environment:
            - POSTGRES_USER=airflow
            - POSTGRES_PASSWORD=airflow
            - POSTGRES_DB=airflow
        ports:
            - "5432:5432"
    pgadmin4:
        image: dpage/pgadmin4
        restart: always
        environment:
            - PGADMIN_DEFAULT_EMAIL=airflow@company.com
            - PGADMIN_DEFAULT_PASSWORD=postgres
        ports:
            - "15432:80"
    webserver:
        image: puckel/docker-airflow
        restart: always
        depends_on:
            - postgres
        environment:
            - LOAD_EX=n
            - EXECUTOR=Local
            - AIRFLOW_HOME=/usr/local/airflow
        volumes:
            - ./dags:/usr/local/airflow/dags
        ports:
            - "8080:8080"
        command: webserver
        privileged: true
        healthcheck:
            test: ["CMD-SHELL", "[ -f /usr/local/airflow/airflow-webserver.pid ]"]
            interval: 30s
            timeout: 30s
            retries: 3
 ```
 
    docker-compose up -f docker-compose.yml
    
*The only reason why we are you pgadmin4 is because to look at whether the data is executed into postgresql after a data pipeline is executed*
  
### Install custom python package
  
  
  1. Create a file "requirements.txt" with the desired python modules
  2. Mount this file as a volume -v $(pwd)/requirements.txt:/requirements.txt (or add it as a volume in docker-compose file)
  3. The entrypoint.sh script execute the pip install command (with --user option)
  
  
  
### Adding datapoint/database inside webserver

1. First thing first, gotta get into bash command inside airflow webserver.

        docker exec -i -t building_server_postgres-webserver-1 /bin/bash
        
2. Make a directory.
 
        mkdir data
 
3. Make airflow connections with http://localhost:8080 :- 
    
![image](https://user-images.githubusercontent.com/61462438/152913715-7fc852b9-9888-4436-b9ad-db355e2b7bc3.png)
`file-path`
![image](https://user-images.githubusercontent.com/61462438/152913175-5fbe41f3-5c06-49e5-8020-806751ecbb09.png)
`postgresql`
![image](https://user-images.githubusercontent.com/61462438/152915253-a14163a8-7b44-4958-86b3-3c4c41f18097.png)



### Functions/Data processing with Dags.

1. Ingesting data/.csv - Transform

```
import csv
import json
import os
import pandas as pd

airflow_home = os.getenv('AIRFLOW_HOME')
data_path = airflow_home + '/data/raw_reading.csv'
transformed_path = airflow_home + '/data/transformed.csv'

def transform(*args,**kwargs):
    raw_reading = pd.read_csv(data_path)
    dataframe = {'id':[],'data':[], 'timestamp':[] ,'local_time':[]}
    
    for i in range(len(raw_reading)):
        
        id = raw_reading.iloc[i]['id']
        value = json.loads(raw_reading.iloc[i]['value'])
        dValue = value['data']
        tValue = value['time']
        lTime = raw_reading.iloc[i]['local_time']
        
        dataframe['id'].append(id)
        dataframe['data'].append(dValue)
        dataframe['timestamp'].append(tValue)
        dataframe['local_time'].append(lTime)
        
    transformed = pd.DataFrame(dataframe)
    transformed.to_csv(transformed_path, index = False)
```

2. Store in DB

```
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
```
3. Masterfile Dag.py

```
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
```
