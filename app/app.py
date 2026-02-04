import streamlit as st

from pages.cadastro import pagina_cadastro
from pages.ponto import pagina_ponto
from pages.relatorio import pagina_relatorio

st.set_page_config(page_title="Ponto com Face", page_icon="🕒", layout="centered")
st.title("🕒 Ponto eletrônico com reconhecimento facial")

aba1, aba2, aba3 = st.tabs([" Cadastrar rosto", "✅ Bater ponto", "📊 Relatório"])

with aba1:
    pagina_cadastro()

with aba2:
    pagina_ponto()

with aba3:
    pagina_relatorio()
