import os
from dotenv import load_dotenv

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
            return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, convert_system_message_to_human=True)
        print("Usando OpenAI como provedor de LLM.")
        return ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)

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
        prompt_template = """
        Você é o MAF (My Agent Friend), um assistente especialista nos produtos da empresa.
        Sua principal função é responder perguntas com base no contexto fornecido.
        Seja amigável, prestativo e forneça respostas detalhadas e precisas.
        Se a resposta não estiver no contexto, diga que você não tem essa informação,
        mas que pode ajudar com outras questões sobre os produtos.

        Contexto:
        {context}

        Pergunta: {input}
        Resposta:
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
        Caso contrário, cria um novo a partir dos documentos.
        """
        if os.path.exists(VECTOR_STORE_PATH):
            print(f"Carregando base de conhecimento de '{VECTOR_STORE_PATH}'...")
            self.vector_store = FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
        else:
            print("Nenhuma base de conhecimento encontrada. Criando uma nova...")
            from data_loader import load_documents
            
            documents = load_documents(DATA_PATH)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            split_documents = text_splitter.split_documents(documents)
            
            self.vector_store = FAISS.from_documents(split_documents, self.embeddings)
            
            print(f"Salvando nova base de conhecimento em '{VECTOR_STORE_PATH}'...")
            self.vector_store.save_local(VECTOR_STORE_PATH)

    def ask(self, question: str):
        """Faz uma pergunta ao agente."""
        if not self.retrieval_chain:
            return {"error": "A cadeia de recuperação não foi inicializada."}
        
        response = self.retrieval_chain.invoke({"input": question})
        return response

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
        print(f"\nMAF: {response.get('answer', 'Não consegui processar sua pergunta.')}") 