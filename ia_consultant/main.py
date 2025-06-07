from fastapi import FastAPI
from pydantic import BaseModel
from agent import Agent

# Inicializa a API FastAPI
app = FastAPI(
    title="MAF API",
    description="API para o My Agent Friend, um consultor de produtos com IA.",
    version="0.1.0",
)

# Modelo de dados para a requisição
class QuestionRequest(BaseModel):
    question: str

# Inicializa o nosso agente de IA.
# Isso pode levar um momento na primeira vez, pois ele criará a base de conhecimento.
print("Inicializando o Agente MAF...")
maf_agent = Agent()
print("Agente MAF pronto para receber requisições.")


@app.post("/ask", summary="Faz uma pergunta ao agente")
def ask_question(request: QuestionRequest):
    """
    Recebe uma pergunta e retorna a resposta do agente de IA.
    """
    question = request.question
    response = maf_agent.ask(question)
    
    return {"answer": response.get('answer', 'Desculpe, não consegui encontrar uma resposta.')}

@app.get("/", summary="Endpoint de verificação")
def read_root():
    """
    Endpoint para verificar se a API está funcionando.
    """
    return {"message": "Bem-vindo à API do MAF (My Agent Friend)!"}

if __name__ == "__main__":
    import uvicorn
    # Para rodar localmente: uvicorn main:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000) 