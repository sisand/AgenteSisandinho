"""
Script para iniciar o backend com configurações específicas
"""
import uvicorn
import os
from pathlib import Path

# Configurar diretórios a serem observados apenas dentro do backend
backend_dir = Path(__file__).parent
app_dir = backend_dir / "app"

if __name__ == "__main__":
    # Iniciar servidor com reload apenas em arquivos do backend
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        reload_dirs=[str(app_dir)],  # Apenas observar diretório app
        reload_excludes=["*frontend*", "*venv*", "*.git*"]  # Excluir diretórios problemáticos
    )
