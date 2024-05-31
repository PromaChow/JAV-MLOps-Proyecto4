from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from mlflow.models import infer_signature
from mlflow import MlflowClient
from datetime import datetime
import os
import pandas as pd
import numpy as np
import mlflow
import shap

def get_data(table_name):
    mysql_hook = MySqlHook(mysql_conn_id='clean_data', schema='clean_data-proyecto-4')
    conn = mysql_hook.get_conn()
    query = f"SELECT * FROM `{table_name}`"
    df = pd.read_sql(query, con = conn)
    return df.drop('price', axis=1), df['price']

def train_model():
    X_train, y_train = get_data('clean_realtor_train')
    X_val, y_val = get_data('clean_realtor_val')
    X_test, y_test = get_data('clean_realtor_test')

    categorical_features = X_train.select_dtypes('O').columns
    numeric_features = X_train.select_dtypes(np.number).columns

    print(categorical_features)
    print(numeric_features)

    model = RandomForestRegressor()

    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(sparse_output=False), categorical_features)]
    )

    pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])

    os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:8081"
    os.environ['AWS_ACCESS_KEY_ID'] = 'access2024minio'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'supersecretaccess2024'

    # connect to mlflow
    mlflow.set_tracking_uri("http://mlflow:8083")
    mlflow.set_experiment("mlflow_tracking_model_P4")

    mlflow.sklearn.autolog(log_model_signatures=True, log_input_examples=True, registered_model_name="realtor_model")

    with mlflow.start_run(run_name="autolog_pipe_model_reg") as run:
        pipe.fit(X_train, y_train)
        y_pred_val = pipe.predict(X_val)
        y_pred_test = pipe.predict(X_test)

        summary = shap.kmeans(X_train, 50)
        explainer = shap.KernelExplainer(pipe.predict, summary)
        shap_values = explainer.shap_values(X_val).mean(0).tolist()

        # Update model if any SHAP value changes more than 20%
        retrain = False
        try:
            client = MlflowClient()
            model_name = "realtor-random-forest-model"
            model_version_details = client.get_model_version(name=model_name, stages=["Production"])
            run_id = model_version_details.run_id
            for idx, new_value in enumerate(shap_values):
                metric_data = client.get_metric_history(run_id=run_id, key=f"shap_{idx}")
                old_value = metric_data[0].value
                if abs(new_value - old_value) > old_value*0.2:
                    retrain = True
                    break
        # Exception catches case where model does not exist yet
        except:
            print("The previous model could not be loaded. The model will be retrained (or trained for the first time).")
            retrain = True
        if not retrain:
            return

        for idx, value in enumerate(shap_values):
            mlflow.log_metric(f"shap_{idx}", value)
        mlflow.log_metric("mae_val", mean_absolute_error(y_val, y_pred_val))
        print('mae_val:', mean_absolute_error(y_val, y_pred_val))
        mlflow.log_metric("mae_test", mean_absolute_error(y_test, y_pred_test))
        print('mae_test:', mean_absolute_error(y_test, y_pred_test))

        signature = infer_signature(X_val, y_pred_val)
        mlflow.sklearn.log_model(
            sk_model=pipe,
            artifact_path="realtor-model",
            signature=signature,
            registered_model_name="realtor-random-forest-model",
        )
    print(X_test[0:3].to_dict('records'))
    """
    client = MlflowClient()
    # create "champion" alias for version 1 of model "example-model"
    client.set_registered_model_alias("realtor-random-forest-model", "production")
    """

with DAG(
    "train_model",
    description="Fetch realtor data from DB, train model, save artifacts with MlFlow and register model",
    start_date=datetime(2024, 5, 31),
    schedule_interval="@once") as dag:

    train_model_task = PythonOperator(task_id="train_model", python_callable=train_model)

    train_model_task
