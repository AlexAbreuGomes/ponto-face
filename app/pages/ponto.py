import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import streamlit as st

from banco import carregar_templates_ativos, inserir_marcacao, ja_existe_marcacao_no_dia
from rosto import bytes_imagem_para_rgb_np, obter_embedding, similaridade_cosseno

CAMINHO_BANCO = os.getenv("DB_PATH", "/data/ponto.db")
PASTA_FOTOS = os.getenv("PHOTOS_DIR", "/data/photos")

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

ESTADOS = {
    "Entrada": "entrada",
    "Intervalo (início)": "intervalo_inicio",
    "Intervalo (volta)": "intervalo_volta",
    "Saída": "saida",
}

def agora_brasilia():
    return datetime.now(FUSO_BRASILIA)

def salvar_foto(bytes_imagem, estado, quando):
    dia = quando.strftime("%Y-%m-%d")
    pasta = Path(PASTA_FOTOS) / dia
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{quando.strftime('%H%M%S')}_{estado}.jpg"
    caminho.write_bytes(bytes_imagem)
    return str(caminho)

def pagina_ponto():
    st.subheader("Bater ponto")

    templates = carregar_templates_ativos(CAMINHO_BANCO)

    if not templates:
        st.warning("Nenhuma pessoa cadastrada.")
        return

    rotulo = st.selectbox("Estado", list(ESTADOS.keys()))
    estado = ESTADOS[rotulo]

    foto = st.camera_input("Foto para registro")

    if st.button("Registrar", disabled=foto is None):

        agora = agora_brasilia()
        data_str = agora.date().isoformat()

        rgb = bytes_imagem_para_rgb_np(foto.getvalue())
        emb = obter_embedding(rgb)

        melhor_score = -1
        melhor_id = None
        melhor_nome = None

        for pessoa_id, nome, template in templates:
            score = similaridade_cosseno(template, emb)
            if score > melhor_score:
                melhor_score = score
                melhor_id = pessoa_id
                melhor_nome = nome

        if melhor_id is None:
            st.error("Rosto não reconhecido")
            return

        if ja_existe_marcacao_no_dia(CAMINHO_BANCO, melhor_id, data_str, estado):
            st.warning("Já registrado hoje.")
            return

        caminho = salvar_foto(foto.getvalue(), estado, agora)

        inserir_marcacao(
            CAMINHO_BANCO,
            melhor_id,
            agora.isoformat(timespec="seconds"),
            data_str,
            estado,
            melhor_score,
            caminho
        )

        st.success(f"{melhor_nome} registrado com sucesso!")
