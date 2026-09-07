import pytest
from unittest.mock import patch, MagicMock
from app import connect_db, app
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.fixture
def cliente():
    app.config['TESTING'] = True
    with app.test_client() as cliente:
        yield cliente

@pytest.fixture
def banco_de_dados():
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST').strip(),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER').strip(),
        password=os.getenv('DB_PASSWORD').strip(),
        database=os.getenv('DB_NAME').strip(),
        ssl_ca=os.getenv('SSL_CA_PATH').strip() 
    )

    cursor = db.cursor()
    resultado = None
    cursor.execute('SELECT * FROM imoveis')
    resultado = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()

    yield resultado

@patch('app.connect_db')
def test_listar_todos(mock_connect_db, cliente):

    
    conn_mock = MagicMock()
    cursor_mock = MagicMock()
    mock_connect_db.return_value = conn_mock
    conn_mock.cursor.return_value = cursor_mock

    gabarito = [
        ('Nicole Common', 'Travessa', 'Lake Danielle', 'Judymouth', '85184', 'casa em condominio', 488423.52, '2017-07-29'),
        ('Price Prairie', 'Travessa', 'Colonton', 'North Garyville', '93354', 'casa em condominio', 260069.89, '2021-11-30')
    ]
    cursor_mock.fetchall.return_value = gabarito
    resposta = cliente.get('/imoveis')

    gabarito_json = [list(imovel) for imovel in gabarito]
    assert resposta.status_code == 200
    assert resposta.get_json() == gabarito_json

@patch('app.connect_db')
def test_buscar_por_imovel(mock_connect_db, cliente):
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    conn_mock.cursor.return_value = cursor_mock
    mock_connect_db.return_value = conn_mock

    gabarito = (
        'Nicole Common', 'Travessa', 'Lake Danielle', 'Judymouth', 
        '85184', 'casa em condominio', 488423.52, '2017-07-29'
    )
    cursor_mock.fetchone.return_value = gabarito
    resposta = cliente.get('/imoveis/1')

    assert resposta.get_json() == list(gabarito)
    assert resposta.status_code == 200

@patch('app.connect_db')
def test_adicionar_por_id(mock_connect_db, cliente):
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    conn_mock.cursor.return_value = cursor_mock
    mock_connect_db.return_value = conn_mock

    novo_imovel = {
        "logradouro": "Rua das Flores",
        "tipo_logradouro": "Rua",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "cep": "01000-000",
        "tipo": "apartamento",
        "valor": 350000.00,
        "data_aquisicao": "2023-01-15"
    }

    resposta = cliente.post('/imoveis', json=novo_imovel)

    assert resposta.get_json() == {"mensagem": "Imóvel adicionado com sucesso!"}
    assert resposta.status_code == 201

@patch('app.connect_db')
def test_atualizar(mock_connect_db, cliente):
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    conn_mock.cursor.return_value = cursor_mock
    mock_connect_db.return_value = conn_mock

    imovel_atualizado = {
        "logradouro": "Rua das Flores",
        "tipo_logradouro": "Rua",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "cep": "01000-000",
        "tipo": "apartamento",
        "valor": 350000.00,
        "data_aquisicao": "2023-01-15"
    }

    resposta = cliente.put('/imoveis/1', json=imovel_atualizado)

    assert resposta.get_json() == {"mensagem": "Imóvel atualizado com sucesso!"}
    assert resposta.status_code == 200

@patch('app.connect_db')
def test_remover(mock_connect_db, cliente):
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    conn_mock.cursor.return_value = cursor_mock
    mock_connect_db.return_value = conn_mock

    resposta = cliente.delete('/imoveis/1')

    assert resposta.get_json() == {"mensagem": "Imóvel deletado com sucesso!"}
    assert resposta.status_code == 200


@patch('app.connect_db')
def test_buscar_por_tipo(mock_connect_db, cliente):
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    conn_mock.cursor.return_value = cursor_mock
    mock_connect_db.return_value = conn_mock




    gabarito = [
            ('Nicole Common', 'Travessa', 'Lake Danielle', 'Judymouth', '85184', 'casa em condominio', 488423.52, '2017-07-29'),
            ('Price Prairie', 'Travessa', 'Colonton', 'North Garyville', '93354', 'casa em condominio', 260069.89, '2021-11-30')
        ]
    cursor_mock.fetchall.return_value = gabarito

    resposta = cliente.get(f'/imoveis/tipo/casa em condominio')
    gabarito_json = [list(imovel) for imovel in gabarito]

    assert resposta.get_json() == gabarito_json
    assert resposta.status_code == 200 


@patch('app.connect_db')
def test_buscar_por_cidade(mock_connect_db, cliente):
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    conn_mock.cursor.return_value = cursor_mock
    mock_connect_db.return_value = conn_mock

    gabarito = [
            ('Nicole Common', 'Travessa', 'Lake Danielle', 'Curitiba', '85184', 'casa em condominio', 488423.52, '2017-07-29'),
            ('Price Prairie', 'Travessa', 'Colonton', 'Curitiba', '93354', 'casa em condominio', 260069.89, '2021-11-30')
        ]
    cursor_mock.fetchall.return_value = gabarito

    resposta = cliente.get(f'/imoveis/cidade/Curitiba')
    gabarito_json = [list(imovel) for imovel in gabarito]

    assert resposta.get_json() == gabarito_json
    assert resposta.status_code == 200 