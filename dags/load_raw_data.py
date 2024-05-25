from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from datetime import datetime
import os
import logging
import pandas as pd
import requests
import math

def fetch_data():
    ## download the dataset
    # Directory of the raw data files
    _data_root = './data/Diabetes'
    # Path to the raw training data
    _data_filepath = os.path.join(_data_root, 'Diabetes.csv')
    # Download data
    os.makedirs(_data_root, exist_ok=True)
    if not os.path.isfile(_data_filepath):
        #https://archive.ics.uci.edu/ml/machine-learning-databases/covtype/
        url = 'https://docs.google.com/uc?export= \
        download&confirm={{VALUE}}&id=1k5-1caezQ3zWJbKaiMULTGq-3sz6uThC'
        r = requests.get(url, allow_redirects=True, stream=True)
        open(_data_filepath, 'wb').write(r.content)

def check_table_exists():
    query = 'select count(*) from information_schema.tables where table_name="raw_diabetes"'
    mysql_hook = MySqlHook(mysql_conn_id='raw_data', schema='raw_data-proyecto-3')
    connection = mysql_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    if results[0][0] == 0:
        print("----- table does not exists, creating it")    
        create_sql = """create table `raw_diabetes` (`encounter_id` BIGINT, `patient_nbr` BIGINT, `race` VARCHAR(50), `gender` VARCHAR(50), `age` VARCHAR(50), `weight` VARCHAR(50), `admission_type_id` BIGINT, 
`discharge_disposition_id` BIGINT, `admission_source_id` BIGINT, `time_in_hospital` BIGINT, `payer_code` VARCHAR(50), `medical_specialty` VARCHAR(50), 
`num_lab_procedures` BIGINT,  `num_procedures` BIGINT, `num_medications` BIGINT, `number_outpatient` BIGINT, `number_emergency` BIGINT, `number_inpatient` BIGINT, 
`diag_1` VARCHAR(50), `diag_2` VARCHAR(50), `diag_3` VARCHAR(50), `number_diagnoses` BIGINT, `max_glu_serum` VARCHAR(50), `A1Cresult` VARCHAR(50), 
`metformin` VARCHAR(50), `repaglinide` VARCHAR(50), `nateglinide` VARCHAR(50), `chlorpropamide` VARCHAR(50), `glimepiride` VARCHAR(50), `acetohexamide` VARCHAR(50), 
`glipizide` VARCHAR(50), `glyburide` VARCHAR(50), `tolbutamide` VARCHAR(50), `pioglitazone` VARCHAR(50), `rosiglitazone` VARCHAR(50), `acarbose` VARCHAR(50), 
`miglitol` VARCHAR(50), `troglitazone` VARCHAR(50), `tolazamide` VARCHAR(50), `examide` VARCHAR(50), `citoglipton` VARCHAR(50), `insulin` VARCHAR(50), 
`glyburide-metformin` VARCHAR(50), `glipizide-metformin` VARCHAR(50), `glimepiride-pioglitazone` VARCHAR(50), `metformin-rosiglitazone` VARCHAR(50), 
`metformin-pioglitazone` VARCHAR(50), `change` VARCHAR(50), `diabetesMed` VARCHAR(50), `readmitted` VARCHAR(50))"""
        mysql_hook.run(create_sql)
    else:
        print("----- table already exists")
        create_sql = """truncate table `raw_diabetes`"""
        mysql_hook.run(create_sql)
    return "ok"

def store_data():
    _data_root = './data/Diabetes'
    # Path to the raw training data
    _data_filepath = os.path.join(_data_root, 'Diabetes.csv')

    df = pd.read_csv(_data_filepath)

    table_status = check_table_exists()
    mysql_hook = MySqlHook(mysql_conn_id='raw_data', schema='raw_data-proyecto-3')
    conn = mysql_hook.get_conn()
    cur = conn.cursor()
    query = f"INSERT INTO `raw_diabetes` ({', '.join(['`'+i+'`' for i in df.columns])}) VALUES ({', '.join(['%s' for i in range(df.shape[1])])})"
    
    chunks = int(math.ceil(df.shape[0]/15000))
    for i in range(chunks):
        if i==chunks-1:
            data = list(df[15000*i:].itertuples(index=False, name=None))
        else:
            data = list(df[15000*i:15000*(i+1)].itertuples(index=False, name=None))
        cur.executemany(query,data)
        conn.commit()
        print(cur.rowcount, "was inserted in chunk", i)
    
    return 'raw_diabetes'

with DAG(
    "load_data",
    description="Fetch Diabetes data from the URI and save in mysql data_raw db",
    start_date=datetime(2023,5,1),
    schedule_interval="@once") as dag:

    get_data_task = PythonOperator(task_id="fetch_data", python_callable=fetch_data)

    store_data_task = PythonOperator(task_id="store_data", python_callable=store_data)

    get_data_task >> store_data_task