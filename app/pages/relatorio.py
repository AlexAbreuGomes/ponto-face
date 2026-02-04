import os
import streamlit as st

from datetime import datetime, date as data_cls

from banco import buscar_marcacoes_por_data
from calculo import calcular_total_do_dia, formatar_hms

CAMINHO_BANCO = os.getenv("DB_PATH", "/data/ponto.db")

def pagina_relatorio():
    st.subheader("Relatório do dia")

    dia = st.date_input("Dia", value=data_cls.today())
    linhas = buscar_marcacoes_por_data(CAMINHO_BANCO, dia.isoformat())

    if not linhas:
        st.info("Sem marcações.")
        return

    for data_hora, estado, score, caminho_foto, nome in linhas:
        dt = datetime.fromisoformat(data_hora)
        st.write(f"**{estado}**: {dt.strftime('%H:%M:%S')} — {nome} — dia {dt.strftime('%d/%m/%y')}")

    ok, dados = calcular_total_do_dia(linhas)

    if not ok:
        st.warning("Faltam batidas.")
    else:
        st.success(f"Total: {formatar_hms(dados['total'])}")
