from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal
from agent import Agent
from fastapi.responses import StreamingResponse
import asyncio
from langchain_core.messages import HumanMessage, AIMessage

# Variável para armazenar a instância do agente
maf_agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado na inicialização
    global maf_agent_instance
    print("Inicializando o Agente MAF (isso pode levar alguns minutos na primeira vez)...")
    maf_agent_instance = Agent()
    print("Agente MAF pronto para receber requisições.")
    yield
    # Código a ser executado no desligamento (se necessário)
    print("Encerrando a aplicação.")

# Inicializa a API FastAPI com o gerenciador de ciclo de vida
app = FastAPI(
    title="MAF API",
    description="API para o My Agent Friend, um consultor de produtos com IA.",
    version="0.1.0",
    lifespan=lifespan
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

# Modelo para validar o corpo da requisição
class Message(BaseModel):
    sender: Literal["user", "bot"]
    text: str

class QuestionRequest(BaseModel):
    question: str
    history: List[Message] = Field(default_factory=list)

# Função geradora assíncrona para o streaming
async def stream_generator(question: str, history: List[Message]):
    # Converte o histórico do formato do frontend para o formato do LangChain
    chat_history = []
    for msg in history:
        if msg.sender == 'user':
            chat_history.append(HumanMessage(content=msg.text))
        else: # 'bot'
            chat_history.append(AIMessage(content=msg.text))
            
    # Chama o agente com a pergunta e o histórico convertido
    async for chunk in maf_agent_instance.ask(question, chat_history):
        yield chunk
        await asyncio.sleep(0.01) # Pequeno delay para não sobrecarregar

@app.post("/ask", summary="Faz uma pergunta ao agente com streaming")
async def ask_question(request: QuestionRequest):
    """
    Recebe uma pergunta e o histórico do chat, e retorna a resposta do agente 
    de IA em tempo real (streaming).
    """
    if not maf_agent_instance:
        raise HTTPException(status_code=503, detail="Agente não está pronto.")
    
    return StreamingResponse(
        stream_generator(request.question, request.history), 
        media_type="text/plain"
    )

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
    if not maf_agent_instance:
        raise HTTPException(status_code=503, detail="Agente não está pronto.")
    suggestions = maf_agent_instance.get_suggested_questions()
    return {"suggestions": suggestions}

if __name__ == "__main__":
    import uvicorn
    # Para rodar localmente: uvicorn main:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000) 