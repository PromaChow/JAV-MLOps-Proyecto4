from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from datetime import datetime, timedelta
import os
import csv
import pandas as pd
import requests

def fetch_data():
    ## download the dataset
    # Directory of the raw data files
    _data_root = './data/Realtor'
    os.makedirs(_data_root, exist_ok=True)
    # Path to the raw training data
    _data_filepath = os.path.join(_data_root, 'Realtor.csv')
    # Download data
    api_url = "http://10.43.101.149:80/data?group_number=5"
    response = requests.get(api_url)
    data = response.json()["data"]

    with open(_data_filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)


def check_table_exists():
    query = 'select count(*) from information_schema.tables where table_name="raw_realtor"'
    mysql_hook = MySqlHook(mysql_conn_id='raw_data', schema='raw_data-proyecto-4')
    connection = mysql_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    if results[0][0] == 0:
        print("----- table does not exists, creating it")
        create_sql = "CREATE TABLE `raw_realtor` (`brokered_by` VARCHAR(50), `status` VARCHAR(50), `price` BIGINT, `bed` INT, `bath` INT, `acre_lot` BIGINT, `street` VARCHAR(50), `city` VARCHAR(50), `state` VARCHAR(50), `zip_code` VARCHAR(10), `house_size` BIGINT, `prev_sold_date` VARCHAR(20))"
        mysql_hook.run(create_sql)
    else:
        print("----- table already exists")
        create_sql = """truncate table `raw_realtor`"""
        mysql_hook.run(create_sql)
    return "ok"

def store_data():
    _data_root = './data/Realtor'
    # Path to the raw training data
    _data_filepath = os.path.join(_data_root, 'Realtor.csv')

    df = pd.read_csv(_data_filepath)

    table_status = check_table_exists()
    mysql_hook = MySqlHook(mysql_conn_id='raw_data', schema='raw_data-proyecto-4')
    conn = mysql_hook.get_conn()
    cur = conn.cursor()
    query = f"INSERT INTO `raw_realtor` ({', '.join(['`'+i+'`' for i in df.columns])}) VALUES ({', '.join(['%s' for i in range(df.shape[1])])})"
    df = list(df.itertuples(index=False, name=None))
    cur.executemany(query, df)
    conn.commit()

    return 'raw_realtor'

with DAG(
    "load_data",
    description="Fetch realtor data from the API and save in mysql data_raw db",
    start_date=datetime(2024, 5, 31),
    end_date=datetime(2024, 5, 31, 1),
    schedule_interval=timedelta(minutes=1),
) as dag:

    get_data_task = PythonOperator(task_id="fetch_data", python_callable=fetch_data)

    store_data_task = PythonOperator(task_id="store_data", python_callable=store_data)

    get_data_task >> store_data_task