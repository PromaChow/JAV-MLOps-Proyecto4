from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from datetime import datetime
from sklearn.model_selection import train_test_split
import os, math
import pandas as pd
import numpy as np

def check_table_exists(table_name):
    query = f'select count(*) from information_schema.tables where table_name="{table_name}"'
    mysql_hook = MySqlHook(mysql_conn_id='clean_data', schema='clean_data-proyecto-3')
    connection = mysql_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    if results[0][0] == 0:
        print("----- table does not exists, creating it")    
        create_sql = f"""create table `{table_name}` (`race` VARCHAR(50), `gender` VARCHAR(50), `age` INT, `admission_type_id` VARCHAR(50), `discharge_disposition_id` VARCHAR(50), 
`admission_source_id` VARCHAR(50), `time_in_hospital` INT, `num_lab_procedures` INT, `num_procedures` INT, `num_medications` INT, 
`number_outpatient` INT, `number_emergency` INT, `number_inpatient` INT, `number_diagnoses` INT, `max_glu_serum` VARCHAR(50), 
`A1Cresult` VARCHAR(50), `examide` VARCHAR(50), `citoglipton` VARCHAR(50), `change` VARCHAR(50), `diabetesMed` VARCHAR(50), `readmitted` INT)"""
        mysql_hook.run(create_sql)
    else:
        print("----- table already exists")
        create_sql = f"""truncate table `{table_name}`"""
        mysql_hook.run(create_sql)

def store_data(df, table_name):
    table_status = check_table_exists(table_name)
    mysql_hook = MySqlHook(mysql_conn_id='clean_data', schema='clean_data-proyecto-3')
    conn = mysql_hook.get_conn()
    cur = conn.cursor()
    query = f"INSERT INTO `{table_name}` ({', '.join(['`'+i+'`' for i in df.columns])}) VALUES ({', '.join(['%s' for i in range(df.shape[1])])})"
    
    chunks = int(math.ceil(df.shape[0]/15000))
    for i in range(chunks):
        if i==chunks-1:
            data = list(df[15000*i:].itertuples(index=False, name=None))
        else:
            data = list(df[15000*i:15000*(i+1)].itertuples(index=False, name=None))
        cur.executemany(query,data)
        conn.commit()
        print(cur.rowcount, "was inserted, chunk", i, "into", table_name)
    
def preprocess_data():
    mysql_hook = MySqlHook(mysql_conn_id='raw_data', schema='raw_data-proyecto-3')
    conn = mysql_hook.get_conn()
    query = f"SELECT * FROM `raw_diabetes`"
    df = pd.read_sql(query, con = conn)
    df = df.replace("?",np.nan)
    df.drop(['weight','payer_code','medical_specialty','diag_1', 'diag_2', 'diag_3', 'metformin','repaglinide', 'nateglinide', 'chlorpropamide', 'glimepiride','acetohexamide', 'glipizide',
                    'glyburide', 'tolbutamide','pioglitazone', 'rosiglitazone', 'acarbose', 'miglitol', 'troglitazone',
                    'tolazamide', 'glyburide-metformin', 'glipizide-metformin','glimepiride-pioglitazone',
                    'metformin-rosiglitazone','metformin-pioglitazone', 'insulin'],axis=1,inplace=True)
    df = df.replace({"NO":0,
                        "<30":1,
                        ">30":0})
    df = df.drop(df.loc[df["gender"]=="Unknown/Invalid"].index, axis=0)
    df.age = df.age.replace({"[70-80)":75,
                            "[60-70)":65,
                            "[50-60)":55,
                            "[80-90)":85,
                            "[40-50)":45,
                            "[30-40)":35,
                            "[90-100)":95,
                            "[20-30)":25,
                            "[10-20)":15,
                            "[0-10)":5})
    mapped = {1.0:"Emergency",
            2.0:"Emergency",
            3.0:"Elective",
            4.0:"New Born",
            5.0:np.nan,
            6.0:np.nan,
            7.0:"Trauma Center",
            8.0:np.nan}
    df.admission_type_id = df.admission_type_id.replace(mapped)
    mapped_discharge = {1:"Discharged to Home",
                        6:"Discharged to Home",
                        8:"Discharged to Home",
                        13:"Discharged to Home",
                        19:"Discharged to Home",
                        18:np.nan,25:np.nan,26:np.nan,
                        2:"Other",3:"Other",4:"Other",
                        5:"Other",7:"Other",9:"Other",
                        10:"Other",11:"Other",12:"Other",
                        14:"Other",15:"Other",16:"Other",
                        17:"Other",20:"Other",21:"Other",
                        22:"Other",23:"Other",24:"Other",
                        27:"Other",28:"Other",29:"Other",30:"Other"}
    df["discharge_disposition_id"] = df["discharge_disposition_id"].replace(mapped_discharge)
    mapped_adm = {1:"Referral",2:"Referral",3:"Referral",
                4:"Other",5:"Other",6:"Other",10:"Other",22:"Other",25:"Other",
                9:"Other",8:"Other",14:"Other",13:"Other",11:"Other",
                15:np.nan,17:np.nan,20:np.nan,21:np.nan,
                7:"Emergency"}
    df.admission_source_id = df.admission_source_id.replace(mapped_adm)
    df['race'] = df['race'].fillna(df['race'].mode()[0])
    df['admission_type_id'] = df['admission_type_id'].fillna(df['admission_type_id'].mode()[0])
    df['discharge_disposition_id'] = df['discharge_disposition_id'].fillna(df['discharge_disposition_id'].mode()[0])
    df['admission_source_id'] = df['admission_source_id'].fillna(df['admission_source_id'].mode()[0])
    df.drop(['encounter_id','patient_nbr'],axis=1,inplace=True)

    print(df.info())

    df_train, df_rest = train_test_split(df, test_size=0.2, random_state=42)
    df_val, df_test = train_test_split(df_rest, test_size=0.25, random_state=42)

    print("df_train shape:", df_train.shape)
    print("df_val shape:", df_val.shape)
    print("df_test shape:", df_test.shape)

    store_data(df_train, 'clean_diabetes_train')
    store_data(df_val, 'clean_diabetes_val')
    store_data(df_test, 'clean_diabetes_test')

with DAG(
    "preprocess_data",
    description="Fetch Diabetes data from DB, preprocess data and save in mysql data_clean DB",
    start_date=datetime(2023,5,1),
    schedule_interval="@once") as dag:

    preprocess_data = PythonOperator(task_id="preprocess_data", python_callable=preprocess_data)

    preprocess_data