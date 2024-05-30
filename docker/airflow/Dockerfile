FROM apache/airflow:2.6.0-python3.9
# Install python packages
RUN pip install -r mlflow==2.3.0
RUN pip install -r pycaret==3.0.0
RUN pip install -r scikit-learn==1.2.2
RUN pip install -r scipy==1.11.4
RUN pip install -r boto3==1.26.121
RUN pip install -r requests==2.28.2
RUN pip install -r joblib==1.3.0
#COPY ./requirements.txt /code/requirements.txt
#RUN pip install --user --upgrade pip
#RUN pip install -r /code/requirements.txt
