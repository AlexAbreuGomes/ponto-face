# 🕒 Ponto eletrônico com reconhecimento facial

Sistema local de controle de ponto usando Python, Streamlit, SQLite e reconhecimento facial via webcam.

O sistema permite:

✅ Cadastro de pessoas com fotos do rosto
✅ Reconhecimento facial automático
✅ Registro de ponto (entrada, intervalo, volta, saída)
✅ Cálculo de horas trabalhadas
✅ Armazenamento local (sem nuvem)

Tudo roda no seu próprio computador via Docker.

---

## 📦 Tecnologias usadas

- Python 3
- Streamlit (interface web)
- SQLite (banco local)
- OpenCV + reconhecimento facial
- Docker + Docker Compose

---

## 🧑‍💻 Requisitos

Você precisa ter instalado:

- Docker
- Docker Compose

Verifique com:

```bash
docker --version
docker compose version
```

## 🚀 Como rodar o projeto

### 1 Clone o repositório:

```bash
git clone git@github.com:AlexAbreuGomes/ponto-face.git
cd ponto-face
```

### 2 Suba o sistema:

```bash
docker compose up --build
```

### 3 Acesse no navegador:

```bash
👉 http://localhost:8501
```

# 👤 Como usar
## ➕ Cadastrar pessoa

* Vá na aba Cadastrar rosto

* Digite o nome

* Clique em Iniciar cadastro

* Tire pelo menos 3 fotos do rosto

* Clique em Gerar template e salvar

## ✅ Bater ponto

* Vá na aba Bater ponto

* Escolha o estado:

* Entrada

* Intervalo (início)

* Intervalo (volta)

* Saída

* Tire a foto

* Clique em Verificar e Registrar

* O sistema reconhece automaticamente a pessoa.

## 📊 Ver relatório

### Na aba Relatório você vê:

* Horários do dia

* Total trabalhado

* Intervalo

* Avisos de ponto faltando

# 📁 Onde ficam os dados:

## Tudo fica localmente na pasta:

```bash
data/
```

## Inclui:

* Banco SQLite

* Fotos dos registros

* Fotos de cadastro

Nada é enviado para internet.

# 🔐 Privacidade:

* Dados ficam somente no seu computador
* Sem servidores externos
* Sem nuvem
