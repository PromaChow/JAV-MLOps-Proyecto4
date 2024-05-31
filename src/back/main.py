from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import mlflow
import pandas as pd
import mysql.connector

def check_table_exists(table_name):
    query = f'select count(*) from information_schema.tables where table_name="{table_name}"'
    connection = mysql.connector.connect(url="http://db_raw:8088", user="estudiante", password="supersecretaccess2024", database="raw_data-proyecto-4")
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    if results[0][0] == 0:
        print("----- table does not exists, creating it")
        create_sql = f"CREATE TABLE `{table_name}` (`brokered_by` VARCHAR(50), `status` VARCHAR(50), `bed` INT, `bath` INT, `acre_lot` BIGINT, `street` VARCHAR(50), `city` VARCHAR(50), `state` VARCHAR(50), `house_size` BIGINT, `price` BIGINT)"
        cursor.execute(create_sql)
    else:
        print("----- table already exists")
        create_sql = f"""truncate table `{table_name}`"""
        cursor.execute(create_sql)
    cursor.close()
    connection.close()

def store_data(df, table_name):
    table_status = check_table_exists(table_name)
    conn = mysql.connector.connect(url="http://db_raw:8088", user="estudiante", password="supersecretaccess2024", database="raw_data-proyecto-4")
    cur = conn.cursor()
    query = f"INSERT INTO `{table_name}` ({', '.join(['`'+i+'`' for i in df.columns])}) VALUES ({', '.join(['%s' for i in range(df.shape[1])])})"
    
    df = list(df.itertuples(index=False, name=None))
    cur.executemany(query, df)
    conn.commit()

    cur.close()
    conn.close()

### Llamar a partir de mlflow, el URI del modelo puesto en producción. 
# set minio environment variables
os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:8081"
os.environ['AWS_ACCESS_KEY_ID'] = 'access2024minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'supersecretaccess2024'

mlflow.set_tracking_uri("http://mlflow:8083")
mlflow.set_experiment("mlflow_tracking_model_P4")

model_name = "realtor-random-forest-model"

model_production_uri = "models:/{model_name}/production".format(model_name=model_name)

loaded_model = mlflow.pyfunc.load_model(model_uri=model_production_uri)

### Inicializar FASTAPI
app = FastAPI()
### JSON que define mis variables de entrada de la API. 
class model_input(BaseModel):
    brokered_by : str = 'Example'
    status: str = "Sale"
    bed: int = 1
    bath: int = 1
    acre_lot: int = 1
    street: str = "Street"
    city: str = "City"
    state: str = "State"
    house_size: int = 1

# Función Predict que se encarga de ejecutar el predict sobre el modelo generado, retorna una predicción, y almacena resultados en base de datos.
@app.post("/predict/")
def predict(item:model_input):
    try:

        global loaded_model

        data_dict = item.dict()

        X = pd.DataFrame({key: [value,] for key, value in data_dict.items()})
    
        prediction = loaded_model.predict(X)

        X["price"] = prediction
        store_data(X, "predictions")

        return {'prediction': int(prediction[0])}
    
    except:

        raise HTTPException(status_code=400, detail="Bad Request")