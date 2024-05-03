from airflow.models import DAG
from airflow.operators.python import PythonOperator
#from airflow.providers.postgres.operators.postgres import PostgresOperator
# from airflow.utils.task_group import TaskGroup
from datetime import datetime
from sqlalchemy import create_engine #koneksi ke postgres
import pandas as pd

from elasticsearch import Elasticsearch
# from elasticsearch.helpers import bulk


def load_csv_to_postgres():
    database = "airflow_m3"
    username = "airflow_m3"
    password = "airflow_m3"
    host = "postgres"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engine = create_engine(postgres_url)
    # engine= create_engine("postgresql+psycopg2://airflow:airflow@postgres/airflow")
    conn = engine.connect()

    df = pd.read_csv('/opt/airflow/dags/P2M3_Fadhilah_data_raw.csv')
    #df.to_sql(nama_table_db, conn, index=False, if_exists='replace')
    df.to_sql('table_m', conn, index=False, if_exists='replace')  # M
    

def ambil_data():
    # fetch data
    database = "airflow_m3"
    username = "airflow_m3"
    password = "airflow_m3"
    host = "postgres"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engine = create_engine(postgres_url)
    conn = engine.connect()

    df = pd.read_sql_query("select * from table_m", conn) #nama table sesuaikan sama nama table di postgres
    df.to_csv('/opt/airflow/dags/P2M3_Fadhilah_data_raw.csv', sep=',', index=False)
    


def preprocessing(): 
    ''' fungsi untuk membersihkan data
    '''
    # pembisihan data
    data = pd.read_csv("/opt/airflow/dags/P2M3_Fadhilah_data_raw.csv")

    # bersihkan data 
    data.dropna(inplace=True)
    data.drop_duplicates(inplace=True)
    data.rename(columns={'Date': 'date', 'F.Y': 'fiscal_year', 'QUARTER': 'quarter', 'P_NO': 'product_number', 'PAYMENT TYPE': 'payment_type', 'TYPE OF PRODUCT': 'type_of_product', 'Quantity': 'quantity', 'Price': 'price', 'Amount': 'amount', 'TYPE OF ACCESSORY/MOBILE': 'type_of_accessory/mobile'}, inplace=True)
    data['date'] = pd.to_datetime(data['date'], format='%d-%m-%Y')
    data['fiscal_year'] = data['fiscal_year'].str.split('-').str[0]
    data.to_csv('/opt/airflow/dags/P2M3_Fadhilah_data_clean.csv', index=False)
    
def upload_to_elasticsearch():
    es = Elasticsearch("http://elasticsearch:9200")
    df = pd.read_csv('/opt/airflow/dags/P2M3_Fadhilah_data_clean.csv')
    
    for i, r in df.iterrows():
        doc = r.to_dict()  # Convert the row to a dictionary
        res = es.index(index="table_m3", id=i+1, body=doc)
        print(f"Response from Elasticsearch: {res}")
        
        
default_args = {
    'owner': 'Fadhil', 
    'start_date': datetime(2023, 12, 24, 12, 00)
}

with DAG(
    "P2M3_Fadhil_DAG_hck", #atur sesuai nama project kalian
    description='Milestone_3',
    schedule_interval='30 6 10 * *', #atur schedule untuk menjalankan airflow pada 06:30.
    default_args=default_args, 
    catchup=False
) as dag:
    # Task : 1
    load_csv_task = PythonOperator(
        task_id='load_csv_to_postgres',
        python_callable=load_csv_to_postgres) #sesuaikan dengan nama fungsi yang kalian buat
    
    #task: 2
    ambil_data_pg = PythonOperator(
        task_id='ambil_data_postgres',
        python_callable=ambil_data) #
    

    # Task: 3
    '''  Fungsi ini ditujukan untuk menjalankan pembersihan data.'''
    edit_data = PythonOperator(
        task_id='edit_data',
        python_callable=preprocessing)

    # Task: 4
    upload_data = PythonOperator(
        task_id='upload_data_elastic',
        python_callable=upload_to_elasticsearch)

    #proses untuk menjalankan di airflow
    load_csv_task >> ambil_data_pg >> edit_data >> upload_data



