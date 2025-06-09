import os
import random
from dotenv import load_dotenv
from filelock import FileLock

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Carregar variáveis de ambiente do .env
load_dotenv()

# --- Configuração ---
VECTOR_STORE_PATH = "faiss_index"
LOCK_FILE = "faiss_index.lock"
# O caminho para a pasta de documentos do cliente
# Estamos usando um caminho relativo que pressupõe uma estrutura de pastas
# ../ -> sobe um nível (de 'ia_consultant' para a raiz 'MAF')
# CPE/produtos -> desce para a pasta de dados
DATA_PATH = "../CPE/produtos" 

class Agent:
    def __init__(self):
        self.vector_store = None
        self.llm = self._get_llm_provider()
        self.embeddings = self._get_embedding_provider()
        self.retrieval_chain = self._setup_retrieval_chain()

    def _get_llm_provider(self):
        """Carrega o provedor de LLM com base na variável de ambiente."""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if provider == "google":
            print("Usando o Google como provedor de LLM.")
            return ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.3, convert_system_message_to_human=True)
        print("Usando OpenAI como provedor de LLM.")
        return ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3)

    def _get_embedding_provider(self):
        """Carrega o provedor de embeddings com base na variável de ambiente."""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if provider == "google":
            print("Usando embeddings do Google.")
            return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        print("Usando embeddings da OpenAI.")
        return OpenAIEmbeddings()

    def _setup_retrieval_chain(self):
        """Configura a cadeia de recuperação de informações (RAG)."""
        # Template do prompt para o chatbot
        prompt_template = """Você é um assistente especialista de uma empresa de compostos plásticos. Sua personalidade é prestativa e profissional.

**FLUXO DE RACIOCÍNIO E REGRAS:**

1.  **ANÁLISE INICIAL:** Primeiro, analise a pergunta do usuário.
    - Se for uma saudação simples (como "Olá", "Oi", "Bom dia"), responda de forma cordial e pergunte como pode ajudar, sem buscar no contexto.
    - Se for uma pergunta técnica, prossiga para o passo 2.

2.  **BUSCA NO CONTEXTO:** Sua principal função é responder perguntas com base **exclusivamente** no CONTEXTO de documentos técnicos fornecidos.

3.  **LÓGICA DE RESPOSTA:**
    - **SE** a resposta exata para a pergunta do usuário estiver no CONTEXTO, forneça-a de forma clara e direta.
    - **SE** a pergunta for sobre um item específico (ex: "composto XPTO-123") que **NÃO** está no CONTEXTO, **NÃO DESISTA IMEDIATAMENTE**. Em vez disso, busque no CONTEXTO por itens da mesma **categoria** ou com **propriedades similares** e ofereça-os como alternativa. (Ex: "Não tenho informações sobre o composto XPTO-123, mas temos os compostos ABC-1 e DEF-2 que também são para aplicações de alta temperatura. Algum deles te interessa?").
    - **SE** a pergunta for muito vaga ou se, após a busca por alternativas, você realmente não encontrar nada relevante no CONTEXTO, peça ao usuário para reformular a pergunta com mais detalhes. (Ex: "Não encontrei informações sobre isso. Você poderia me dar mais detalhes sobre a aplicação ou as propriedades que procura? Assim posso tentar te ajudar melhor.").
    - **FORMATAÇÃO:** Para formatar suas respostas, use sempre HTML. Use `<b>` para negrito e `<ul>` com `<li>` para listas. Ao listar produtos ou dados técnicos, **SEMPRE use uma tabela HTML** para organizar a informação.
      Exemplo de tabela: `<table border="1" style="width:100%; border-collapse: collapse;"><thead><tr><th style="text-align: left; padding: 8px;">Produto</th><th style="text-align: left; padding: 8px;">Descrição</th></tr></thead><tbody><tr><td style="padding: 8px;">Nome do Produto</td><td style="padding: 8px;">Detalhes...</td></tr></tbody></table>`.
      **NÃO USE SINTAXE MARKDOWN** (`---`, `|`, `*`).

**SINÔNIMOS E TERMOS DA EMPRESA:**
- O termo "Normas" é um sinônimo para "Especificações Automotivas".

**CONTEXTO:**
{context}

**PERGUNTA DO USUÁRIO:**
{input}

**RESPOSTA (siga o fluxo de raciocínio):**
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Carrega ou cria o Vector Store
        self._load_or_create_vector_store()

        retriever = self.vector_store.as_retriever()
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        
        return create_retrieval_chain(retriever, question_answer_chain)

    def _load_or_create_vector_store(self):
        """
        Carrega o Vector Store do disco se existir.
        Caso contrário, cria um novo a partir dos documentos, usando uma trava
        para evitar que múltiplos processos o façam ao mesmo tempo.
        """
        # Trava para garantir que apenas um processo crie o índice. Timeout de 10 min.
        lock = FileLock(LOCK_FILE, timeout=600)

        with lock:
            if os.path.exists(VECTOR_STORE_PATH):
                print(f"Carregando base de conhecimento de '{VECTOR_STORE_PATH}'...")
                self.vector_store = FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
            else:
                print("Nenhuma base de conhecimento encontrada. Criando uma nova...")
                from data_loader import load_documents
                
                # Carrega todos os documentos (locais e os previamente coletados da web)
                documents = load_documents(path=DATA_PATH)
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                split_documents = text_splitter.split_documents(documents)
                
                self.vector_store = FAISS.from_documents(split_documents, self.embeddings)
                
                print(f"Salvando nova base de conhecimento em '{VECTOR_STORE_PATH}'...")
                self.vector_store.save_local(VECTOR_STORE_PATH)

    def ask(self, question: str):
        """
        Faz uma pergunta ao agente e retorna um gerador que transmite a resposta.
        """
        if not self.retrieval_chain:
            yield "Erro: A cadeia de recuperação não foi inicializada."
            return
        
        # A forma correta de lidar com o stream é simplesmente iterar
        # sobre os 'chunks' e extrair o conteúdo de 'answer'.
        # O LangChain já nos entrega o "delta" em cada chunk.
        for chunk in self.retrieval_chain.stream({"input": question}):
            if 'answer' in chunk:
                yield chunk['answer']

    def get_suggested_questions(self):
        """Gera perguntas sugeridas com base em documentos aleatórios."""
        if not self.vector_store:
            return []

        try:
            # Pega 3 documentos aleatórios da base de dados.
            # O FAISS não tem um método "sample", então usamos uma pequena busca com k=10
            # e pegamos uma amostra aleatória dos resultados.
            retriever = self.vector_store.as_retriever(search_kwargs={'k': 10})
            all_docs = retriever.get_relevant_documents("compostos plásticos")
            
            sample_size = min(3, len(all_docs))
            if sample_size == 0: return []
            sampled_docs = random.sample(all_docs, sample_size)

            # Template do prompt para gerar perguntas
            suggestion_template = """
            Com base no trecho de documento abaixo, gere UMA única pergunta curta e direta que um cliente poderia fazer sobre o assunto.
            Retorne apenas a pergunta, sem saudações ou texto adicional.

            Documento:
            {context}

            Pergunta Sugerida:
            """
            suggestion_prompt = ChatPromptTemplate.from_template(suggestion_template)
            suggestion_chain = create_stuff_documents_chain(self.llm, suggestion_prompt)
            
            suggestions = []
            for doc in sampled_docs:
                response = suggestion_chain.invoke({"context": [doc]}) # Passa um único doc por vez
                if response:
                    suggestions.append(response.strip())
            
            return suggestions

        except Exception as e:
            print(f"Erro ao gerar perguntas sugeridas: {e}")
            return []

if __name__ == "__main__":
    # Exemplo de como usar a classe Agent
    maf_agent = Agent()

    print("\n--- Agente MAF Pronto ---")
    print("Faça sua pergunta ou digite 'sair' para terminar.")

    while True:
        user_question = input("\nVocê: ")
        if user_question.lower() == 'sair':
            break
        
        response = maf_agent.ask(user_question)
        print(f"\nMAF: {response}") 