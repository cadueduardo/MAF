# Lista de Tarefas do Projeto MAF

Esta lista documenta o progresso do desenvolvimento do projeto My Agent Friend.

## ✅ Concluído

-   [x] **Visão e Escopo**: Definição da ideia central do projeto e suas funcionalidades chave.
-   [x] **Estrutura do Projeto**: Inicialização do repositório Git e criação da estrutura de pastas inicial (`documents`, `ia_consultant`).
-   [x] **Documentação Inicial**: Criação do arquivo `PROJECT_OVERVIEW.md` com a visão detalhada do projeto.
-   [x] **Desenvolvimento do Backend**: Implementação da API com Python e FastAPI.
-   [x] **Coração da IA**: Criação da classe `Agent` com LangChain para orquestrar a lógica de RAG.
-   [x] **Carregador de Dados Flexível**: Implementação do `data_loader.py` para processar arquivos `.docx` e `.json`.
-   [x] **IA Agnóstica**: Arquitetura configurada para permitir a troca entre modelos da OpenAI e do Google.
-   [x] **Base de Conhecimento Persistente**: Implementação do salvamento e carregamento do índice FAISS para evitar reprocessamento.
-   [x] **Criação da API**: Exposição do agente através de um endpoint `/ask` no `main.py`.
-   [x] **Segurança dos Dados**: Remoção completa dos dados sigilosos (`pasta CPE`) do histórico do repositório Git e atualização do `.gitignore`.

## ⏳ Próximos Passos

### Frontend (MVP)
-   [x] **Inicializar o Projeto**: Criar a aplicação frontend usando Next.js, TypeScript e Tailwind CSS.
-   [x] **Instalar Componentes de UI**: Adicionar as bibliotecas de componentes (shadcn/ui) ao projeto frontend.
-   [x] **Construir a Interface do Chat**: Desenvolver os componentes visuais para a caixa de diálogo do chat.
-   [x] **Conectar com a API**: Implementar a lógica no frontend para chamar o endpoint do backend.
-   [x] **Gerenciar Estado do Chat**: Controlar o histórico de mensagens e o estado de "digitando...".
-   [x] **Deploy e Configuração**: Publicar a aplicação em um subdomínio com Nginx e HTTPS.

## 🚀 Futuro e Melhorias (Plataforma SaaS)

-   [ ] **Arquitetura Multi-Tenant**: Evoluir o backend para uma plataforma SaaS capaz de servir múltiplos clientes.
    -   [ ] **Banco de Dados Central**: Implementar PostgreSQL para gerenciar clientes, configurações de IA (chaves de API criptografadas) e fontes de dados.
    -   [ ] **Painel de Administração do Cliente**: Desenvolver uma interface web para que clientes possam fazer login, gerenciar suas chaves de LLM e fontes de conhecimento (upload de arquivos, adição de URLs de sites).
    -   [ ] **Processamento em Segundo Plano**: Utilizar uma fila de tarefas (Celery/Redis) para lidar com a indexação de conteúdo sem travar a interface.
    -   [ ] **Autenticação Segura**: Implementar um sistema de API Keys para autenticação de clientes na plataforma.

-   [ ] **Plugin WordPress**: Desenhar e desenvolver um plugin para integrar facilmente o chat MAF em sites WordPress.
-   [ ] **Suporte a Novos Formatos**: Expandir o `data_loader` para incluir PDFs, imagens e transcrição de áudio/vídeo. 