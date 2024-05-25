from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import mlflow
import pandas as pd

### Llamar a partir de mlflow, el URI del modelo puesto en producción. 
# set minio environment variables
os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:8081"
os.environ['AWS_ACCESS_KEY_ID'] = 'access2024minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'supersecretaccess2024'

mlflow.set_tracking_uri("http://mlflow:8083")
mlflow.set_experiment("mlflow_tracking_model_P3")

model_name = "diabetes-random-forest-model"

model_production_uri = "models:/{model_name}/production".format(model_name=model_name)

loaded_model = mlflow.pyfunc.load_model(model_uri=model_production_uri)

### Inicializar FASTAPI
app = FastAPI()
### JSON que define mis variables de entrada de la API. 
class model_input(BaseModel):
    race : str = 'Caucasian'
    gender : str = 'Male'
    age : int = 75
    admission_type_id : str = 'Emergency'
    discharge_disposition_id : str = 'Discharged to Home'
    admission_source_id : str = 'Emergency'
    time_in_hospital : int = 2
    num_lab_procedures : int = 36
    num_procedures : int = 0
    num_medications : int = 8
    number_outpatient : int = 0
    number_emergency : int = 0
    number_inpatient : int = 1
    number_diagnoses : int = 9
    max_glu_serum : str = 'None'
    A1Cresult : str = 'None'
    examide : str = 'No'
    citoglipton : str = 'No'
    change : str = 'Ch'
    diabetesMed : str = 'Yes'

# Función Predict que se encarga de ejecutar el predict sobre el modelo generado y retorna una predicción. 
# OJO: tener en cuenta hacer alguna especie de try except que muestre los errores presentes sobre la API. 
@app.post("/predict/")
def predict(item:model_input):
    try:

        global loaded_model

        data_dict = item.dict()

        X = pd.DataFrame({key: [value,] for key, value in data_dict.items()})
    
        prediction = loaded_model.predict(X)

        return {'prediction': int(prediction[0])}
    
    except:

        raise HTTPException(status_code=400, detail="Bad Request")