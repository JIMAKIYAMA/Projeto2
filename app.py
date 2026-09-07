from flask import Flask, request
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv('.env')

config = {
    'host': os.getenv('DB_HOST', 'localhost'),  
    'user': os.getenv('DB_USER'),  
    'password': os.getenv('DB_PASSWORD'),  
    'database': os.getenv('DB_NAME', 'db_imoveis'),  
    'port': int(os.getenv('DB_PORT', 3306)),
    'ssl_ca': os.getenv('SSL_CA_PATH')  
}


def connect_db():
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as err:
        print(f"Erro: {err}")
        return None


app = Flask(__name__)


@app.route('/imoveis', methods=['GET'])
def listar_todos():
    pass

@app.route('/imoveis/<int:id>', methods=['GET'])
def buscar_por_id(id):
    pass

@app.route('/imoveis', methods=['POST'])
def adicionar():
    pass

@app.route('/imoveis/<int:id>', methods=['DELETE'])
def deletar(id):
    pass

@app.route('/imoveis/<int:id>', methods=['PUT'])
def atualizar(id):
    pass

@app.route('/imoveis/tipo/<string:tipo>', methods=['GET'])
def buscar_por_tipo(tipo):
    pass

@app.route('/imoveis/cidade/<string:cidade>', methods=['GET'])
def buscar_por_cidade(cidade):
    pass


if __name__ == '__main__':
    app.run(debug=True)