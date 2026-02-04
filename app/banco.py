import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np

def iniciar_banco(caminho_banco: str):
    Path(caminho_banco).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho_banco)
    conexao.execute("PRAGMA journal_mode=WAL;")

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            identificador TEXT,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL,
            template_blob BLOB,
            template_dim INTEGER
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS fotos_cadastro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pessoa_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            caminho_foto TEXT NOT NULL,
            FOREIGN KEY (pessoa_id) REFERENCES pessoas(id)
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS marcacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pessoa_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            data TEXT NOT NULL,
            estado TEXT NOT NULL,
            score REAL NOT NULL,
            caminho_foto TEXT NOT NULL,
            FOREIGN KEY (pessoa_id) REFERENCES pessoas(id)
        )
    """)

        # Garante: 1 marcação por dia por estado, por pessoa
    conexao.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_marcacao_unica
        ON marcacoes (pessoa_id, data, estado)
    """)


    conexao.commit()
    conexao.close()

def criar_pessoa(
        caminho_banco: str,
        nome: str,
        identificador: Optional[str],
        criado_em: str
    ) -> int:

    conexao = sqlite3.connect(caminho_banco)
    cur = conexao.cursor()
    cur.execute(
        "INSERT INTO pessoas (nome, identificador, criado_em) VALUES (?, ?, ?)",
        (nome.strip(), (identificador or "").strip() or None, criado_em),
    )
    pessoa_id = cur.lastrowid
    conexao.commit()
    conexao.close()
    return int(pessoa_id)

def atualizar_template_pessoa(caminho_banco: str, pessoa_id: int, template: np.ndarray):
    # template float32 normalizado (ex: 512 dims)
    template = template.astype(np.float32)
    blob = template.tobytes()
    dim = int(template.shape[0])

    conexao = sqlite3.connect(caminho_banco)
    conexao.execute(
        "UPDATE pessoas SET template_blob = ?, template_dim = ? WHERE id = ?",
        (sqlite3.Binary(blob), dim, pessoa_id),
    )
    conexao.commit()
    conexao.close()

def registrar_foto_cadastro(
        caminho_banco: str,
        pessoa_id: int,
        data_hora: str,
        caminho_foto: str
    ):

    conexao = sqlite3.connect(caminho_banco)
    conexao.execute(
        "INSERT INTO fotos_cadastro (pessoa_id, data_hora, caminho_foto) VALUES (?, ?, ?)",
        (pessoa_id, data_hora, caminho_foto),
    )
    conexao.commit()
    conexao.close()

def listar_pessoas(caminho_banco: str) -> List[Tuple[int, str, Optional[str], int]]:
    # id, nome, identificador, ativo
    conexao = sqlite3.connect(caminho_banco)
    cur = conexao.cursor()
    cur.execute("SELECT id, nome, identificador, ativo FROM pessoas ORDER BY nome ASC")
    rows = cur.fetchall()
    conexao.close()
    return [(int(r[0]), r[1], r[2], int(r[3])) for r in rows]

def carregar_templates_ativos(caminho_banco: str):
    """
    Retorna lista de (pessoa_id, nome, template_np)
    Apenas quem tem template cadastrado e está ativo.
    """
    conexao = sqlite3.connect(caminho_banco)
    cur = conexao.cursor()
    cur.execute("""
        SELECT id, nome, template_blob, template_dim
        FROM pessoas
        WHERE ativo = 1 AND template_blob IS NOT NULL AND template_dim IS NOT NULL
    """)
    rows = cur.fetchall()
    conexao.close()

    saida = []
    for pessoa_id, nome, blob, dim in rows:
        arr = np.frombuffer(blob, dtype=np.float32, count=int(dim))
        # garante normalizado
        arr = arr / (np.linalg.norm(arr) + 1e-9)
        saida.append((int(pessoa_id), nome, arr))
    return saida

def inserir_marcacao(
        caminho_banco: str,
        pessoa_id: int,
        data_hora: str,
        data: str,
        estado: str,
        score: float,
        caminho_foto: str
    ):
    conexao = sqlite3.connect(caminho_banco)
    try:
        conexao.execute(
            "INSERT INTO marcacoes (pessoa_id, data_hora, data, estado, score, caminho_foto) VALUES (?, ?, ?, ?, ?, ?)",
            (pessoa_id, data_hora, data, estado, score, caminho_foto),
        )
        conexao.commit()
    except sqlite3.IntegrityError as e:
        raise ValueError("Já existe uma marcação nesse estado para essa pessoa hoje.")
    finally:
        conexao.close()

def buscar_marcacoes_por_data(caminho_banco: str, data: str):
    """
    Retorna: (data_hora, estado, score, caminho_foto, pessoa_nome)
    """
    conexao = sqlite3.connect(caminho_banco)
    cur = conexao.cursor()
    cur.execute("""
        SELECT m.data_hora, m.estado, m.score, m.caminho_foto, p.nome
        FROM marcacoes m
        JOIN pessoas p ON p.id = m.pessoa_id
        WHERE m.data = ?
        ORDER BY m.data_hora ASC
    """, (data,))
    linhas = cur.fetchall()
    conexao.close()
    return linhas

def ja_existe_marcacao_no_dia(
        caminho_banco: str,
        pessoa_id: int,
        data: str,
        estado: str
    ) -> bool:

    conexao = sqlite3.connect(caminho_banco)
    cur = conexao.cursor()
    cur.execute(
        "SELECT 1 FROM marcacoes WHERE pessoa_id = ? AND data = ? AND estado = ? LIMIT 1",
        (pessoa_id, data, estado),
    )
    existe = cur.fetchone() is not None
    conexao.close()
    return existe

