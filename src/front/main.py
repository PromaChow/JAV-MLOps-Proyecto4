import streamlit as st
import pandas as pd
import numpy as np
import requests
import json

st.title("Operaciones de Machine Learning")
st.write("Proyecto Final")
st.write("Por Juan Pablo Nieto, Nicolas Rojas y Brayan Carvajal")

# Colección de variables.  
st.write("### Registrar Dato")
col1, col2, col3 = st.columns(3)

brokered_by = col1.text_input("brokered_by", value="Broker")
status = col2.text_input("status", value="Status")
bed = col3.number_input("bed", value=1)
bath = col1.number_input("bath", value=1)
acre_lot = col2.number_input("acre_lot", value=1)
street = col3.text_input("street", value="street")
city = col1.text_input("city", value="city")
state = col2.text_input("state", value="state")
house_size = col3.number_input("house_size", value=1)

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
            "brokered_by" :  brokered_by,
            "status" :  status,
            "bed" :  bed,
            "bath" :  bath,
            "acre_lot" :  acre_lot,
            "street" :  street,
            "city" :  city,
            "state" :  state,
            "house_size" :  house_size
        }

        # Convierte el diccionario a una cadena JSON
        json_str = json.dumps(datos)
        # st.json(json_str)

        # Request al API generado para calcular predicción sobre dato. 
        url = 'http://fast_api:8086/predict/'

        response = requests.post(url, data=json_str)

        # Plotear resultado ( con retorno de posible error )
        st.metric("resultado", value=response.text)
    except Exception as e: 
        st.metric("Falla:", value=e)
