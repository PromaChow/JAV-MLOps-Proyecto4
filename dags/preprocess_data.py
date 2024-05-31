from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from datetime import datetime
from sklearn.model_selection import train_test_split
import pandas as pd

def check_table_exists(table_name):
    query = f'select count(*) from information_schema.tables where table_name="{table_name}"'
    mysql_hook = MySqlHook(mysql_conn_id='clean_data', schema='clean_data-proyecto-4')
    connection = mysql_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    if results[0][0] == 0:
        print("----- table does not exists, creating it")    
        create_sql = f"CREATE TABLE `{table_name}` (`brokered_by` VARCHAR(50), `status` VARCHAR(50), `price` BIGINT, `bed` INT, `bath` INT, `acre_lot` BIGINT, `street` VARCHAR(50), `city` VARCHAR(50), `state` VARCHAR(50), `house_size` BIGINT)"
        mysql_hook.run(create_sql)
    else:
        print("----- table already exists")
        create_sql = f"""truncate table `{table_name}`"""
        mysql_hook.run(create_sql)

def store_data(df, table_name):
    table_status = check_table_exists(table_name)
    mysql_hook = MySqlHook(mysql_conn_id='clean_data', schema='clean_data-proyecto-4')
    conn = mysql_hook.get_conn()
    cur = conn.cursor()
    query = f"INSERT INTO `{table_name}` ({', '.join(['`'+i+'`' for i in df.columns])}) VALUES ({', '.join(['%s' for i in range(df.shape[1])])})"
    
    df = list(df.itertuples(index=False, name=None))
    cur.executemany(query, df)
    conn.commit()

def preprocess_data():
    mysql_hook = MySqlHook(mysql_conn_id='raw_data', schema='raw_data-proyecto-4')
    conn = mysql_hook.get_conn()
    query = f"SELECT * FROM `raw_realtor`"
    df = pd.read_sql(query, con = conn)
    df.drop(columns=["zip_code", "prev_sold_date"], inplace=True)
    print(df.info())

    df_train, df_rest = train_test_split(df, test_size=0.2, random_state=42)
    df_val, df_test = train_test_split(df_rest, test_size=0.25, random_state=42)

    print("df_train shape:", df_train.shape)
    print("df_val shape:", df_val.shape)
    print("df_test shape:", df_test.shape)

    store_data(df_train, 'clean_realtor_train')
    store_data(df_val, 'clean_realtor_val')
    store_data(df_test, 'clean_realtor_test')

with DAG(
    "preprocess_data",
    description="Fetch realtor data from DB, preprocess data and save in mysql data_clean DB",
    start_date=datetime(2024, 5, 31),
    schedule_interval="@once") as dag:

    preprocess_data = PythonOperator(task_id="preprocess_data", python_callable=preprocess_data)

    preprocess_data