from fastapi import APIRouter
# Corrigindo o import para usar caminho absoluto
from app.services.movidesk import buscar_tickets

router = APIRouter()

@router.get("/tickets")
def listar_tickets():
    tickets = buscar_tickets()
    return {"tickets": tickets}
