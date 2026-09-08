# Flask + SQLite3 + pytest + Mocks — Guia Completo com Exercícios Progressivos

> Um caminho do zero até uma API CRUD completa, testada com `pytest`, `unittest.mock` e banco `sqlite3`.
> Cada nível tem **teoria curta → código comentado → exercício → solução**.

---

## Índice

| Nível | Assunto | O que você sai sabendo |
|---|---|---|
| 0 | Ambiente e estrutura | venv, dependências, organização de pastas |
| 1 | `sqlite3` puro | conectar, criar tabela, INSERT, SELECT, cursor |
| 2 | Flask básico | rotas, JSON, status codes |
| 3 | `pytest` e o test client | primeiro teste, fixtures, `assert` |
| 4 | `unittest.mock` isolado | `MagicMock`, `patch`, `return_value` |
| 5 | Mockando o banco na API | `@patch("app.connect_db")` |
| 6 | Rotas com parâmetro e POST | validação, 400, 404, 201 |
| 7 | `conftest.py` e `parametrize` | testes tabelados, reuso de fixtures |
| 8 | `side_effect` e falhas | simular exceções, erro 500 |
| 9 | Teste de integração real | SQLite em memória, quando NÃO mockar |
| 10 | Projeto final | CRUD completo + suíte de testes + cobertura |

---

## Nível 0 — Preparando o ambiente

### Teoria

Todo projeto Python sério vive dentro de um **ambiente virtual**. Isso evita que as bibliotecas de um projeto quebrem outro.

O `sqlite3` é ainda mais simples que o MySQL do material original: **já vem embutido no Python** e o banco inteiro é um único arquivo `.db`. Você não precisa instalar servidor, nem usuário, nem senha, nem `.env`.

### Passo a passo

```bash
# 1. Criar a pasta do projeto
mkdir api_escola && cd api_escola

# 2. Criar e ativar o ambiente virtual
python -m venv venv

# Linux / macOS
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# 3. Instalar as dependências
pip install flask pytest pytest-cov

# 4. Congelar as versões
pip freeze > requirements.txt
```

### Estrutura de pastas que vamos usar

```
api_escola/
├── app.py              # a API Flask
├── db.py               # funções de conexão e criação do banco
├── schema.sql          # DDL das tabelas
├── escola.db           # gerado automaticamente (NÃO versionar)
├── requirements.txt
└── tests/
    ├── conftest.py     # fixtures compartilhadas
    └── test_app.py     # os testes
```

E um `.gitignore` mínimo:

```
venv/
__pycache__/
*.db
.pytest_cache/
.coverage
htmlcov/
```

### 🎯 Exercício 0

Crie o ambiente acima e rode `pytest --version` e `python -c "import sqlite3; print(sqlite3.sqlite_version)"`. Ambos devem imprimir algo sem erro.

---

## Nível 1 — `sqlite3` puro (sem Flask ainda)

### Teoria

O fluxo com `sqlite3` é sempre o mesmo:

```
connect() → cursor() → execute() → fetch*() / commit() → close()
```

Diferenças importantes em relação ao `mysql.connector` do material original:

| Conceito | MySQL | SQLite3 |
|---|---|---|
| Import | `import mysql.connector` | `import sqlite3` (nativo) |
| Conexão | host, user, password, port | caminho de um arquivo |
| Placeholder na query | `%s` | `?` |
| Auto increment | `AUTO_INCREMENT` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| Checar conexão | `conn.is_connected()` | não existe (levanta exceção se falhar) |
| Erro base | `mysql.connector.Error` | `sqlite3.Error` |

### `schema.sql`

```sql
DROP TABLE IF EXISTS tbl_alunos;

CREATE TABLE tbl_alunos (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
```

### `db.py`

```python
import sqlite3
import os

# Caminho do arquivo do banco. Usamos caminho absoluto para não depender
# de onde o comando foi executado (isso quebra muito teste na vida real).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "escola.db")


def connect_db():
    """Estabelece a conexão com o banco SQLite.

    Retorna a conexão ou None se der erro — mesmo contrato do exemplo
    com MySQL, para o resto do código não precisar mudar.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # row_factory faz o cursor devolver objetos parecidos com dicionário
        # (acessáveis por nome de coluna). Comentado por enquanto: no Nível 1
        # vamos trabalhar com tuplas, igual ao material original.
        # conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as err:
        print(f"Erro: {err}")
        return None


def init_db():
    """Cria as tabelas a partir do schema.sql e insere dados de exemplo."""
    conn = connect_db()
    if conn is None:
        raise RuntimeError("Não foi possível conectar ao banco")

    with open(os.path.join(BASE_DIR, "schema.sql")) as f:
        conn.executescript(f.read())

    conn.executemany(
        "INSERT INTO tbl_alunos (nome, email) VALUES (?, ?)",
        [("Alice", "alice@email.com"), ("Bob", "bob@email.com")],
    )
    conn.commit()
    conn.close()
    print("Banco inicializado com sucesso.")


if __name__ == "__main__":
    init_db()
```

Rode:

```bash
python db.py
```

### Lendo os dados

```python
from db import connect_db

conn = connect_db()
cursor = conn.cursor()
cursor.execute("SELECT * FROM tbl_alunos")
print(cursor.fetchall())
# [(1, 'Alice', 'alice@email.com'), (2, 'Bob', 'bob@email.com')]
conn.close()
```

Repare: `fetchall()` devolve uma **lista de tuplas**. É exatamente por isso que a API precisa converter para dicionário antes de virar JSON.

### ⚠️ Nunca faça isso

```python
# ERRADO — SQL Injection
cursor.execute(f"SELECT * FROM tbl_alunos WHERE nome = '{nome}'")

# CERTO — placeholder
cursor.execute("SELECT * FROM tbl_alunos WHERE nome = ?", (nome,))
```

A vírgula em `(nome,)` é obrigatória: sem ela não é uma tupla.

### 🎯 Exercício 1

1. Crie o `schema.sql` e o `db.py` acima e rode `python db.py`.
2. Escreva um script `consulta.py` que:
   - conecte ao banco;
   - insira um aluno chamado `Carol / carol@email.com`;
   - imprima **apenas** os alunos cujo email termine em `@email.com`, usando placeholder `?` e `LIKE`;
   - feche a conexão.

<details>
<summary>💡 Solução</summary>

```python
from db import connect_db

conn = connect_db()
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO tbl_alunos (nome, email) VALUES (?, ?)",
    ("Carol", "carol@email.com"),
)
conn.commit()

cursor.execute("SELECT * FROM tbl_alunos WHERE email LIKE ?", ("%@email.com",))
for linha in cursor.fetchall():
    print(linha)

conn.close()
```
</details>

---

## Nível 2 — A API Flask

### Teoria

O Flask converte automaticamente um `dict` retornado por uma rota em JSON. O padrão `return resp, status` define o corpo e o código HTTP.

Códigos que vamos usar:

| Código | Quando |
|---|---|
| 200 OK | deu certo, tem conteúdo |
| 201 Created | criou um recurso (POST) |
| 400 Bad Request | o cliente mandou dados inválidos |
| 404 Not Found | o recurso não existe |
| 500 Internal Server Error | falhou do lado do servidor (ex.: banco caiu) |

### `app.py`

```python
from flask import Flask
from db import connect_db

app = Flask(__name__)


@app.route("/alunos", methods=["GET"])
def get_alunos():
    conn = connect_db()

    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_alunos")
    results = cursor.fetchall()
    conn.close()

    if not results:
        return {"erro": "Nenhum aluno encontrado"}, 404

    alunos = [
        {"id": aluno[0], "nome": aluno[1], "email": aluno[2]}
        for aluno in results
    ]
    return {"alunos": alunos}, 200


if __name__ == "__main__":
    app.run(debug=True)
```

Suba com `python app.py` e acesse `http://localhost:5000/alunos`.

### 🎯 Exercício 2

Adicione a rota `GET /alunos/<int:id>` que retorna **um** aluno:

- 200 com `{"aluno": {...}}` se existir;
- 404 com `{"erro": "Aluno não encontrado"}` se não existir;
- 500 se a conexão falhar.

<details>
<summary>💡 Solução</summary>

```python
@app.route("/alunos/<int:id>", methods=["GET"])
def get_aluno(id):
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_alunos WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {"erro": "Aluno não encontrado"}, 404

    return {"aluno": {"id": row[0], "nome": row[1], "email": row[2]}}, 200
```

Note o `fetchone()`: devolve **uma tupla ou `None`**, não uma lista.
</details>

---

## Nível 3 — Primeiro contato com `pytest`

### Teoria

O `pytest` descobre testes automaticamente seguindo convenções:

- arquivos `test_*.py` ou `*_test.py`
- funções `test_*`
- classes `Test*` (sem `__init__`)

E usa o `assert` do Python puro — sem `assertEquals`, sem herdar de classe nenhuma.

```python
def test_soma():
    assert 1 + 1 == 2
```

### Fixtures: o coração do pytest

Uma **fixture** é uma função que prepara algo para o teste. Você a "pede" declarando o nome dela como parâmetro do teste.

```python
import pytest

@pytest.fixture
def numeros():
    return [1, 2, 3]

def test_soma_lista(numeros):   # pytest injeta a fixture aqui
    assert sum(numeros) == 6
```

Se a fixture usa `yield`, tudo depois do `yield` roda como **limpeza** (teardown) após o teste:

```python
@pytest.fixture
def arquivo_temporario():
    f = open("temp.txt", "w")
    yield f          # o teste roda aqui
    f.close()        # limpeza
    os.remove("temp.txt")
```

### O test client do Flask

O Flask oferece um cliente HTTP falso: ele executa as rotas **em memória**, sem subir servidor, sem abrir porta, sem rede.

```python
import pytest
from app import app


@pytest.fixture
def client():
    """Cria um cliente de teste para a API."""
    app.config["TESTING"] = True   # mostra erros reais em vez de HTML de erro
    with app.test_client() as client:
        yield client


def test_rota_alunos_responde(client):
    response = client.get("/alunos")
    assert response.status_code in (200, 404)
```

Métodos úteis da resposta:

| Atributo | O que devolve |
|---|---|
| `response.status_code` | inteiro (200, 404...) |
| `response.get_json()` | o corpo já convertido em `dict`/`list` |
| `response.data` | bytes crus |
| `response.headers` | cabeçalhos |

### 🎯 Exercício 3

Crie `tests/test_app.py` com a fixture `client` e dois testes que rodam **contra o banco real** (`escola.db`, que já tem Alice e Bob):

1. `test_get_alunos_ok`: status 200 e a chave `"alunos"` presente no JSON.
2. `test_get_aluno_inexistente`: `GET /alunos/9999` retorna 404.

Rode com `pytest -v`.

<details>
<summary>💡 Solução</summary>

```python
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_alunos_ok(client):
    response = client.get("/alunos")
    assert response.status_code == 200
    assert "alunos" in response.get_json()


def test_get_aluno_inexistente(client):
    response = client.get("/alunos/9999")
    assert response.status_code == 404
    assert response.get_json() == {"erro": "Aluno não encontrado"}
```

**Mas repare no problema:** esse teste só passa porque o `escola.db` existe e tem dados. Se alguém apagar um aluno, o teste quebra sem que o código tenha mudado. Isso é um **teste frágil** — e é exatamente o problema que os mocks resolvem no próximo nível.
</details>

---

## Nível 4 — `unittest.mock` fora do Flask

### Teoria

Um **mock** é um objeto falso que finge ser outro. Ele aceita qualquer chamada, qualquer atributo, e grava tudo que aconteceu com ele.

```python
from unittest.mock import MagicMock

m = MagicMock()
m.qualquer_coisa()            # não dá erro
m.a.b.c.d()                   # não dá erro
print(m.metodo())             # <MagicMock name='mock.metodo()' id=...>
```

#### `return_value` — o que o mock devolve quando é chamado

```python
m = MagicMock()
m.fetchall.return_value = [(1, "Alice")]

print(m.fetchall())   # [(1, 'Alice')]
print(m.fetchall())   # [(1, 'Alice')]  → sempre o mesmo
```

#### Encadeando mocks

Esta é a parte que costuma confundir. Queremos simular:

```python
conn.cursor().execute(...)
conn.cursor().fetchall()
```

Então precisamos que `conn.cursor()` **devolva** o mock do cursor:

```python
mock_conn = MagicMock()
mock_cursor = MagicMock()

mock_conn.cursor.return_value = mock_cursor      # conn.cursor() → mock_cursor
mock_cursor.fetchall.return_value = [(1, "Alice", "alice@email.com")]

# Agora, do ponto de vista do código testado:
c = mock_conn.cursor()
c.execute("SELECT ...")
print(c.fetchall())    # [(1, 'Alice', 'alice@email.com')]
```

> 🧠 **Regra de ouro:** `mock.metodo.return_value` configura o resultado de `mock.metodo()`.
> Sem os parênteses você configura; com os parênteses você chama.

#### Verificando o que foi chamado

```python
mock_cursor.execute.assert_called_once_with("SELECT * FROM tbl_alunos")
mock_cursor.execute.assert_called()          # foi chamado pelo menos 1x
mock_cursor.execute.assert_not_called()      # nunca foi chamado
mock_conn.close.assert_called_once()         # exatamente 1x

print(mock_cursor.execute.call_count)        # 1
print(mock_cursor.execute.call_args)         # call('SELECT * FROM tbl_alunos')
print(mock_cursor.execute.call_args_list)    # todas as chamadas
```

#### `patch` — trocando o objeto real pelo mock

`patch` substitui temporariamente um objeto **no lugar onde ele é usado**, e desfaz a substituição no fim.

```python
from unittest.mock import patch

# Como decorator (o mock vira o 1º parâmetro da função)
@patch("app.connect_db")
def test_algo(mock_connect_db):
    mock_connect_db.return_value = "fingindo ser uma conexão"
    ...

# Como context manager
def test_algo():
    with patch("app.connect_db") as mock_connect_db:
        mock_connect_db.return_value = "..."
        ...
```

### ⚠️ O erro nº 1 de quem começa: patchear o caminho errado

> **Patch onde é usado, não onde é definido.**

Se o `app.py` faz:

```python
from db import connect_db      # ← trouxe o nome para dentro de app
```

então existe uma referência chamada `app.connect_db`, e é **essa** que você precisa trocar:

```python
@patch("app.connect_db")     # ✅ CERTO
@patch("db.connect_db")      # ❌ ERRADO — app.py já guardou a referência antiga
```

Se, em vez disso, o `app.py` fizesse `import db` e chamasse `db.connect_db()`, aí sim o alvo seria `db.connect_db`.

### Ordem dos parâmetros com múltiplos decorators

Os `@patch` são aplicados **de baixo para cima**:

```python
@patch("app.log")           # → segundo parâmetro
@patch("app.connect_db")    # → primeiro parâmetro
def test_x(mock_connect_db, mock_log, client):
    ...
```

E as fixtures do pytest (como `client`) vêm **depois** de todos os mocks.

### 🎯 Exercício 4

Sem Flask, apenas com `MagicMock`, escreva a função e o teste:

```python
def contar_alunos(conn):
    """Retorna quantos alunos existem na tabela."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tbl_alunos")
    return cursor.fetchone()[0]
```

Escreva um teste que:
1. crie um mock de conexão que simule o banco retornando `(42,)`;
2. verifique que `contar_alunos(mock_conn) == 42`;
3. verifique que o SQL correto foi executado exatamente uma vez.

<details>
<summary>💡 Solução</summary>

```python
from unittest.mock import MagicMock


def test_contar_alunos():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (42,)

    assert contar_alunos(mock_conn) == 42

    mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM tbl_alunos")
    mock_conn.cursor.assert_called_once()
```
</details>

---

## Nível 5 — Mockando o banco dentro da API

Agora juntamos tudo: test client do Flask + `patch` + `MagicMock`.

### O teste completo, linha a linha

```python
import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.connect_db")
def test_get_alunos(mock_connect_db, client):
    """Testa a rota /alunos sem tocar no banco real."""

    # 1. Criamos os dublês
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # 2. conn.cursor() devolve nosso cursor falso
    mock_conn.cursor.return_value = mock_cursor

    # 3. O "banco" responde isso
    mock_cursor.fetchall.return_value = [
        (1, "Alice", "alice@email.com"),
        (2, "Bob", "bob@email.com"),
    ]

    # 4. connect_db() devolve nossa conexão falsa
    mock_connect_db.return_value = mock_conn

    # 5. Executamos a rota
    response = client.get("/alunos")

    # 6. Verificamos a resposta
    assert response.status_code == 200
    assert response.get_json() == {
        "alunos": [
            {"id": 1, "nome": "Alice", "email": "alice@email.com"},
            {"id": 2, "nome": "Bob", "email": "bob@email.com"},
        ]
    }

    # 7. Verificamos a interação com o "banco"
    mock_cursor.execute.assert_called_once_with("SELECT * FROM tbl_alunos")
    mock_conn.close.assert_called_once()
```

### Os três cenários da mesma rota

```python
@patch("app.connect_db")
def test_get_alunos_vazio(mock_connect_db, client):
    """Banco sem nenhum aluno → 404."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []       # ← lista vazia
    mock_connect_db.return_value = mock_conn

    response = client.get("/alunos")

    assert response.status_code == 404
    assert response.get_json() == {"erro": "Nenhum aluno encontrado"}


@patch("app.connect_db")
def test_get_alunos_sem_conexao(mock_connect_db, client):
    """connect_db() falhou e devolveu None → 500."""
    mock_connect_db.return_value = None          # ← simula falha

    response = client.get("/alunos")

    assert response.status_code == 500
    assert response.get_json() == {"erro": "Erro ao conectar ao banco de dados"}
```

Repare como o terceiro teste é **impossível** de escrever sem mock: você teria que derrubar o banco de verdade no meio da suíte.

### Por que isso vale a pena

| Sem mock | Com mock |
|---|---|
| Precisa de banco rodando | Roda em qualquer máquina |
| Lento (I/O de disco/rede) | Milissegundos |
| Um teste suja o dado do outro | Cada teste é isolado |
| Difícil testar erro de conexão | Trivial |
| Falha ambígua: foi o código ou o banco? | Falhou = o código quebrou |

### 🎯 Exercício 5

Escreva três testes mockados para a rota `GET /alunos/<id>` que você criou no Nível 2:

1. aluno existe → 200 e o JSON correto;
2. aluno não existe (`fetchone` devolve `None`) → 404;
3. bônus: verifique que o SQL foi chamado com o parâmetro correto, ou seja
   `execute("SELECT * FROM tbl_alunos WHERE id = ?", (1,))`.

<details>
<summary>💡 Solução</summary>

```python
@patch("app.connect_db")
def test_get_aluno_existente(mock_connect_db, client):
    mock_conn, mock_cursor = MagicMock(), MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1, "Alice", "alice@email.com")
    mock_connect_db.return_value = mock_conn

    response = client.get("/alunos/1")

    assert response.status_code == 200
    assert response.get_json() == {
        "aluno": {"id": 1, "nome": "Alice", "email": "alice@email.com"}
    }
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM tbl_alunos WHERE id = ?", (1,)
    )


@patch("app.connect_db")
def test_get_aluno_nao_encontrado(mock_connect_db, client):
    mock_conn, mock_cursor = MagicMock(), MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_connect_db.return_value = mock_conn

    response = client.get("/alunos/999")

    assert response.status_code == 404
    assert response.get_json() == {"erro": "Aluno não encontrado"}
```
</details>

---

## Nível 6 — POST, validação e mais códigos de status

### Teoria

Numa rota `POST` você lê o corpo com `request.get_json()`. E **nunca confie no cliente**: valide antes de tocar no banco.

Ordem recomendada dentro da rota:

1. ler e validar a entrada → `400` se inválida
2. conectar → `500` se falhar
3. executar → `commit()`
4. devolver `201` com o recurso criado

### `POST /alunos`

```python
from flask import Flask, request
import sqlite3
from db import connect_db

app = Flask(__name__)


@app.route("/alunos", methods=["POST"])
def criar_aluno():
    dados = request.get_json(silent=True)

    # 1. Validação — antes de qualquer coisa
    if not dados:
        return {"erro": "Corpo da requisição deve ser um JSON válido"}, 400

    nome = dados.get("nome")
    email = dados.get("email")

    if not nome or not email:
        return {"erro": "Campos 'nome' e 'email' são obrigatórios"}, 400

    if "@" not in email:
        return {"erro": "Email inválido"}, 400

    # 2. Conexão
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    # 3. Execução
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tbl_alunos (nome, email) VALUES (?, ?)",
            (nome, email),
        )
        conn.commit()
        novo_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return {"erro": "Email já cadastrado"}, 409
    finally:
        conn.close()

    # 4. Resposta
    return {"aluno": {"id": novo_id, "nome": nome, "email": email}}, 201
```

### Testando o POST

```python
@patch("app.connect_db")
def test_criar_aluno_sucesso(mock_connect_db, client):
    mock_conn, mock_cursor = MagicMock(), MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 3                    # o "id" gerado pelo banco
    mock_connect_db.return_value = mock_conn

    response = client.post("/alunos", json={"nome": "Carol", "email": "carol@email.com"})

    assert response.status_code == 201
    assert response.get_json() == {
        "aluno": {"id": 3, "nome": "Carol", "email": "carol@email.com"}
    }
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO tbl_alunos (nome, email) VALUES (?, ?)",
        ("Carol", "carol@email.com"),
    )
    mock_conn.commit.assert_called_once()        # ← sem commit, nada é salvo!


@patch("app.connect_db")
def test_criar_aluno_sem_nome(mock_connect_db, client):
    response = client.post("/alunos", json={"email": "x@email.com"})

    assert response.status_code == 400
    # O banco nem deveria ter sido tocado:
    mock_connect_db.assert_not_called()
```

> 🧠 Esse `assert_not_called()` no fim é ouro: ele prova que a validação
> acontece **antes** da conexão. É um teste de comportamento, não só de saída.

### 🎯 Exercício 6

1. Escreva o teste do caso `409` (email duplicado). Dica: use
   `mock_cursor.execute.side_effect = sqlite3.IntegrityError` — veremos
   `side_effect` em detalhe no Nível 8, mas já dá para usar.
2. Escreva um teste que garanta que `POST /alunos` com `{"nome": "X", "email": "semarroba"}`
   retorna 400.
3. Implemente e teste `DELETE /alunos/<int:id>`, retornando 200 se apagou e 404 se
   o id não existia. Dica: `cursor.rowcount` vale `0` quando nada foi afetado.

<details>
<summary>💡 Solução</summary>

```python
# 1
@patch("app.connect_db")
def test_criar_aluno_email_duplicado(mock_connect_db, client):
    mock_conn, mock_cursor = MagicMock(), MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = sqlite3.IntegrityError
    mock_connect_db.return_value = mock_conn

    response = client.post("/alunos", json={"nome": "Alice", "email": "alice@email.com"})

    assert response.status_code == 409
    assert response.get_json() == {"erro": "Email já cadastrado"}


# 2
def test_criar_aluno_email_invalido(client):
    response = client.post("/alunos", json={"nome": "X", "email": "semarroba"})
    assert response.status_code == 400


# 3 — rota
@app.route("/alunos/<int:id>", methods=["DELETE"])
def deletar_aluno(id):
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    cursor = conn.cursor()
    cursor.execute("DELETE FROM tbl_alunos WHERE id = ?", (id,))
    conn.commit()
    afetados = cursor.rowcount
    conn.close()

    if afetados == 0:
        return {"erro": "Aluno não encontrado"}, 404
    return {"mensagem": "Aluno removido com sucesso"}, 200


# 3 — testes
@patch("app.connect_db")
def test_deletar_aluno_ok(mock_connect_db, client):
    mock_conn, mock_cursor = MagicMock(), MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1
    mock_connect_db.return_value = mock_conn

    response = client.delete("/alunos/1")

    assert response.status_code == 200
    mock_conn.commit.assert_called_once()


@patch("app.connect_db")
def test_deletar_aluno_inexistente(mock_connect_db, client):
    mock_conn, mock_cursor = MagicMock(), MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 0
    mock_connect_db.return_value = mock_conn

    response = client.delete("/alunos/999")

    assert response.status_code == 404
```
</details>

---

## Nível 7 — `conftest.py` e `parametrize`

### Teoria: `conftest.py`

Você percebeu que está repetindo o mesmo bloco de 4 linhas de mock em todo teste. O `conftest.py` resolve isso: fixtures declaradas nele ficam **disponíveis automaticamente** em todos os testes da pasta, sem `import`.

### `tests/conftest.py`

```python
import pytest
from unittest.mock import MagicMock
from app import app as flask_app


@pytest.fixture
def client():
    """Cliente de teste da API Flask."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    """Devolve (conexão_mock, cursor_mock) já ligados entre si.

    Uso típico:
        def test_x(client, mock_db):
            conn, cursor = mock_db
            cursor.fetchall.return_value = [...]
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor
```

Agora os testes ficam bem mais limpos:

```python
from unittest.mock import patch


@patch("app.connect_db")
def test_get_alunos(mock_connect_db, client, mock_db):
    conn, cursor = mock_db
    cursor.fetchall.return_value = [(1, "Alice", "alice@email.com")]
    mock_connect_db.return_value = conn

    response = client.get("/alunos")

    assert response.status_code == 200
    assert len(response.get_json()["alunos"]) == 1
```

### Escopo das fixtures

```python
@pytest.fixture(scope="function")  # padrão: recriada a cada teste
@pytest.fixture(scope="module")    # uma vez por arquivo
@pytest.fixture(scope="session")   # uma vez por execução inteira
```

Mocks devem ser sempre `function` (o padrão) — compartilhá-los faz um teste enxergar as chamadas do outro.

### Teoria: `@pytest.mark.parametrize`

Roda o mesmo teste várias vezes com entradas diferentes. Cada linha vira um teste independente no relatório.

```python
import pytest


@pytest.mark.parametrize(
    "payload, status_esperado",
    [
        ({"nome": "Ana", "email": "ana@email.com"}, 201),   # válido
        ({"nome": "Ana"},                            400),   # falta email
        ({"email": "ana@email.com"},                 400),   # falta nome
        ({"nome": "", "email": "ana@email.com"},     400),   # nome vazio
        ({"nome": "Ana", "email": "invalido"},       400),   # email sem @
        ({},                                         400),   # vazio
    ],
)
@patch("app.connect_db")
def test_validacao_criar_aluno(mock_connect_db, client, mock_db, payload, status_esperado):
    conn, cursor = mock_db
    cursor.lastrowid = 1
    mock_connect_db.return_value = conn

    response = client.post("/alunos", json=payload)

    assert response.status_code == status_esperado
```

Saída:

```
test_app.py::test_validacao_criar_aluno[payload0-201] PASSED
test_app.py::test_validacao_criar_aluno[payload1-400] PASSED
...
```

Seis testes com o custo de escrever um.

### Marcadores úteis

```python
@pytest.mark.skip(reason="ainda não implementado")
@pytest.mark.skipif(sys.version_info < (3, 10), reason="requer 3.10+")
@pytest.mark.xfail(reason="bug conhecido #42")   # esperado falhar
```

### 🎯 Exercício 7

1. Mova a fixture `client` para o `conftest.py` e crie a `mock_db`.
2. Reescreva **todos** os testes dos níveis 5 e 6 usando `mock_db`.
3. Crie um teste parametrizado para `GET /alunos/<id>` cobrindo:
   `(id=1, encontrado=True → 200)`, `(id=999, encontrado=False → 404)`.
4. Crie um teste parametrizado que verifique que a rota `/alunos` **não** aceita
   os métodos `PUT` e `PATCH` (deve retornar 405 Method Not Allowed).

<details>
<summary>💡 Solução do item 3 e 4</summary>

```python
@pytest.mark.parametrize(
    "id_aluno, linha_retornada, status_esperado",
    [
        (1,   (1, "Alice", "alice@email.com"), 200),
        (999, None,                            404),
    ],
)
@patch("app.connect_db")
def test_get_aluno_por_id(
    mock_connect_db, client, mock_db, id_aluno, linha_retornada, status_esperado
):
    conn, cursor = mock_db
    cursor.fetchone.return_value = linha_retornada
    mock_connect_db.return_value = conn

    response = client.get(f"/alunos/{id_aluno}")

    assert response.status_code == status_esperado


@pytest.mark.parametrize("metodo", ["put", "patch"])
def test_metodos_nao_permitidos(client, metodo):
    response = getattr(client, metodo)("/alunos")
    assert response.status_code == 405
```
</details>

---

## Nível 8 — `side_effect`: simulando falhas

### Teoria

`return_value` sempre devolve a mesma coisa. `side_effect` é mais poderoso — aceita três formas:

#### 1. Uma exceção → o mock levanta ela

```python
mock_cursor.execute.side_effect = sqlite3.OperationalError("database is locked")
```

#### 2. Uma lista → devolve um item por chamada, em ordem

```python
mock_cursor.fetchone.side_effect = [(1, "Alice"), (2, "Bob"), None]

cursor.fetchone()   # (1, 'Alice')
cursor.fetchone()   # (2, 'Bob')
cursor.fetchone()   # None
cursor.fetchone()   # StopIteration!
```

Perfeito para rotas que consultam o banco mais de uma vez.

#### 3. Uma função → o retorno é calculado

```python
def fake_execute(sql, params=None):
    if "DROP" in sql:
        raise sqlite3.OperationalError("proibido")
    return None

mock_cursor.execute.side_effect = fake_execute
```

### Tornando a API resistente a falhas

Uma rota que só trata `conn is None` ainda quebra com erro 500 feio se o `execute` explodir. Vamos blindar:

```python
@app.route("/alunos", methods=["GET"])
def get_alunos():
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tbl_alunos")
        results = cursor.fetchall()
    except sqlite3.Error as err:
        app.logger.error("Erro ao consultar alunos: %s", err)
        return {"erro": "Erro ao consultar o banco de dados"}, 500
    finally:
        conn.close()

    if not results:
        return {"erro": "Nenhum aluno encontrado"}, 404

    alunos = [{"id": a[0], "nome": a[1], "email": a[2]} for a in results]
    return {"alunos": alunos}, 200
```

### O teste que prova isso

```python
@patch("app.connect_db")
def test_get_alunos_erro_no_banco(mock_connect_db, client, mock_db):
    conn, cursor = mock_db
    cursor.execute.side_effect = sqlite3.OperationalError("database is locked")
    mock_connect_db.return_value = conn

    response = client.get("/alunos")

    assert response.status_code == 500
    assert response.get_json() == {"erro": "Erro ao consultar o banco de dados"}
    conn.close.assert_called_once()   # o finally rodou mesmo com exceção
```

Sem mock você precisaria travar um banco de verdade. Com mock, é uma linha.

### Testando que uma exceção é levantada

Quando o comportamento correto é **estourar**, use `pytest.raises`:

```python
def test_init_db_sem_conexao():
    with patch("db.connect_db", return_value=None):
        with pytest.raises(RuntimeError, match="Não foi possível conectar"):
            init_db()
```

### 🎯 Exercício 8

1. Blinde a rota `POST /alunos` com `try/except sqlite3.Error` e escreva o teste
   correspondente que force um `sqlite3.OperationalError`.
2. Crie uma rota `GET /alunos/<int:id>/detalhes` que faz **duas** consultas:
   primeiro busca o aluno, depois conta suas matrículas.
   Escreva o teste usando `side_effect` como **lista** para que a primeira chamada
   de `fetchone()` devolva o aluno e a segunda devolva `(3,)`.

<details>
<summary>💡 Solução do item 2</summary>

```python
# rota
@app.route("/alunos/<int:id>/detalhes", methods=["GET"])
def detalhes_aluno(id):
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_alunos WHERE id = ?", (id,))
    aluno = cursor.fetchone()

    if aluno is None:
        conn.close()
        return {"erro": "Aluno não encontrado"}, 404

    cursor.execute("SELECT COUNT(*) FROM tbl_matriculas WHERE aluno_id = ?", (id,))
    total = cursor.fetchone()[0]
    conn.close()

    return {
        "aluno": {"id": aluno[0], "nome": aluno[1], "email": aluno[2]},
        "matriculas": total,
    }, 200


# teste
@patch("app.connect_db")
def test_detalhes_aluno(mock_connect_db, client, mock_db):
    conn, cursor = mock_db
    cursor.fetchone.side_effect = [
        (1, "Alice", "alice@email.com"),   # 1ª chamada
        (3,),                              # 2ª chamada
    ]
    mock_connect_db.return_value = conn

    response = client.get("/alunos/1/detalhes")

    assert response.status_code == 200
    assert response.get_json()["matriculas"] == 3
    assert cursor.execute.call_count == 2
```
</details>

---

## Nível 9 — Teste de integração com SQLite real (em memória)

### Teoria: quando NÃO mockar

Mock tem um ponto cego perigoso: **ele confirma que você chamou o banco do jeito que você imaginou, não que o SQL funciona.** Um `SELECT * FROM tbl_aluno` (sem o "s") passa em todos os testes mockados e explode em produção.

A solução é ter os dois tipos:

| | Teste unitário (mock) | Teste de integração (banco real) |
|---|---|---|
| Verifica | lógica da rota, status, JSON, tratamento de erro | se o SQL é válido, schema, constraints |
| Velocidade | muito rápido | rápido (SQLite) |
| Quantidade | muitos | poucos, nos caminhos principais |
| Pega erro de digitação no SQL | ❌ não | ✅ sim |

O SQLite é ideal para isso: dá para criar um banco descartável por teste.

### Fixture de banco real e descartável

Adicione ao `tests/conftest.py`:

```python
import os
import sqlite3
import pytest

SCHEMA = """
CREATE TABLE tbl_alunos (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
"""


@pytest.fixture
def banco_real(tmp_path, monkeypatch):
    """Cria um banco SQLite temporário e faz a API usá-lo.

    - tmp_path: fixture do pytest, uma pasta temporária única por teste
    - monkeypatch: substitui app.connect_db pela nossa versão
    """
    db_file = tmp_path / "teste.db"

    # Monta o schema e os dados iniciais
    conn = sqlite3.connect(db_file)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO tbl_alunos (nome, email) VALUES (?, ?)",
        [("Alice", "alice@email.com"), ("Bob", "bob@email.com")],
    )
    conn.commit()
    conn.close()

    # A API passa a conectar nesse arquivo
    def connect_temporario():
        return sqlite3.connect(db_file)

    monkeypatch.setattr("app.connect_db", connect_temporario)

    yield db_file
    # tmp_path é apagada automaticamente pelo pytest — sem limpeza manual
```

> 💡 `monkeypatch` é a fixture nativa do pytest para substituições. Ela desfaz
> tudo sozinha no fim do teste, então nunca sobra sujeira entre testes.

### Testes de integração

```python
def test_integracao_listar_alunos(client, banco_real):
    response = client.get("/alunos")

    assert response.status_code == 200
    alunos = response.get_json()["alunos"]
    assert len(alunos) == 2
    assert alunos[0]["nome"] == "Alice"


def test_integracao_criar_e_listar(client, banco_real):
    # cria
    r1 = client.post("/alunos", json={"nome": "Carol", "email": "carol@email.com"})
    assert r1.status_code == 201
    novo_id = r1.get_json()["aluno"]["id"]

    # lê de volta — prova que o commit realmente persistiu
    r2 = client.get(f"/alunos/{novo_id}")
    assert r2.status_code == 200
    assert r2.get_json()["aluno"]["nome"] == "Carol"


def test_integracao_email_duplicado(client, banco_real):
    """A constraint UNIQUE do schema é exercitada de verdade aqui."""
    response = client.post("/alunos", json={"nome": "Outra", "email": "alice@email.com"})
    assert response.status_code == 409


def test_integracao_ciclo_completo(client, banco_real):
    """Create → Read → Delete → confirma que sumiu."""
    r = client.post("/alunos", json={"nome": "Dan", "email": "dan@email.com"})
    id_dan = r.get_json()["aluno"]["id"]

    assert client.get(f"/alunos/{id_dan}").status_code == 200
    assert client.delete(f"/alunos/{id_dan}").status_code == 200
    assert client.get(f"/alunos/{id_dan}").status_code == 404
```

### Alternativa: `:memory:` compartilhado

Se quiser evitar até o arquivo temporário:

```python
conn = sqlite3.connect("file:memdb1?mode=memory&cache=shared", uri=True)
```

Todas as conexões com essa URI enxergam o **mesmo** banco em memória — mas ele só existe enquanto ao menos uma conexão estiver aberta. Por isso a fixture precisa segurar uma conexão viva durante todo o teste:

```python
@pytest.fixture
def banco_memoria(monkeypatch):
    uri = "file:memdb_teste?mode=memory&cache=shared"
    guardiao = sqlite3.connect(uri, uri=True)   # mantém o banco vivo
    guardiao.executescript(SCHEMA)
    guardiao.commit()

    monkeypatch.setattr("app.connect_db", lambda: sqlite3.connect(uri, uri=True))

    yield guardiao
    guardiao.close()   # aqui o banco deixa de existir
```

Cuidado: `sqlite3.connect(":memory:")` puro cria um banco **novo e isolado a cada chamada** — a API não veria nada do que a fixture inseriu. É a pegadinha clássica.

### Separando as duas suítes com marcadores

Crie um `pytest.ini` na raiz:

```ini
[pytest]
testpaths = tests
markers =
    integracao: testes que usam banco de dados real
```

Marque os testes:

```python
@pytest.mark.integracao
def test_integracao_listar_alunos(client, banco_real):
    ...
```

E rode seletivamente:

```bash
pytest -m "not integracao"    # só os rápidos (unitários)
pytest -m integracao          # só os de integração
pytest                        # tudo
```

### 🎯 Exercício 9

1. Implemente a fixture `banco_real` e escreva um teste de integração que prove
   que `GET /alunos` retorna **404** num banco vazio (dica: crie uma segunda
   fixture `banco_vazio` sem o `executemany`).
2. Escreva um teste de integração que crie 50 alunos num laço e confirme que
   `GET /alunos` devolve 50 itens.
3. **Desafio de detecção de bug:** troque na rota o SQL para
   `SELECT * FROM tbl_aluno` (singular, errado). Rode `pytest -m "not integracao"`
   e depois `pytest -m integracao`. Observe qual suíte pega o erro. Escreva em
   uma frase por que isso acontece.

<details>
<summary>💡 Resposta do desafio</summary>

Os testes mockados continuam passando porque o `MagicMock` aceita **qualquer** string de SQL sem validar nada — a única coisa que quebraria seria um
`assert_called_once_with` com o texto antigo. Já o teste de integração falha com
`sqlite3.OperationalError: no such table: tbl_aluno`, porque um banco de verdade
realmente interpreta a query.

Moral: mock testa **o seu código**; integração testa **o seu SQL**. Você precisa dos dois.
</details>

---

## Nível 10 — Projeto final: CRUD completo e testado

Agora você junta tudo. Este é o entregável.

### `app.py` completo

```python
import sqlite3
from flask import Flask, request
from db import connect_db

app = Flask(__name__)


# ---------------------------------------------------------------- helpers
def linha_para_dict(linha):
    """Converte uma tupla do banco em dicionário."""
    return {"id": linha[0], "nome": linha[1], "email": linha[2]}


def validar_payload(dados):
    """Retorna (nome, email, None) se válido, ou (None, None, mensagem_erro)."""
    if not dados:
        return None, None, "Corpo da requisição deve ser um JSON válido"

    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()

    if not nome or not email:
        return None, None, "Campos 'nome' e 'email' são obrigatórios"
    if "@" not in email:
        return None, None, "Email inválido"

    return nome, email, None


# ---------------------------------------------------------------- rotas
@app.route("/alunos", methods=["GET"])
def listar_alunos():
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tbl_alunos")
        results = cursor.fetchall()
    except sqlite3.Error:
        return {"erro": "Erro ao consultar o banco de dados"}, 500
    finally:
        conn.close()

    if not results:
        return {"erro": "Nenhum aluno encontrado"}, 404

    return {"alunos": [linha_para_dict(l) for l in results]}, 200


@app.route("/alunos/<int:id>", methods=["GET"])
def buscar_aluno(id):
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tbl_alunos WHERE id = ?", (id,))
        linha = cursor.fetchone()
    except sqlite3.Error:
        return {"erro": "Erro ao consultar o banco de dados"}, 500
    finally:
        conn.close()

    if linha is None:
        return {"erro": "Aluno não encontrado"}, 404

    return {"aluno": linha_para_dict(linha)}, 200


@app.route("/alunos", methods=["POST"])
def criar_aluno():
    nome, email, erro = validar_payload(request.get_json(silent=True))
    if erro:
        return {"erro": erro}, 400

    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tbl_alunos (nome, email) VALUES (?, ?)", (nome, email)
        )
        conn.commit()
        novo_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return {"erro": "Email já cadastrado"}, 409
    except sqlite3.Error:
        return {"erro": "Erro ao inserir no banco de dados"}, 500
    finally:
        conn.close()

    return {"aluno": {"id": novo_id, "nome": nome, "email": email}}, 201


@app.route("/alunos/<int:id>", methods=["PUT"])
def atualizar_aluno(id):
    nome, email, erro = validar_payload(request.get_json(silent=True))
    if erro:
        return {"erro": erro}, 400

    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tbl_alunos SET nome = ?, email = ? WHERE id = ?",
            (nome, email, id),
        )
        conn.commit()
        afetados = cursor.rowcount
    except sqlite3.IntegrityError:
        return {"erro": "Email já cadastrado"}, 409
    except sqlite3.Error:
        return {"erro": "Erro ao atualizar o banco de dados"}, 500
    finally:
        conn.close()

    if afetados == 0:
        return {"erro": "Aluno não encontrado"}, 404

    return {"aluno": {"id": id, "nome": nome, "email": email}}, 200


@app.route("/alunos/<int:id>", methods=["DELETE"])
def remover_aluno(id):
    conn = connect_db()
    if conn is None:
        return {"erro": "Erro ao conectar ao banco de dados"}, 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tbl_alunos WHERE id = ?", (id,))
        conn.commit()
        afetados = cursor.rowcount
    except sqlite3.Error:
        return {"erro": "Erro ao remover do banco de dados"}, 500
    finally:
        conn.close()

    if afetados == 0:
        return {"erro": "Aluno não encontrado"}, 404

    return {"mensagem": "Aluno removido com sucesso"}, 200


if __name__ == "__main__":
    app.run(debug=True)
```

### 🎯 Exercício 10 — o entregável

Escreva a suíte de testes completa em `tests/test_app.py` cobrindo, para **cada** rota:

- [ ] caminho feliz (200 / 201)
- [ ] recurso inexistente (404)
- [ ] payload inválido (400) — use `parametrize`
- [ ] conflito de email (409)
- [ ] falha de conexão (500, `connect_db` devolve `None`)
- [ ] erro do banco (500, `side_effect = sqlite3.Error`)
- [ ] pelo menos 4 testes marcados com `@pytest.mark.integracao` usando `banco_real`
- [ ] verificação de `commit()` em todas as rotas que escrevem
- [ ] verificação de `close()` em todas as rotas

**Meta: 90% de cobertura.**

```bash
pytest --cov=app --cov=db --cov-report=term-missing -v
```

Saída esperada mais ou menos assim:

```
---------- coverage: platform linux, python 3.12 -----------
Name     Stmts   Miss  Cover   Missing
--------------------------------------
app.py      78      5    94%   112, 130-132
db.py       22      3    86%   28-30
--------------------------------------
TOTAL      100      8    92%
```

A coluna `Missing` mostra as **linhas que nenhum teste executou**. Use ela como lista de tarefas.

Para um relatório navegável em HTML:

```bash
pytest --cov=app --cov-report=html
# abra htmlcov/index.html
```

### Extensões opcionais (se quiser ir além)

1. Adicione a tabela `tbl_cursos` e `tbl_matriculas` (N:N) e rotas com `JOIN`.
2. Adicione paginação: `GET /alunos?page=1&limit=10`.
3. Use `conn.row_factory = sqlite3.Row` e reescreva `linha_para_dict` como
   `dict(linha)` — depois ajuste os mocks (dica: agora o mock precisa devolver
   dicionários, não tuplas).
4. Adicione autenticação por token num header e teste o 401.
5. Configure GitHub Actions para rodar `pytest` a cada push.

---

## 📎 Apêndice A — Colinha de `unittest.mock`

```python
from unittest.mock import MagicMock, patch, call, ANY

# Criar
m = MagicMock()
m = MagicMock(return_value=42)              # m() → 42
m = MagicMock(spec=sqlite3.Connection)      # só aceita atributos que existem de verdade

# Configurar retorno
m.metodo.return_value = "x"                 # sempre "x"
m.metodo.side_effect = [1, 2, 3]            # 1, depois 2, depois 3
m.metodo.side_effect = ValueError("boom")   # levanta exceção
m.metodo.side_effect = lambda x: x * 2      # calcula

# Encadear
m.cursor.return_value.fetchall.return_value = [(1,)]   # m.cursor().fetchall()

# Verificar
m.metodo.assert_called()
m.metodo.assert_called_once()
m.metodo.assert_called_with("arg")
m.metodo.assert_called_once_with("arg")
m.metodo.assert_any_call("arg")             # em qualquer uma das chamadas
m.metodo.assert_not_called()
m.metodo.assert_has_calls([call("a"), call("b")])
m.metodo.call_count                          # int
m.metodo.call_args                           # última chamada
m.metodo.call_args_list                      # todas
m.reset_mock()                               # zera o histórico

# ANY: quando um argumento não importa
m.execute.assert_called_once_with("INSERT ...", ANY)

# patch
@patch("modulo.funcao")                              # vira MagicMock
@patch("modulo.funcao", return_value=42)             # já configurado
@patch.object(MinhaClasse, "metodo")
@patch.dict(os.environ, {"DB_HOST": "fake"})
with patch("modulo.funcao") as mock: ...
```

---

## 📎 Apêndice B — Colinha de `pytest`

```bash
pytest                          # roda tudo
pytest -v                       # verboso (nome de cada teste)
pytest -q                       # silencioso
pytest -x                       # para na primeira falha
pytest --maxfail=3              # para após 3 falhas
pytest -k "alunos and not post" # filtra por nome
pytest -m integracao            # filtra por marcador
pytest tests/test_app.py::test_get_alunos   # um teste específico
pytest -s                       # mostra os print()
pytest --lf                     # roda só os que falharam da última vez
pytest --ff                     # roda os que falharam primeiro
pytest --tb=short               # traceback curto
pytest --durations=5            # os 5 testes mais lentos
pytest --cov=app --cov-report=term-missing
```

```python
# Asserções úteis
assert x == y
assert item in lista
assert isinstance(x, dict)
assert set(d.keys()) == {"id", "nome", "email"}
assert resposta.get_json()["alunos"][0]["nome"] == "Alice"

with pytest.raises(ValueError):
    funcao_que_falha()

with pytest.raises(ValueError, match="mensagem esperada"):
    funcao_que_falha()

assert pytest.approx(0.1 + 0.2) == 0.3       # floats
```

---

## 📎 Apêndice C — Erros comuns e como resolver

| Sintoma | Causa provável | Correção |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | pytest rodando de outra pasta | rode da raiz do projeto; crie `pytest.ini` ou um `conftest.py` na raiz |
| O mock não é usado, a API acessa o banco real | patch no caminho errado | patcheie `"app.connect_db"`, não `"db.connect_db"` |
| `TypeError: 'MagicMock' object is not iterable` | esqueceu de configurar `fetchall.return_value` | o mock devolve outro MagicMock por padrão, não uma lista |
| `StopIteration` no meio do teste | `side_effect` com lista curta demais | acrescente mais itens à lista |
| Testes passam sozinhos mas falham juntos | estado compartilhado (fixture com escopo errado, banco real) | escopo `function`, `monkeypatch`, `tmp_path` |
| Dados sumiram após o POST no teste de integração | faltou `conn.commit()` | commit antes de fechar |
| `:memory:` "esquece" o que a fixture inseriu | cada `connect(":memory:")` cria um banco novo | use `cache=shared` com URI, ou arquivo em `tmp_path` |
| Os parâmetros do teste chegam trocados | ordem dos `@patch` | decorators de baixo para cima; fixtures por último |
| `sqlite3.ProgrammingError: ... thread` | conexão usada em outra thread | `sqlite3.connect(path, check_same_thread=False)` |

---

## 📎 Apêndice D — Roteiro de estudo sugerido

| Sessão | Faça | Tempo estimado |
|---|---|---|
| 1 | Níveis 0–2: ambiente, sqlite3, primeira rota | 1h |
| 2 | Nível 3: pytest e test client | 45min |
| 3 | Nível 4: mock isolado (o mais importante) | 1h |
| 4 | Nível 5: mock na API | 1h |
| 5 | Níveis 6–7: POST, conftest, parametrize | 1h30 |
| 6 | Nível 8: side_effect e falhas | 45min |
| 7 | Nível 9: integração | 1h |
| 8 | Nível 10: projeto final + cobertura | 2h |

---

## ✅ Checklist final de aprendizado

- [ ] Sei conectar, criar tabela e consultar com `sqlite3` usando placeholders `?`
- [ ] Sei criar rotas Flask que devolvem JSON com o status code correto
- [ ] Sei escrever uma fixture `client` e usar `client.get/post/put/delete`
- [ ] Entendo a diferença entre `mock.metodo` e `mock.metodo()`
- [ ] Sei encadear `mock_conn.cursor.return_value = mock_cursor` e explicar por quê
- [ ] Sei decidir o alvo correto do `patch` (onde é usado, não onde é definido)
- [ ] Sei usar `return_value` vs `side_effect` (exceção / lista / função)
- [ ] Sei verificar interações com `assert_called_once_with` e `call_count`
- [ ] Sei centralizar fixtures no `conftest.py`
- [ ] Sei escrever testes tabelados com `@pytest.mark.parametrize`
- [ ] Sei simular falha de conexão e erro de banco, e testar o 500
- [ ] Entendo por que testes mockados não pegam SQL errado
- [ ] Sei montar um banco SQLite descartável com `tmp_path` + `monkeypatch`
- [ ] Sei ler `--cov-report=term-missing` e usar a coluna `Missing` como TODO

Bons testes! 🚀