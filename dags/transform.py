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