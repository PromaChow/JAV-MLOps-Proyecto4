from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import recall_score, classification_report
from mlflow.models import infer_signature
from mlflow import MlflowClient
from datetime import datetime
import os, re
import pandas as pd
import numpy as np
import mlflow

def get_data(table_name):
    mysql_hook = MySqlHook(mysql_conn_id='clean_data', schema='clean_data-proyecto-3')
    conn = mysql_hook.get_conn()
    query = f"SELECT * FROM `{table_name}`"
    df = pd.read_sql(query, con = conn)
    if table_name == "clean_diabetes_train":
        df_positive = df[df['readmitted']==1]
        df_negative = df[df['readmitted']==0][:df_positive.shape[0]*2]
        df = pd.concat([df_positive,df_negative],ignore_index=True)
        print(df.shape)
    return df.drop('readmitted',axis=1), df['readmitted']

def train_model():
    X_train, y_train = get_data('clean_diabetes_train')
    X_val, y_val = get_data('clean_diabetes_val')
    X_test, y_test = get_data('clean_diabetes_test')

    categorical_features = X_train.select_dtypes('O').columns
    numeric_features = X_train.select_dtypes(np.number).columns

    print(categorical_features)
    print(numeric_features)

    model = RandomForestClassifier()

    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(sparse_output=False), categorical_features)]
    )

    pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])

    os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:8081"
    os.environ['AWS_ACCESS_KEY_ID'] = 'access2024minio'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'supersecretaccess2024'

    # connect to mlflow
    mlflow.set_tracking_uri("http://mlflow:8083")
    mlflow.set_experiment("mlflow_tracking_model_P3")

    mlflow.sklearn.autolog(log_model_signatures=True, log_input_examples=True, registered_model_name="diabetes_model")

    with mlflow.start_run(run_name="autolog_pipe_model_reg") as run:
        pipe.fit(X_train, y_train)
        y_pred_val = pipe.predict(X_val)
        y_pred_test = pipe.predict(X_test)
        mlflow.log_metric("recall_score_val", recall_score(y_val,y_pred_val))
        print('recall_score_val:', recall_score(y_val,y_pred_val))
        mlflow.log_metric("recall_score_test", recall_score(y_test,y_pred_test))
        print('recall_score_val:', recall_score(y_test,y_pred_test))
        print(classification_report(y_val,y_pred_val))
        signature = infer_signature(X_val, y_pred_val)
        mlflow.sklearn.log_model(
            sk_model=pipe,
            artifact_path="diabetes-model",
            signature=signature,
            registered_model_name="diabetes-random-forest-model",
        )
    print(X_test[0:3].to_dict('records'))
    """
    client = MlflowClient()
    # create "champion" alias for version 1 of model "example-model"
    client.set_registered_model_alias("diabetes-random-forest-model", "production")
    """

with DAG(
    "train_model",
    description="Fetch Diabetes data from DB, train model, save artifacts with MlFlow and register model",
    start_date=datetime(2023,5,1),
    schedule_interval="@once") as dag:

    train_model_task = PythonOperator(task_id="train_model", python_callable=train_model)

    train_model_task
