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
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

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
        """Configura a cadeia de recuperação de informações (RAG) com memória e busca ampla."""
        self._load_or_create_vector_store()
        retriever = self.vector_store.as_retriever(search_kwargs={'k': 20})

        # 1. Prompt para reescrever a pergunta do usuário com base no histórico
        contextualize_q_system_prompt = """Dada uma conversa e uma pergunta de acompanhamento, reformule a pergunta de acompanhamento para ser uma pergunta independente, em seu idioma original.
Combine o histórico da conversa com a pergunta de acompanhamento em uma única e completa pergunta de busca.
Não responda à pergunta, apenas a reformule.

Histórico da Conversa:
{chat_history}

Pergunta de Acompanhamento:
{input}

Pergunta Independente e Completa:"""
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # 2. Prompt final com diretivas inquebráveis para a IA
        qa_system_prompt = """### PERSONA E OBJETIVO:
Você é MAF, um consultor técnico especialista em compostos plásticos da empresa CPE. Seu único objetivo é analisar as **Fichas Técnicas** fornecidas no `CONTEXTO` para responder às perguntas dos usuários de forma precisa e direta, como um engenheiro faria.

### DIRETIVAS INQUEBRÁVEIS:

1.  **O CONTEXTO É A ÚNICA VERDADE:** Suas respostas devem ser baseadas **exclusivamente** nas Fichas Técnicas do `CONTEXTO`. Cada ficha começa com `--- INÍCIO DA FICHA TÉCNICA` e termina com `--- FIM DA FICHA TÉCNICA ---`. Se a resposta não estiver no `CONTEXTO`, você **DEVE** responder: "Não encontrei essa informação na minha base de dados."

2.  **O NOME DO PRODUTO É SAGRADO:**
    - Sua principal função é conectar os pedidos dos usuários a **NOMES DE PRODUTOS** específicos. O nome está sempre no campo `PRODUTO:` dentro de cada Ficha Técnica.
    - Se uma pergunta resultar em múltiplos produtos, liste todos eles, com seus nomes.
    - Se você encontrar um dado técnico (ex: densidade), mas não conseguir associá-lo a um `PRODUTO:` dentro da mesma Ficha Técnica, você **DEVE** responder: "Encontrei dados que correspondem à sua busca, mas não consegui identificar o nome do produto associado a eles."
    - **NUNCA, JAMAIS, EM HIPÓTESE ALGUMA,** invente nomes genéricos como "Produto 1", "Composto 2" ou "Produto com Densidade X". Isso é uma falha crítica e inaceitável.

3.  **MEMÓRIA DE CONVERSA E CONCISÃO:**
    - Use o `chat_history` para entender o contexto de perguntas de acompanhamento. Se o usuário pergunta "e qual a cor dele?", você deve olhar o histórico para saber de qual produto ele está falando e buscar essa informação na ficha técnica correspondente.
    - Não cumprimente o usuário ("Olá!", "Agradeço pela mensagem") após a primeira interação da conversa. Seja direto e eficiente.

4.  **FORMATAÇÃO:** Use tabelas HTML (`<table border="1">`) para apresentar dados.

### CONTEXTO (FICHAS TÉCNICAS DOS DOCUMENTOS):
{context}

### RESPOSTA (Siga as Diretivas Inquebráveis à risca):
"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        return create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def _load_or_create_vector_store(self):
        """
        Carrega a base de conhecimento. Se não existir, a cria a partir dos documentos.
        """
        lock = FileLock(LOCK_FILE, timeout=600)
        with lock:
            if os.path.exists(VECTOR_STORE_PATH):
                print(f"Carregando base de conhecimento de '{VECTOR_STORE_PATH}'...")
                self.vector_store = FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
            else:
                print("Nenhuma base de conhecimento encontrada. Criando uma nova...")
                from data_loader import load_documents
                
                documents = load_documents(path=DATA_PATH)
                
                # Cada documento (uma ficha inteira) é tratado como uma unidade indivisível.
                # Isso garante que o nome do produto e seus dados nunca sejam separados.
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                
                print(f"Salvando nova base de conhecimento em '{VECTOR_STORE_PATH}'...")
                self.vector_store.save_local(VECTOR_STORE_PATH)

    async def ask(self, question: str, chat_history: list):
        """
        Faz uma pergunta ao agente e retorna um gerador que transmite a resposta.
        O histórico é uma lista de mensagens HumanMessage e AIMessage.
        """
        if not self.retrieval_chain:
            yield "Erro: A cadeia de recuperação não foi inicializada."
            return
        
        # O LangChain já nos entrega o "delta" em cada chunk.
        # MODIFICADO: usa 'astream' para compatibilidade com a API assíncrona.
        async for chunk in self.retrieval_chain.astream(
            {"input": question, "chat_history": chat_history}
        ):
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
    
    # Simula um histórico para teste local
    chat_history_test = []

    print("\n--- Agente MAF Pronto ---")
    print("Faça sua pergunta ou digite 'sair' para terminar.")

    # Loop principal para teste local foi removido porque o 'ask' agora é assíncrono
    # e não pode ser chamado diretamente em um loop síncrono simples.
    # O teste deve ser feito através da API. 