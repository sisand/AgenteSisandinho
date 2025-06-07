from app.utils.database import get_supabase_client
from app.utils.logger import get_logger
from app.utils.time_utils import get_brazil_time
from typing import List, Dict, Any, Optional, Union
import asyncio
import time

logger = get_logger(__name__)

async def salvar_mensagem(
    pergunta: str, 
    resposta: str, 
    usuario_id: Optional[int] = None,
    sessao_id: Optional[int] = None,
    prompt_usado: Optional[str] = None,
    classificacao: Optional[str] = None,
    tipo_resposta: str = 'ia'
) -> Optional[Dict[str, Any]]:
    """
    Salva uma mensagem de usuário e sua resposta no banco de dados.
    Adaptado para lidar com diferentes estruturas de schema.
    
    Args:
        pergunta: Mensagem do usuário
        resposta: Resposta do sistema
        usuario_id: ID do usuário (opcional)
        sessao_id: ID da sessão (opcional)
        prompt_usado: Prompt utilizado para gerar a resposta
        classificacao: Classificação da pergunta/resposta
        tipo_resposta: Tipo de resposta (ia, humana, etc.)
        
    Returns:
        Mensagem salva ou None em caso de erro
    """
    try:
        supabase = get_supabase_client()
        
        # Se não recebeu sessao_id e tem usuario_id, tenta obter/criar sessão
        if sessao_id is None and usuario_id is not None:
            try:
                from app.services.sessoes import obter_ou_criar_sessao
                # Importante: await a chamada assíncrona
                sessao_id = await obter_ou_criar_sessao(usuario_id)
                logger.info(f"Sessão {sessao_id} obtida/criada para usuário {usuario_id}")
            except Exception as e:
                logger.error(f"❌ Erro ao obter/criar sessão: {str(e)}")
                # Prosseguir sem sessão
        
        # Verificar a estrutura da tabela antes de tentar inserir
        try:
            # Consulta para obter informações da tabela
            schema_info = supabase.table("mensagens").select("*").limit(1).execute()
            
            # Verificar quais colunas existem baseado no retorno
            if schema_info.data:
                columns = schema_info.data[0].keys()
                logger.info(f"Colunas encontradas: {', '.join(columns)}")
            else:
                # Tentar obter descrição da tabela via função RPC (se disponível)
                try:
                    table_desc = supabase.rpc("get_table_columns", {"table_name": "mensagens"}).execute()
                    if table_desc.data:
                        columns = [col["column_name"] for col in table_desc.data]
                        logger.info(f"Colunas obtidas via RPC: {', '.join(columns)}")
                    else:
                        # Usar nomes de colunas mais comuns como fallback
                        columns = ["pergunta", "resposta", "usuario_id", "sessao_id", "created_at"]
                except Exception:
                    # Estrutura baseada no código existente e logs de erro
                    columns = ["pergunta", "resposta", "usuario_id", "sessao_id", "created_at"]
                    
                logger.info(f"Usando estrutura inferida: {', '.join(columns)}")
        except Exception as e:
            # Em caso de erro, usar estrutura baseada nos logs de erro
            columns = ["pergunta", "resposta", "usuario_id", "sessao_id", "created_at"]
            logger.warning(f"Erro ao verificar estrutura da tabela: {str(e)}")
        
        # Validação e conversão de tipos para evitar erros de tipo
        if usuario_id is not None:
            try:
                # Garantir que usuario_id seja int se a coluna espera int
                if isinstance(usuario_id, int) and usuario_id.isdigit():
                    usuario_id = int(usuario_id)
            except (ValueError, TypeError):
                logger.warning(f"Não foi possível converter usuario_id '{usuario_id}' para inteiro")
        
        if sessao_id is not None:
            try:
                # Garantir que sessao_id seja int
                if not isinstance(sessao_id, int):
                    sessao_id = int(sessao_id)
            except (ValueError, TypeError):
                logger.warning(f"Não foi possível converter sessao_id '{sessao_id}' para inteiro")
                # Se não conseguir converter, é melhor não incluir
                sessao_id = None
        
        # Preparar dados para inserção baseado nas colunas existentes
        dados = {}
        
        # Verificação de segurança: garantir que os valores são dos tipos adequados
        if not isinstance(pergunta, str) or not isinstance(resposta, str):
            logger.error(f"❌ Tipos inválidos: pergunta ({type(pergunta).__name__}), resposta ({type(resposta).__name__})")
            pergunta = str(pergunta) if pergunta is not None else "Sem pergunta"
            resposta = str(resposta) if resposta is not None else "Sem resposta"
        
        # Mapear campos comuns com verificação
        field_mapping = {
            "pergunta": pergunta,
            "texto": pergunta,  # Compatibilidade com versões antigas
            "resposta": resposta,
            "usuario_id": usuario_id,
            "sessao_id": sessao_id,
            "prompt_usado": prompt_usado,
            "classificacao_huggingface": classificacao,
            "tipo_resposta": tipo_resposta
        }
        
        # Adicionar apenas campos existentes no schema
        for column_name, value in field_mapping.items():
            if column_name in columns and value is not None:
                dados[column_name] = value
        
        # Log do payload para debug antes da inserção
        logger.debug(f"Preparando para inserir: {dados}")
            
        # Inserir dados
        result = supabase.table("mensagens").insert(dados).execute()
        
        if not result.data:
            logger.error("Erro ao salvar mensagem: sem dados retornados")
            return None
            
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar mensagem: {str(e)}")
        return None

def buscar_mensagens_sessao(sessao_id: int) -> List[Dict[str, Any]]:
    """
    Busca todas as mensagens de uma sessão.
    
    Args:
        sessao_id: ID da sessão
        
    Returns:
        Lista de mensagens ou lista vazia em caso de erro
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar primeiro quais colunas estão disponíveis
        try:
            schema_info = supabase.table("mensagens").select("*").limit(1).execute()
            available_columns = schema_info.data[0].keys() if schema_info.data else []
            
            # Determinar quais colunas selecionar
            select_columns = []
            for col in ["id", "pergunta", "texto", "resposta", "created_at", "metadados"]:
                if col in available_columns:
                    select_columns.append(col)
                    
            select_str = ", ".join(select_columns) if select_columns else "*"
        except Exception:
            # Em caso de erro, usar select genérico
            select_str = "*"
        
        result = (
            supabase.table("mensagens")
            .select(select_str)
            .eq("sessao_id", sessao_id)
            .order("created_at")
            .execute()
        )
        
        logger.info(f"Carregadas {len(result.data)} mensagens da sessão {sessao_id}")
        return result.data
    
    except Exception as e:
        logger.error(f"❌ Erro ao buscar mensagens da sessão {sessao_id}: {str(e)}")
        return []
