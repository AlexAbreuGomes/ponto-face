import os
from pathlib import Path
from datetime import datetime, date as data_cls
from zoneinfo import ZoneInfo

import streamlit as st
import numpy as np

from banco import (
    iniciar_banco,
    criar_pessoa,
    atualizar_template_pessoa,
    registrar_foto_cadastro,
    listar_pessoas,
    carregar_templates_ativos,
    inserir_marcacao,
    buscar_marcacoes_por_data,
    ja_existe_marcacao_no_dia
)

from calculo import calcular_total_do_dia, formatar_hms
from rosto import bytes_imagem_para_rgb_np, obter_embedding, similaridade_cosseno, gerar_template_medio

CAMINHO_BANCO = os.getenv("DB_PATH", "/data/ponto.db")
PASTA_FOTOS = os.getenv("PHOTOS_DIR", "/data/photos")
LIMIAR_PADRAO = float(os.getenv("FACE_THRESHOLD", "0.50"))
PASTA_CADASTROS = os.getenv("ENROLL_DIR", "/data/cadastros")

Path(PASTA_CADASTROS).mkdir(parents=True, exist_ok=True)


ESTADOS = {
    "Entrada": "entrada",
    "Intervalo (início)": "intervalo_inicio",
    "Intervalo (volta)": "intervalo_volta",
    "Saída": "saida",
}

Path(PASTA_FOTOS).mkdir(parents=True, exist_ok=True)
iniciar_banco(CAMINHO_BANCO)

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

def agora_brasilia() -> datetime:
    return datetime.now(FUSO_BRASILIA)

def salvar_foto(bytes_imagem: bytes, estado: str, quando: datetime) -> str:
    dia = quando.strftime("%Y-%m-%d")
    horario = quando.strftime("%H%M%S")
    pasta_dia = Path(PASTA_FOTOS) / dia
    pasta_dia.mkdir(parents=True, exist_ok=True)
    caminho = pasta_dia / f"{horario}_{estado}.jpg"
    with open(caminho, "wb") as f:
        f.write(bytes_imagem)
    return str(caminho)

st.set_page_config(page_title="Ponto com Face", page_icon="🕒", layout="centered")
st.title("🕒 Ponto eletrônico com reconhecimento facial")

aba1, aba2, aba3 = st.tabs(["👤 Cadastrar rosto", "✅ Bater ponto", "📊 Relatório"])

with aba1:
    st.subheader("Cadastrar pessoa (nome + fotos + template)")

    if "pessoa_id_em_cadastro" not in st.session_state:
        st.session_state.pessoa_id_em_cadastro = None
    if "embeddings_cadastro" not in st.session_state:
        st.session_state.embeddings_cadastro = []

    colA, colB = st.columns(2)
    with colA:
        nome = st.text_input("Nome", placeholder="Ex.: Alex")
    with colB:
        identificador = st.text_input("Identificador (opcional)", placeholder="Ex.: matrícula / email")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Iniciar cadastro", type="primary", disabled=not nome.strip()):
            agora = agora_brasilia().isoformat(timespec="seconds")
            pessoa_id = criar_pessoa(CAMINHO_BANCO, nome, identificador, agora)
            st.session_state.pessoa_id_em_cadastro = pessoa_id
            st.session_state.embeddings_cadastro = []
            st.success(f"Cadastro iniciado para: {nome} (ID {pessoa_id})")

    with col2:
        if st.button("Cancelar cadastro"):
            st.session_state.pessoa_id_em_cadastro = None
            st.session_state.embeddings_cadastro = []
            st.info("Cadastro cancelado.")

    pessoa_id = st.session_state.pessoa_id_em_cadastro
    if pessoa_id is None:
        st.info("Clique em **Iniciar cadastro** para começar.")
    else:
        st.write(f"**Pessoa em cadastro:** ID {pessoa_id}")

        foto = st.camera_input("Tire uma foto (cadastro)")
        if foto is not None:
            try:
                agora = agora_brasilia()
                data_hora_iso = agora.isoformat(timespec="seconds")

                bytes_imagem = foto.getvalue()
                rgb = bytes_imagem_para_rgb_np(bytes_imagem)
                emb = obter_embedding(rgb)
                st.session_state.embeddings_cadastro.append(emb)

                # salva foto no disco
                pasta_pessoa = Path(PASTA_CADASTROS) / str(pessoa_id)
                pasta_pessoa.mkdir(parents=True, exist_ok=True)
                caminho = pasta_pessoa / f"{agora.strftime('%Y%m%d_%H%M%S')}.jpg"
                with open(caminho, "wb") as f:
                    f.write(bytes_imagem)

                # registra foto no banco
                registrar_foto_cadastro(CAMINHO_BANCO, pessoa_id, data_hora_iso, str(caminho))

                st.success(f"Foto válida! Total capturas: {len(st.session_state.embeddings_cadastro)}")
            except Exception as e:
                st.error(str(e))

        st.write("Capturas atuais:", len(st.session_state.embeddings_cadastro))

        colx, coly = st.columns(2)
        with colx:
            if st.button("Limpar capturas"):
                st.session_state.embeddings_cadastro = []
                st.info("Capturas limpas.")
        with coly:
            if st.button("Gerar template e salvar", type="primary", disabled=(len(st.session_state.embeddings_cadastro) < 3)):
                template = gerar_template_medio(st.session_state.embeddings_cadastro)
                atualizar_template_pessoa(CAMINHO_BANCO, pessoa_id, template)
                st.session_state.embeddings_cadastro = []
                st.session_state.pessoa_id_em_cadastro = None
                st.success("✅ Template salvo e cadastro finalizado.")


with aba2:
    st.subheader("Bater ponto (com verificação facial)")

    # Carrega todos os templates (pessoas ativas) do banco
    templates = carregar_templates_ativos(CAMINHO_BANCO)

    if not templates:
        st.warning("Nenhuma pessoa com template cadastrado. Vá na aba **Cadastrar pessoa** e finalize o cadastro.")
    else:
        rotulo = st.selectbox("Estado", list(ESTADOS.keys()))
        estado = ESTADOS[rotulo]

        # Limiar mais alto deixa mais rígido (recomendado depois ajustar)
        limiar = st.slider("Limiar (similaridade)", 0.30, 0.95, LIMIAR_PADRAO, 0.01)

        foto = st.camera_input("Tire a foto para registrar")

        if st.button("Verificar e Registrar", type="primary", disabled=(foto is None)):
            try:
                agora = agora_brasilia()
                data_hora_iso = agora.isoformat(timespec="seconds")
                data_str = agora.date().isoformat()


                bytes_imagem = foto.getvalue()
                rgb = bytes_imagem_para_rgb_np(bytes_imagem)
                emb = obter_embedding(rgb)

                # 1) Encontra a pessoa com maior similaridade
                melhor_score = -1.0
                melhor_pessoa_id = None
                melhor_nome = None

                for pessoa_id, nome_pessoa, template in templates:
                    score = similaridade_cosseno(template, emb)
                    if score > melhor_score:
                        melhor_score = score
                        melhor_pessoa_id = pessoa_id
                        melhor_nome = nome_pessoa

                # 2) Valida o limiar
                if melhor_score < limiar:
                    st.error(
                        f"❌ Não reconhecido. Similaridade={melhor_score:.3f} "
                        f"(mínimo={limiar:.3f})"
                    )
                else:
                    if ja_existe_marcacao_no_dia(
                        CAMINHO_BANCO,
                        melhor_pessoa_id,
                        data_str, estado
                    ):
                        st.warning(
                            f"⚠️ Já existe **{rotulo}** registrado hoje para **{melhor_nome}**."
                            f"Não é permitido registrar duas vezes."
                        )
                        st.stop()

                    # 3) Salva a foto do registro (auditável)
                    caminho_foto = salvar_foto(bytes_imagem, estado, agora)

                    # 4) Registra no banco com pessoa identificada
                    inserir_marcacao(
                        CAMINHO_BANCO,
                        melhor_pessoa_id,
                        data_hora_iso,
                        data_str,
                        estado,
                        float(melhor_score),
                        caminho_foto,
                    )

                    # 5) Mensagem final (sem mostrar score se você não quiser)
                    st.success(
                        f"✅ Registrado: **{melhor_nome}** — **{rotulo}** às **{data_hora_iso}**"
                    )
                    st.caption(f"Foto salva: {caminho_foto}")

            except Exception as e:
                st.error(str(e))


with aba3:
    st.subheader("Relatório do dia")
    dia_selecionado = st.date_input("Dia", value=data_cls.today())
    linhas = buscar_marcacoes_por_data(CAMINHO_BANCO, dia_selecionado.strftime("%Y-%m-%d"))

    if not linhas:
        st.info("Sem marcações nesse dia.")
    else:
        st.write("Marcações:")
        for data_hora, estado, score, caminho_foto, nome_pessoa in linhas:
            dt = datetime.fromisoformat(data_hora)  # já vem com -03:00, ok
            hora_formatada = dt.strftime("%H:%M:%S")
            dia_formatado = dt.strftime("%d/%m/%y")

            st.write(f"**{estado}**: {hora_formatada} — {nome_pessoa} — dia: {dia_formatado}")



        ok, dados = calcular_total_do_dia(linhas)
        st.subheader("Cálculo")
        if not ok:
            st.warning("Faltam: " + ", ".join(dados["faltando"]))
        else:
            st.write(f"**Saída - Entrada:** {formatar_hms(dados['bruto'])}")
            st.write(f"**Intervalo:** {formatar_hms(dados['intervalo'])}")
            st.success(f"**Total trabalhado:** {formatar_hms(dados['total'])}")
