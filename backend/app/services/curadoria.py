"""
Sistema de curadoria de conteúdo.
Permite a revisão, aprovação e melhoria de conteúdos para a base de conhecimento.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.utils.logger import get_logger
from app.core.clients import get_supabase_client
from app.utils.time_utils import get_brazil_time

logger = get_logger(__name__)

async def salvar_curadoria(
    ticket_id: str, 
    curador: str, 
    pergunta: str, 
    resposta: str,
    metadados: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Salva uma curadoria de ticket no banco de dados.
    
    Args:
        ticket_id: ID do ticket no Movidesk
        curador: Nome do curador
        pergunta: Pergunta do cliente
        resposta: Resposta curada
        metadados: Dados adicionais (opcional)
        
    Returns:
        Status da operação
    """
    try:
        supabase = get_supabase_client()
        
        # Dados para inserção
        dados = {
            "ticket_id": ticket_id,
            "curador": curador,
            "pergunta": pergunta,
            "resposta": resposta,
            "data_curadoria": get_brazil_time().isoformat(),
            "status": "aprovado"
        }
        
        # Adicionar metadados se fornecidos
        if metadados:
            dados["metadados"] = metadados
            
        # Inserir no Supabase
        result = supabase.table("curadorias").insert(dados).execute()
        
        if not result.data:
            raise Exception("Erro ao salvar curadoria: sem dados de retorno")
            
        curadoria_id = result.data[0]["id"]
        
        logger.info(f"Curadoria do ticket {ticket_id} salva com sucesso (ID: {curadoria_id})")
        return {"status": "success", "id": curadoria_id}
        
    except Exception as e:
        logger.error(f"Erro ao salvar curadoria para ticket {ticket_id}: {str(e)}")
        return {"error": str(e), "status": "error"}
        
async def listar_curadorias(
    status: Optional[str] = None,
    curador: Optional[str] = None,
    limite: int = 50
) -> List[Dict[str, Any]]:
    """
    Lista curadorias existentes com opção de filtro.
    
    Args:
        status: Filtro por status (opcional)
        curador: Filtro por curador (opcional)
        limite: Número máximo de resultados
        
    Returns:
        Lista de curadorias
    """
    try:
        supabase = get_supabase_client()
        
        # Construir consulta
        query = (
            supabase.table("curadorias")
            .select("id, ticket_id, curador, pergunta, resposta, data_curadoria, status")
            .order("data_curadoria", desc=True)
            .limit(limite)
        )
        
        # Adicionar filtros
        if status:
            query = query.eq("status", status)
            
        if curador:
            query = query.eq("curador", curador)
            
        # Executar consulta
        result = query.execute()
        
        logger.info(f"Listadas {len(result.data)} curadorias")
        return result.data
        
    except Exception as e:
        logger.error(f"Erro ao listar curadorias: {str(e)}")
        return []
        
async def avaliar_curadoria(
    curadoria_id: int,
    avaliacao: str,
    comentario: Optional[str] = None
) -> Dict[str, Any]:
    """
    Avalia uma curadoria existente.
    
    Args:
        curadoria_id: ID da curadoria
        avaliacao: Avaliação (aprovado/rejeitado)
        comentario: Comentário opcional
        
    Returns:
        Status da operação
    """
    try:
        supabase = get_supabase_client()
        
        # Validar avaliação
        if avaliacao not in ["aprovado", "rejeitado"]:
            return {"error": "Avaliação inválida. Use 'aprovado' ou 'rejeitado'", "status": "error"}
            
        # Dados para atualização
        dados = {
            "status": avaliacao,
            "data_avaliacao": get_brazil_time().isoformat()
        }
        
        if comentario:
            dados["comentario_avaliacao"] = comentario
            
        # Atualizar no Supabase
        result = supabase.table("curadorias").update(dados).eq("id", curadoria_id).execute()
        
        if not result.data:
            raise Exception(f"Curadoria {curadoria_id} não encontrada")
            
        logger.info(f"Curadoria {curadoria_id} avaliada como '{avaliacao}'")
        return {"status": "success", "id": curadoria_id}
        
    except Exception as e:
        logger.error(f"Erro ao avaliar curadoria {curadoria_id}: {str(e)}")
        return {"error": str(e), "status": "error"}
