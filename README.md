# Proyecto 3: MLOps

## Por Brayan Carvajal, Juan Pablo Nieto y Nicolás Rojas

Este proyecto busca evaluar el proceso despliegue de MLOPS usando Kubernetes, empezando
por la recolección y procesamiento de datos, para generar una fuente de información lista para el
entrenamiento de modelos de Machine Learning. El modelo de mejor desempeño debe usarse para
realizar inferencia mediante un API, la cual se consume mediante una interfaz gráfica. Para esto se debe:

- Usando AirFlow cree los DAGs que le permitan recolectar, procesar y almacenar los datos.
- Para el registro de experimentos y modelos utilice MLflow
- Usando FastAPI cree un API que consuma el mejor modelo
- Cree una interfaz gráfica usando Streamlit que permita realizar inferencia.

Para crear el servidor de MLflow y AirFlow, depende del estudiante decidir donde se alojará, puede ser en en la máquina virtual directamente, en un contenedor usando docker-compose o en un pod de kubernetes.

## Ejecución del código

El código en este repositorio puede ejecutarse siguiendo los siguientes pasos:

- Instale docker siguiendo las instrucciones en la [documentación oficial](https://docs.docker.com/get-docker/).

- Clone este repositorio con el siguiente comando:
    ```shell
    git clone https://github.com/GacelyML/JAV_MLOps_Proyecto3
    ```

- Ubíquese en la carpeta recién creada:
    ```shell
    cd JAV_MLOps_Proyecto3
    ```

- Cree las carpetas que contendran los datos de las BD y minio
    ```shell
    mkdir data, db_clean_data, db_ml_data, db_raw_data, minio_data
    ```

- Abra en una nueva pestaña una terminal dentro del entorno Jupyter y descargue los datos a través de los siguientes comandos:
    ```shell
    dvc remote modify --local data credentialpath './credentials/test-gcp-gacelydev-e4bc89448148.json'
    ```
    ```shell
    dvc pull
    ```

- Cree los servicios con los siguientes comandos:
    ```shell
    docker compose -f docker-compose.yaml --env-file config.env up airflow-init --build
    ```
    ```shell
    docker compose -f docker-compose.yaml --env-file config.env up --build -d
    ```
    ```shell
    docker compose -f docker-compose-kube.yaml --env-file config.env up --build -d
    ```

- Si desea probar los servicios desplegados a traves de la red PUJ con la maquina virtual, cambie "localhost" por 10.43.101.154 en las siguientes indicaciones 

- Ingrese a Airflow desde un navegador web apuntando a la dirección http://localhost:8080, desde este podrá observar los DAGS construidos para la descarga de los datos, el procesamiento de los mismo y el entrenamiento y registro del modelo con MLFlow

- Ingrese a MLFlow desde un navegador web apuntando a la dirección http://localhost:8083, en esta interfaz se encontraran los diferentes experimentos ejecutados y los modelos registrados, junto con sus artifactos y métricas de rendimiento

- En la dirección http://localhost:8082, se encuentra la interfaz de minio en la cual se podrán crear buckets de almacenamiento

- En http://localhost:8085, se encuentra una interfaz de jupyterlab que permite interactuar de forma dinámica con los códigos fuentes

- En http://localhost:8086/docs se podrá visualizar interactivamente con la API que realiza inferencia con el modelo asignado como productivo desde MLFlow

- En http://localhost:8087, se encuentra una interfaz gráfica que permite recibir las variables de entrada del modelo y realizar la predicción a través de la API anteriormente mencionada

- Si desea interrumpir el servicio, puede hacerlo con el siguiente comando:
    ```shell
    docker compose down --volumes --remove-orphans
    ```
- Opcionalmente se puede levantar algunos servicios con Kubernetes, para esto se construyeron dos archivos docker-compose. El primero docker-compose.yaml contiene los servicios Airflow, MLFlow y JupyterLab que se esperan seguir ejecutando a través de docker, y el segundo docker-compose-kube.yaml, contiene los servicios que pueden ser desplegados a través de kubernetes. Para desplegar estos servicios se debe seguir los siguientes pasos

- Compile el archivo docker-compose-kube a través de kompose para convertir docker compose a archivos de configuración yaml
    ```shell
    kompose convert -f docker-compose.yml -o komposefiles/ --volumes hostPath
    ```
- Aplique estas configuraciones agregando cada uno de los archivos de configuración creados
    ```shell
    microk8s kubectl apply -f komposefiles/
    ```