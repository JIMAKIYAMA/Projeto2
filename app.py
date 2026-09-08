from flask import Flask, request, jsonify
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
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imoveis")
        resultado = cursor.fetchall()

        if not resultado: 
            return jsonify({'mensagem': 'Nenhum imóvel encontrado'}), 200
        
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/imoveis/<int:id>', methods=['GET'])
def buscar_por_id(id):
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (id,))
        resultado = cursor.fetchone()

        if not resultado: 
            return jsonify({'mensagem': 'Nenhum imóvel encontrado'}), 200

        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/imoveis', methods=['POST'])
def adicionar():
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    add = request.get_json()

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO imoveis (logradouro, tipo_logradouro, bairro, cidade, cep, tipo," \
        "valor, data_aquisicao) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (add['logradouro'], add['tipo_logradouro'], add['bairro'], add['cidade'],
                                           add['cep'],add['tipo'], add['valor'], add['data_aquisicao']))

        conn.commit()
        return jsonify({'mensagem': 'Imóvel adicionado com sucesso!'}), 201
    
    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/imoveis/<int:id>', methods=['DELETE'])
def deletar(id):
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM imoveis WHERE id = %s",(id,))
        conn.commit()

        return jsonify({"mensagem": "Imóvel deletado com sucesso!"}), 200
    
    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/imoveis/<int:id>', methods=['PUT'])
def atualizar(id):
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    dados = request.get_json()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE imoveis SET logradouro = %s, tipo_logradouro = %s, bairro = %s, cidade = %s, cep= %s, tipo= %s," \
        "valor = %s, data_aquisicao = %s WHERE id = %s",(dados['logradouro'], dados['tipo_logradouro'], dados['bairro'], dados['cidade'],
            dados['cep'], dados['tipo'], dados['valor'], dados['data_aquisicao'], id))
        conn.commit()

        return jsonify({'mensagem': 'Imóvel atualizado com sucesso!'}), 200
    
    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/imoveis/tipo/<string:tipo>', methods=['GET'])
def buscar_por_tipo(tipo):
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imoveis WHERE tipo = %s",(tipo,))
        resultado = cursor.fetchall()
        conn.commit()

        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/imoveis/cidade/<string:cidade>', methods=['GET'])
def buscar_por_cidade(cidade):
    conn = connect_db()
    if conn is None:
        return jsonify({'mensagem': 'Erro interno ao tentar conectar ao banco de dados'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imoveis WHERE cidade = %s",(cidade,))
        resultado = cursor.fetchall()
        conn.commit()

        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)