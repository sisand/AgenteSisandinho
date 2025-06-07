from app.utils.database import get_supabase_client
from app.utils.time_utils import get_brazil_time
from app.utils.logger import get_logger

logger = get_logger(__name__)

def obter_ou_criar_usuario(login: str, nome: str = None) -> int:
    """
    Obtém ou cria um usuário no banco de dados.
    
    Args:
        login: Login do usuário (identificador único)
        nome: Nome do usuário (opcional)
    
    Returns:
        ID do usuário
        
    Raises:
        Exception: Se ocorrer um erro ao obter/criar usuário
    """
    try:
        supabase = get_supabase_client()
        
        # Buscar usuário existente
        result = supabase.table("usuarios").select("id").eq("login", login).limit(1).execute()
        
        # Se encontrou, retornar o ID
        if result.data:
            usuario_id = result.data[0]["id"]
            logger.info(f"Usuário existente encontrado: {login} (ID: {usuario_id})")
            return usuario_id
            
        # Caso contrário, criar novo usuário
        nome_usuario = nome or login  # Usa o login como nome se não fornecido
        
        novo_usuario = {
            "login": login,
            "nome": nome_usuario,
            "criado_em": get_brazil_time().isoformat()
        }
        
        result = supabase.table("usuarios").insert(novo_usuario).execute()
        
        if not result.data:
            raise Exception(f"Erro ao criar usuário: sem dados de retorno")
            
        novo_usuario_id = result.data[0]["id"]
        logger.info(f"Novo usuário criado: {login} (ID: {novo_usuario_id})")
        return novo_usuario_id
        
    except Exception as e:
        logger.error(f"Erro ao obter/criar usuário: {str(e)}")
        raise
