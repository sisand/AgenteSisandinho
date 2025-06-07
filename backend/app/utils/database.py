"""
Módulo centralizado para operações com Supabase
Contém todas as funções de acesso a dados e manipulação de entidades
"""

import logging
from datetime import datetime, timedelta
from app.core.clients import get_supabase_client  # Corrigindo a importação aqui
import os
from typing import Optional

# Configure logger com tratamento de erro
try:
    logger = logging.getLogger(__name__)
except Exception:
    # Logger à prova de falhas que não quebra o código
    class NullLogger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    logger = NullLogger()

def get_brazil_time():
    """Retorna datetime atual no fuso horário do Brasil (UTC-3)"""
    return datetime.utcnow() - timedelta(hours=3)

# Cliente Supabase
_supabase_client = None

def get_supabase_client():
    """
    Obtém o cliente do Supabase, inicializando se necessário.
    Em modo de desenvolvimento, retorna um cliente mock.
    
    Returns:
        Cliente Supabase (real ou mock)
    """
    global _supabase_client
    
    # Se já inicializado, retornar a instância existente
    if _supabase_client:
        return _supabase_client
        
    # Obter URL e chave do ambiente
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    # Validar formato da URL
    if not supabase_url.startswith("http"):
        logger.warning(f"URL do Supabase inválida: {supabase_url} - usando modo de desenvolvimento")
        from clients.mock_supabase import MockSupabaseClient
        _supabase_client = MockSupabaseClient()
        logger.info("Cliente Supabase MOCK inicializado para desenvolvimento")
        return _supabase_client
    
    try:
        # Importar biblioteca
        from supabase import create_client
        
        # Inicializar cliente
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Cliente Supabase real inicializado com sucesso")
        
        return _supabase_client
    except ImportError:
        logger.error("Biblioteca do Supabase não está instalada")
        from clients.mock_supabase import MockSupabaseClient
        _supabase_client = MockSupabaseClient()
        logger.info("Cliente Supabase MOCK inicializado (biblioteca não instalada)")
        return _supabase_client
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente Supabase: {str(e)}")
        from clients.mock_supabase import MockSupabaseClient
        _supabase_client = MockSupabaseClient()
        logger.info(f"Cliente Supabase MOCK inicializado (erro: {str(e)})")
        return _supabase_client
