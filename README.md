# Proyecto 4: MLOps

## Por Brayan Carvajal, Juan Pablo Nieto y Nicolás Rojas

Este trabajo busca evaluar entendimiento, aplicación y explicación del ciclo de vida de un proyecto de aprendizaje de maquina. Se espera ver aplicados conceptos vistos en el desarrollo del curso, procesamiento de datos mediante pipeline completos que permitan realizar entrenamiento de modelos. Este debe ser un proceso automatizado que permita identificar cambios en los datos que permitan de manera automática realizar nuevos entrenamientos mediante el uso de un orquestador. Cada modelo entrenado debe ser registrado para su posterior uso. El modelo que presente mejor desempeño ante las métricas definidas, debe ser usado en un proceso de inferencia mediante una API que estará en un contenedor, el cual su imagen debe crearse y publicarse de manera automática. El objetivo es desplegar todas las herramientas necesarias para ejecutar el procesamiento de datos y entrenamiento de manera programada. Finalmente se espera un análisis del mejor modelo en cada etapa y una explicación de a que se debe el cambio en el modelo, que cambió para que fuera necesario un nuevo entrenamiento.

- Usando AirFlow cree los DAGs que le permitan recolectar, procesar y almacenar los datos.
- Para el registro de experimentos y modelos utilice MLflow.
- Usando FastAPI cree un API que consuma el mejor modelo.
- Cree una interfaz gráfica usando Streamlit que permita realizar inferencia.
- Utilice Github Actions para construir y publicar las imágenes de contenedores.
- Usando SHAP realice interpretación de los modelos desplegados y cambios de los mismos.

## Ejecución del código

El código en este repositorio puede ejecutarse siguiendo los siguientes pasos:

- Instale docker siguiendo las instrucciones en la [documentación oficial](https://docs.docker.com/get-docker/).

- Clone este repositorio con el siguiente comando:

  ```shell
  git clone https://github.com/GacelyML/JAV_MLOps_Proyecto4
  ```

- Ubíquese en la carpeta recién creada:

  ```shell
  cd JAV_MLOps_Proyecto4
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
  docker compose -f docker-compose.yaml --env-file config.env up --build -d
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
