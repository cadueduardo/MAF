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
        """Configura a cadeia de recuperação de informações (RAG) com memória de conversa."""
        self._load_or_create_vector_store()
        retriever = self.vector_store.as_retriever(search_kwargs={'k': 5})

        # 1. Prompt para reescrever a pergunta do usuário com base no histórico
        contextualize_q_system_prompt = """Dada uma conversa e uma pergunta de acompanhamento, reformule a pergunta de acompanhamento para ser uma pergunta independente, em seu idioma original.
Se a pergunta de acompanhamento não estiver relacionada ao histórico, use-a como está.
Não responda à pergunta, apenas reformule-a se necessário.

Histórico da Conversa:
{chat_history}

Pergunta de Acompanhamento:
{input}

Pergunta Independente:"""
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

        # 2. Prompt para responder à pergunta com base no contexto recuperado
        qa_system_prompt = """### PERSONA:
Você é MAF, um consultor técnico especialista em compostos plásticos. Sua comunicação é profissional, precisa e direta. Você ajuda os clientes a encontrar os produtos certos para suas necessidades, usando os dados técnicos fornecidos.

### DIRETIVAS PRINCIPAIS:

1.  **NOME DO PRODUTO É PRIORIDADE ABSOLUTA:** Sua função principal é conectar as perguntas dos usuários a **NOMES DE PRODUTOS** específicos.
    - Ao listar propriedades em uma tabela, a primeira coluna **DEVE** ser o nome do `PRODUTO`.
    - Se os documentos de `CONTEXTO` fornecerem dados técnicos, mas você não conseguir associá-los a um nome de produto específico e inequívoco, você **DEVE** responder: "Encontrei dados que correspondem à sua busca, mas não consegui identificar o nome do produto associado a eles."
    - **NUNCA** invente nomes genéricos como "Produto com densidade 1.23" ou "Composto 1".

2.  **ANÁLISE DE CONVERSA CONTÍNUA:**
    - Antes de cada resposta, analise o `chat_history` para entender o contexto.
    - Se a pergunta do usuário for um acompanhamento (ex: "e qual a cor dele?", "e o teor?"), identifique o produto discutido anteriormente no histórico e responda sobre **esse produto**.
    - **NÃO** cumprimente o usuário ("Olá!", "Agradeço pela mensagem") após a primeira interação da conversa. Vá direto ao ponto.

3.  **FORMATAÇÃO E PRECISÃO:**
    - Use tabelas HTML (`<table border="1">...</table>`) para apresentar dados.
    - Responda apenas com base nas informações encontradas no `CONTEXTO` dos documentos técnicos.
    - Se o `CONTEXTO` não contiver a resposta, informe que não possui essa informação em sua base de dados.

4.  **SINÔNIMOS:** Lembre-se que "Normas" é um sinônimo para "Especificações Automotivas".

### CONTEXTO DOS DOCUMENTOS TÉCNICOS:
{context}

### RESPOSTA (Siga as Diretivas Principais à risca):
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
                
                # Agora carrega tanto dos arquivos locais quanto do site
                documents = load_documents(path=DATA_PATH)
                
                # AUMENTADO: Chunks maiores e com mais sobreposição para manter o contexto (nome do produto + dados)
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
                split_documents = text_splitter.split_documents(documents)
                
                self.vector_store = FAISS.from_documents(split_documents, self.embeddings)
                
                print(f"Salvando nova base de conhecimento em '{VECTOR_STORE_PATH}'...")
                self.vector_store.save_local(VECTOR_STORE_PATH)

    def ask(self, question: str, chat_history: list):
        """
        Faz uma pergunta ao agente e retorna um gerador que transmite a resposta.
        O histórico é uma lista de mensagens HumanMessage e AIMessage.
        """
        if not self.retrieval_chain:
            yield "Erro: A cadeia de recuperação não foi inicializada."
            return
        
        # O LangChain já nos entrega o "delta" em cada chunk.
        for chunk in self.retrieval_chain.stream(
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

    while True:
        user_question = input("\nVocê: ")
        if user_question.lower() == 'sair':
            break
        
        full_response = ""
        # Itera sobre o gerador para obter a resposta completa
        for part in maf_agent.ask(user_question, chat_history_test):
            print(part, end="", flush=True)
            full_response += part
        
        # Adiciona a pergunta e a resposta completa ao histórico de teste
        chat_history_test.append(HumanMessage(content=user_question))
        chat_history_test.append(AIMessage(content=full_response))
        
        print() # Nova linha para a próxima pergunta 