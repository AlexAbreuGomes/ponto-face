import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
import numpy as np

from banco import criar_pessoa, atualizar_template_pessoa, registrar_foto_cadastro
from rosto import bytes_imagem_para_rgb_np, obter_embedding, gerar_template_medio

CAMINHO_BANCO = os.getenv("DB_PATH", "/data/ponto.db")
PASTA_CADASTROS = os.getenv("ENROLL_DIR", "/data/cadastros")

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

def agora_brasilia():
    return datetime.now(FUSO_BRASILIA)

def pagina_cadastro():
    st.subheader("Cadastrar pessoa (nome + fotos + template)")

    if "pessoa_id_em_cadastro" not in st.session_state:
        st.session_state.pessoa_id_em_cadastro = None
    if "embeddings_cadastro" not in st.session_state:
        st.session_state.embeddings_cadastro = []

    colA, colB = st.columns(2)
    with colA:
        nome = st.text_input("Nome")
    with colB:
        identificador = st.text_input("Identificador (opcional)")

    if st.button("Iniciar cadastro", type="primary", disabled=not nome.strip()):
        agora = agora_brasilia().isoformat(timespec="seconds")
        pessoa_id = criar_pessoa(CAMINHO_BANCO, nome, identificador, agora)
        st.session_state.pessoa_id_em_cadastro = pessoa_id
        st.session_state.embeddings_cadastro = []
        st.success(f"Cadastro iniciado para {nome}")

    pessoa_id = st.session_state.pessoa_id_em_cadastro

    if pessoa_id is None:
        st.info("Inicie o cadastro para capturar fotos.")
        return

    foto = st.camera_input("Tire a foto para cadastro")

    if foto:
        agora = agora_brasilia()
        bytes_imagem = foto.getvalue()
        rgb = bytes_imagem_para_rgb_np(bytes_imagem)
        emb = obter_embedding(rgb)

        st.session_state.embeddings_cadastro.append(emb)

        pasta = Path(PASTA_CADASTROS) / str(pessoa_id)
        pasta.mkdir(parents=True, exist_ok=True)

        caminho = pasta / f"{agora.strftime('%Y%m%d_%H%M%S')}.jpg"
        caminho.write_bytes(bytes_imagem)

        registrar_foto_cadastro(
            CAMINHO_BANCO,
            pessoa_id,
            agora.isoformat(timespec="seconds"),
            str(caminho)
        )

        st.success(f"Foto salva ({len(st.session_state.embeddings_cadastro)})")

    if st.button("Gerar template", disabled=len(st.session_state.embeddings_cadastro) < 3):
        template = gerar_template_medio(st.session_state.embeddings_cadastro)
        atualizar_template_pessoa(CAMINHO_BANCO, pessoa_id, template)
        st.session_state.pessoa_id_em_cadastro = None
        st.session_state.embeddings_cadastro = []
        st.success("Template criado com sucesso!")
