from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import Agent
from fastapi.responses import StreamingResponse
import asyncio

# Inicializa a API FastAPI
app = FastAPI(
    title="MAF API",
    description="API para o My Agent Friend, um consultor de produtos com IA.",
    version="0.1.0",
)

# --- Configuração do CORS ---
# Lista de origens que podem fazer requisições para a nossa API
origins = [
    "http://localhost:3000", # Endereço do nosso frontend Next.js em desenvolvimento
    # "https://www.sitedoseucliente.com.br", # Adicione o domínio do frontend aqui!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)
# --- Fim da Configuração do CORS ---

# Modelo de dados para a requisição
class QuestionRequest(BaseModel):
    question: str

# Inicializa o nosso agente de IA.
# Isso pode levar um momento na primeira vez, pois ele criará a base de conhecimento.
print("Inicializando o Agente MAF...")
maf_agent = Agent()
print("Agente MAF pronto para receber requisições.")

# Função geradora assíncrona para o streaming
async def stream_generator(question: str):
    for chunk in maf_agent.ask(question):
        yield chunk
        await asyncio.sleep(0.01) # Pequeno delay para não sobrecarregar

@app.post("/ask", summary="Faz uma pergunta ao agente com streaming")
async def ask_question(request: QuestionRequest):
    """
    Recebe uma pergunta e retorna a resposta do agente de IA em tempo real (streaming).
    """
    question = request.question
    return StreamingResponse(stream_generator(question), media_type="text/plain")

@app.get("/", summary="Endpoint de verificação")
def read_root():
    """
    Endpoint para verificar se a API está funcionando.
    """
    return {"message": "Bem-vindo à API do MAF (My Agent Friend)!"}

@app.get("/suggest-questions", summary="Sugere perguntas com base nos documentos")
def suggest_questions():
    """
    Retorna uma lista de perguntas sugeridas geradas pela IA.
    """
    suggestions = maf_agent.get_suggested_questions()
    return {"suggestions": suggestions}

if __name__ == "__main__":
    import uvicorn
    # Para rodar localmente: uvicorn main:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000) 