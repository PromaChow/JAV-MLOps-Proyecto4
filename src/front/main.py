import streamlit as st
import pandas as pd
import numpy as np
import requests
import json

st.title("Operaciones de Machine Learning")
st.write("Proyecto 3 - Nivel 3")
st.write("Orquestación, metricas y modelos")
st.write("Por Juan Pablo Nieto, Nicolas Rojas y Brayan Carvajal")

# Colección de variables.  
st.write("### Registrar Dato")
col1, col2, col3, col4 = st.columns(4)

race = col1.text_input('race', value='Caucasian')
gender = col2.text_input("gender", value='Male')
age = col3.number_input("age", value=75)
admission_type_id = col4.text_input("admission_type_id", value='Emergency')

discharge_disposition_id = col1.text_input('discharge_disposition_id', value='Discharged to Home')
admission_source_id = col2.text_input("admission_source_id", value='Emergency')
time_in_hospital = col3.number_input("time_in_hospital", value=2)
num_lab_procedures = col4.number_input("num_lab_procedures", value=36)

num_procedures = col1.number_input('num_procedures', value=0)
num_medications = col2.number_input("num_medications", value=8)
number_outpatient = col3.number_input("number_outpatient", value=0)
number_emergency = col4.number_input("number_emergency", value=0)

number_inpatient = col1.number_input('number_inpatient', value=1)
number_diagnoses = col2.number_input("number_diagnoses", value=9)
max_glu_serum = col3.text_input("max_glu_serum", value='None')
A1Cresult = col4.text_input("A1Cresult", value='None')

examide = col1.text_input('examide', value='No')
citoglipton = col2.text_input("citoglipton", value='No')
change = col3.text_input("change", value='Ch')
diabetesMed = col4.text_input("diabetesMed", value='Yes')

# Ejecutar la instrucción indicada. 
click = st.button("Predecir")

# Iniciar session state
if "load_state" not in st.session_state:
    st.session_state.load_state = False

if click or st.session_state.load_state:
    st.session_state.load_state = True

    try:

        # Armar JSON con estructura de datos como lo necesita la API a consumir. 
        # Agrupa las variables en un diccionario
        datos = {
            "race" :  race,
            "gender" : gender,
            "age" : age,
            "admission_type_id" : admission_type_id,
            "discharge_disposition_id" : discharge_disposition_id,
            "admission_source_id" : admission_source_id,
            "time_in_hospital" : time_in_hospital,
            "num_lab_procedures" : num_lab_procedures,
            "num_procedures" : num_procedures,
            "num_medications" : num_medications,
            "number_outpatient" : number_outpatient,
            "number_emergency" : number_emergency,
            "number_inpatient" : number_inpatient,
            "number_diagnoses" : number_diagnoses,
            "max_glu_serum" : max_glu_serum,
            "A1Cresult" : A1Cresult,
            "examide" : examide,
            "citoglipton" : citoglipton,
            "change" : change,
            "diabetesMed" : diabetesMed
        }

        # Convierte el diccionario a una cadena JSON
        json_str = json.dumps(datos)
        # st.json(json_str)

        # Request al API generado para calcular predicción sobre dato. 
        url = 'http://fast_api:8086/predict/'

        response = requests.post(url, data=json_str)

        # Plotear resultado ( con retorno de posible error )
        st.metric("resultado", value=response.text )
    except Exception as e: 
        st.metric("Falla:", value=e)
