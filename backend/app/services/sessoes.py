# services/sessoes.py

"""
Módulo de Serviços para Gerenciamento de Sessões
Contém a lógica de negócios relacionada às sessões de usuário
"""

from app.utils.database import get_supabase_client
from app.utils.logger import get_logger
from app.utils.time_utils import get_brazil_time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
import uuid
from app.utils.time_utils import parse_isoformat_safe


# Configurar logger
logger = get_logger(__name__)

# Constantes de configuração
SESSAO_TIMEOUT_MINUTOS = 30

async def obter_ou_criar_sessao(
    usuario_id: Union[int], 
    criar_nova: bool = False
) -> int:
    """
    Obtém a sessão ativa do usuário ou cria uma nova.
    
    Args:
        usuario_id: ID do usuário
        criar_nova: Se True, sempre cria uma nova sessão
        
    Returns:
        ID da sessão
        
    Raises:
        Exception: Se não for possível obter ou criar uma sessão
    """
    try:
        supabase = get_supabase_client()
        
        # Garantir que usuario_id seja do tipo correto
        user_id = usuario_id
        if isinstance(usuario_id, str) and usuario_id.isdigit():
            user_id = int(usuario_id)
        
        if not criar_nova:
            # Verificar se existe sessão ativa
            limite_tempo = datetime.utcnow() - timedelta(minutes=SESSAO_TIMEOUT_MINUTOS)
            limite_tempo_iso = limite_tempo.isoformat()
            
            # Modificado para usar created_at em vez de updated_at
            result = (supabase.table("sessoes")
                     .select("id")
                     .eq("usuario_id", user_id)
                     .gt("created_at", limite_tempo_iso)  # Usando created_at em vez de updated_at
                     .order("created_at", desc=True)      # Usando created_at em vez de updated_at
                     .limit(1)
                     .execute())
            
            if result.data:
                sessao_id = result.data[0]["id"]
                logger.info(f"Sessão existente {sessao_id} ainda válida para usuário {user_id}")
                
                # Não tentamos atualizar updated_at, já que não existe
                return sessao_id
        
        # Se não encontrou ou quer criar nova
        # Verificar a estrutura da tabela antes da inserção
        try:
            # Consulta para obter informações da tabela
            schema_info = supabase.table("sessoes").select("*").limit(1).execute()
            
            # Verificar quais colunas existem baseado no retorno
            columns = []
            if schema_info.data:
                columns = list(schema_info.data[0].keys())
                logger.info(f"Colunas encontradas na tabela sessoes: {', '.join(columns)}")
        except Exception as e:
            # Em caso de erro, usar estrutura conhecida
            columns = ["id", "usuario_id", "created_at"]
            logger.warning(f"Erro ao verificar estrutura da tabela: {str(e)}")
        
        # Preparar dados para inserção baseado nas colunas existentes
        dados = {"usuario_id": user_id}
        
        # Adicionar outras colunas se existirem
        if "inicio" in columns:
            dados["inicio"] = datetime.utcnow().isoformat()
        if "ultima_atividade" in columns:
            dados["ultima_atividade"] = datetime.utcnow().isoformat()
        if "ativa" in columns:
            dados["ativa"] = True
                
        result = supabase.table("sessoes").insert(dados).execute()
        
        if result.data:
            nova_sessao_id = result.data[0]["id"]
            logger.info(f"Nova sessão {nova_sessao_id} criada para usuário {user_id}")
            return nova_sessao_id
        else:
            logger.error("Erro ao criar sessão - sem dados retornados")
            raise Exception("Não foi possível criar uma nova sessão no banco de dados")
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter/criar sessão: {str(e)}")
        raise  # Re-lança a exceção para tratamento adequado na camada superior

async def atualizar_ultima_atividade(sessao_id: int) -> bool:
    """
    Atualiza o timestamp de última atividade de uma sessão.
    
    Args:
        sessao_id: ID da sessão a ser atualizada
        
    Returns:
        True se atualizado com sucesso, False se falhou
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar a estrutura da tabela antes da inserção
        try:
            # Consulta para obter informações da tabela
            schema_info = supabase.table("sessoes").select("*").limit(1).execute()
            
            # Verificar quais colunas existem baseado no retorno
            columns = []
            if schema_info.data:
                columns = list(schema_info.data[0].keys())
        except Exception:
            # Em caso de erro, usar estrutura conhecida
            columns = ["id", "usuario_id", "created_at"]
        
        # Obter data/hora atual em formato ISO 8601
        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        
        # Preparar dados para atualização conforme colunas disponíveis
        update_data = {}
        
        # Usar colunas disponíveis
        if "ultima_atividade" in columns:
            update_data["ultima_atividade"] = now_iso
            
        # Se não houver colunas para atualizar, não faz nada
        if not update_data:
            logger.warning(f"Nenhuma coluna apropriada para atualizar na tabela sessoes")
            return True
            
        # Atualizar campos
        result = supabase.table("sessoes").update(update_data).eq("id", sessao_id).execute()
        
        if result.data:
            logger.info(f"Última atividade da sessão {sessao_id} atualizada para {now_iso}")
            return True
        else:
            logger.warning(f"Nenhum registro atualizado para sessão {sessao_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar última atividade da sessão {sessao_id}: {str(e)}")
        return False

def obter_detalhes_sessao(sessao_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtém detalhes de uma sessão específica.
    """
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("sessoes")
            .select("*")
            .eq("id", sessao_id)
            .limit(1)
            .execute()
        )

        if not result.data:
            logger.warning(f"Sessão {sessao_id} não encontrada")
            return None

        sessao = result.data[0]

        # Lista dos campos de data que precisam ser tratados
        campos_data = ["created_at", "inicio", "ultima_atividade", "fim"]

        for campo in campos_data:
            if campo in sessao and sessao[campo]:
                try:
                    dt = parse_isoformat_safe(sessao[campo].replace('Z', '+00:00'))
                    sessao[campo] = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    sessao[f'{campo}_formatted'] = dt.strftime('%d/%m/%Y %H:%M:%S')
                except Exception as e:
                    logger.warning(f"Erro ao processar campo {campo} da sessão {sessao_id}: {e}")
                    now = datetime.now()
                    sessao[campo] = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    sessao[f'{campo}_formatted'] = now.strftime('%d/%m/%Y %H:%M:%S')

        logger.info(f"Detalhes da sessão {sessao_id} obtidos com sucesso")
        return sessao

    except Exception as e:
        logger.error(f"❌ Erro ao obter detalhes da sessão {sessao_id}: {str(e)}")
        return None

def encerrar_sessao(sessao_id: int) -> bool:
    """
    Encerra uma sessão de usuário.
    
    Args:
        sessao_id: ID da sessão
        
    Returns:
        True se bem-sucedido, False caso contrário
    """
    try:
        supabase = get_supabase_client()
        
        # Usar formato ISO 8601 com timezone
        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        
        # Atualizar múltiplos campos de uma vez
        result = supabase.table("sessoes").update({
            "fim": now_iso,
            "ativa": False,
            "updated_at": now_iso
        }).eq("id", sessao_id).execute()
        
        success = bool(result.data)
        if success:
            logger.info(f"Sessão {sessao_id} encerrada com sucesso")
        else:
            logger.warning(f"Não foi possível encerrar sessão {sessao_id}")
        
        return success
    
    except Exception as e:
        logger.error(f"❌ Erro ao encerrar sessão {sessao_id}: {str(e)}")
        return False

def encerrar_sessao_antiga(sessao_id: int) -> bool:
    """
    Encerra uma sessão preenchendo o campo 'fim'.
    Mantida para compatibilidade com código existente.
    
    Args:
        sessao_id: ID da sessão
        
    Returns:
        True se bem-sucedido, False caso contrário
    """
    try:
        supabase = get_supabase_client()
        
        # Usar formato ISO 8601 com timezone
        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        
        # Atualizar campo 'fim' com data/hora atual
        supabase.table("sessoes").update({
            "fim": now_iso
        }).eq("id", sessao_id).execute()
        
        logger.info(f"Sessão {sessao_id} encerrada com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao encerrar sessão {sessao_id}: {str(e)}")
        return False


def listar_sessoes_usuario(usuario_id: int, incluir_inativas: bool = False) -> List[Dict[str, Any]]:
    """
    Lista todas as sessões de um usuário.
    
    Args:
        usuario_id: ID do usuário
        incluir_inativas: Se deve incluir sessões encerradas
        
    Returns:
        Lista de sessões ou lista vazia em caso de erro
    """
    try:
        supabase = get_supabase_client()
        
        query = (
            supabase.table("sessoes")
            .select("id, inicio, ultima_atividade, fim, created_at")
            .eq("usuario_id", usuario_id)
        )
        
        if not incluir_inativas:
            query = query.is_("fim", "null")  # Apenas sessões não encerradas
            
        result = query.order("created_at", desc=True).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar sessões do usuário {usuario_id}: {str(e)}")
        return []