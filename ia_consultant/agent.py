import os
import random
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
        prompt_template = """
        Você é o MAF (My Agent Friend), um assistente especialista nos produtos da empresa.
        Sua personalidade é amigável, prestativa e um pouco informal, como um colega de trabalho experiente.
        Sua principal função é responder perguntas com base no contexto técnico fornecido, mas traduzindo a informação para uma linguagem mais humana e fácil de entender.
        
        **Instruções de Formatação:**
        - Para respostas que tenham mais de uma ideia principal, separe-as em parágrafos curtos para facilitar a leitura. Use uma linha em branco (duas quebras de linha) entre os parágrafos.
        - Use analogias ou exemplos simples quando apropriado.
        
        Seja sempre cordial. Comece as respostas de forma amigável antes de ir para os detalhes técnicos.
        Se a resposta não estiver no contexto, diga que você não encontrou essa informação específica nos seus documentos, mas que pode tentar ajudar de outra forma ou procurar mais a fundo se o usuário der mais detalhes.

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
            # Pega alguns documentos aleatórios da base de dados para dar contexto
            retriever = self.vector_store.as_retriever(search_kwargs={'k': 5})
            # Busca por um termo mais específico para obter documentos relevantes
            all_docs = retriever.get_relevant_documents("compostos plásticos para indústria automotiva")
            
            # Garante que temos documentos suficientes para a amostra
            sample_size = min(3, len(all_docs))
            if sample_size == 0:
                return []

            sampled_docs = random.sample(all_docs, sample_size)

            # Template do prompt para gerar perguntas
            suggestion_template = """
            Com base nos trechos de documentos abaixo, que descrevem principalmente compostos plásticos e matéria-prima para a indústria automotiva, gere exatamente 3 perguntas que um cliente (como um engenheiro ou comprador técnico) faria.
            Foque em aspectos como aplicação do material, propriedades técnicas, compatibilidade e fornecimento. Evite tópicos secundários como móveis ou cadeiras, a menos que seja o único assunto dos trechos.
            Retorne apenas as perguntas, uma por linha, sem numeração ou marcadores.

            Exemplo de formato da resposta:
            Qual a resistência a impacto do composto XPTO-123?
            Esse polímero é adequado para peças de painel automotivo?
            Vocês fornecem este material em pellets?

            Documentos:
            {context}

            Perguntas Sugeridas:
            """
            suggestion_prompt = ChatPromptTemplate.from_template(suggestion_template)

            # Cria uma cadeia simples apenas para esta tarefa
            suggestion_chain = create_stuff_documents_chain(self.llm, suggestion_prompt)
            
            response = suggestion_chain.invoke({"context": sampled_docs})
            
            # Processa a resposta para retornar uma lista de strings
            suggestions = response.strip().split('\n')
            # Filtra linhas vazias que possam aparecer
            return [s.strip() for s in suggestions if s.strip()]

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