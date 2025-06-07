# Projeto MAF (My Agent Friend)

## Visão Geral

O MAF é uma plataforma de IA conversacional projetada para que empresas possam criar seus próprios agentes de IA especialistas. A ideia central é permitir que os clientes alimentem o agente com sua própria base de conhecimento (documentos, manuais, catálogos de produtos) e o disponibilizem em seus sites para atuar como um consultor virtual inteligente.

## Principais Funcionalidades

1.  **Base de Conhecimento Flexível:**
    *   Os clientes poderão fazer o upload de seus próprios arquivos para criar o "cérebro" do agente.
    *   O MVP suportará documentos de texto como `.docx` e `.json`.
    *   **Visão Futura:** Expandir para suportar mais formatos, como PDF, imagens (usando modelos de visão), áudio e vídeo (usando transcrição).

2.  **Agente de IA Multimodelo:**
    *   O sistema será agnóstico em relação ao provedor de LLM (Large Language Model).
    *   Os clientes poderão conectar suas próprias chaves de API e escolher o modelo que desejam usar (ex: OpenAI GPT-4, Google Gemini, etc.).

3.  **Arquitetura Multi-cliente (Multi-tenant):**
    *   **Visão Futura:** A plataforma será projetada para isolar os dados de cada cliente, permitindo que múltiplos clientes usem o serviço de forma segura e independente a partir da mesma infraestrutura. Para o MVP, focaremos em uma estrutura para um único cliente, mas com a arquitetura pensada para essa expansão.

4.  **Integração Fácil:**
    *   A solução principal será uma API REST que pode ser consumida por qualquer front-end.
    *   **Visão Futura:** Criar um plugin para WordPress para facilitar a integração em sites que usam essa plataforma.

## Tecnologia do MVP

*   **Backend:** Python com FastAPI.
*   **Inteligência Artificial:** LangChain para orquestrar o fluxo de RAG (Retrieval-Augmented Generation).
*   **Base de Conhecimento (Vector Store):** FAISS, com persistência em disco para permitir atualizações incrementais.
*   **Suporte a Documentos:** `unstructured` para extrair texto de `.docx` e `JSONLoader` para `.json`.
*   **Suporte a LLM:** `langchain-openai` e `langchain-google-genai`. 