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





