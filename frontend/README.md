# Frontend - Sisandinho

## 🏗️ Arquitetura
- `pages/`: Telas e funcionalidades do Streamlit.
- `services/`: Comunicação com backend (API).
- `components/`: Componentes reutilizáveis (ex.: chat Sisandinho).
- `app.py`: Arquivo principal da aplicação.

## 🚀 Como rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🐳 Como rodar via Docker
```bash
docker build -t frontend-sisand .
docker run -p 8501:8501 frontend-sisand
```

## ⚙️ Configuração
Preencha seu arquivo `.env` baseado no `.env.example`:

```bash
API_URL=http://localhost:8000
```

## 🔗 Backend
O frontend se comunica via API REST com o backend (FastAPI).