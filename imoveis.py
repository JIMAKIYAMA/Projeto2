import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def criar_banco_de_dados():
    try:
        print("Tentando conectar ao banco de dados Aiven...")
        
        db = mysql.connector.connect(
            host=os.getenv('DB_HOST').strip(),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER').strip(),
            password=os.getenv('DB_PASSWORD').strip(),
            database=os.getenv('DB_NAME').strip(),
            ssl_ca=os.getenv('SSL_CA_PATH').strip(),
            use_pure=True
        )

        cursor = db.cursor()

        caminho = os.path.join(os.path.dirname(__file__), 'imoveis(1).sql')
        with open(caminho, 'r', encoding='utf-8') as file:
             dados = file.read()

        
        lista_de_comandos = dados.split(';')
        
        for comando in lista_de_comandos:
            comando_limpo = comando.strip()
            
            if comando_limpo:
                cursor.execute(comando_limpo)
                
        db.commit()
        
    except Exception as e:
        print(f"Ocorreu um erro ao executar: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

def gerar_links(movel_id):
    return [
        {'rel': 'self', 'href':f'/imoveis/{movel_id}', 'method': 'GET'},
        {'rel': 'update', 'href':f'/imoveis/{movel_id}', 'method': 'PUT'},
        {'rel': 'delete', 'href':f'/imoveis/{movel_id}', 'method': 'DELETE'},
    ]

if __name__ == '__main__':
     criar_banco_de_dados()