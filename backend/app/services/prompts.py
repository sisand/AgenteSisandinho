from app.core.clients import get_supabase_client
import logging

logger = logging.getLogger(__name__)


def buscar_prompt(nome: str = "padrao") -> str:
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("prompts")
            .select("nome, conteudo, descricao")
            .eq("nome", nome)
            .eq("ativo", True)
            .limit(1)
            .execute()
        )

        if result.data:
            logger.info(f"Prompt '{nome}' encontrado")
            return result.data[0]["conteudo"]

        logger.warning(f"Prompt '{nome}' não encontrado, usando fallback")
        return "Você é um assistente virtual prestativo. Responda de forma clara e objetiva."

    except Exception as e:
        logger.error(f"Erro ao buscar prompt '{nome}': {str(e)}")
        return "Erro ao buscar prompt. Responda de maneira útil e amigável."


def atualizar_prompt(nome: str, conteudo: str, descricao: str = None) -> bool:
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("prompts")
            .select("id")
            .eq("nome", nome)
            .limit(1)
            .execute()
        )

        dados = {
            "nome": nome,
            "conteudo": conteudo,
            "ativo": True
        }

        if descricao:
            dados["descricao"] = descricao

        if result.data:
            prompt_id = result.data[0]["id"]
            supabase.table("prompts").update(dados).eq("id", prompt_id).execute()
            logger.info(f"Prompt '{nome}' atualizado")
        else:
            supabase.table("prompts").insert(dados).execute()
            logger.info(f"Prompt '{nome}' criado")

        return True

    except Exception as e:
        logger.error(f"Erro ao atualizar prompt '{nome}': {str(e)}")
        return False


def listar_prompts():
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("prompts")
            .select("id, nome, conteudo, descricao, ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )

        logger.info(f"Listados {len(result.data)} prompts ativos")
        return result.data

    except Exception as e:
        logger.error(f"Erro ao listar prompts: {str(e)}")
        return []
