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
-   [ ] **Inicializar o Projeto**: Criar a aplicação frontend usando Next.js, TypeScript e Tailwind CSS.
-   [ ] **Instalar Magic UI**: Adicionar as bibliotecas do Magic UI ao projeto frontend.
-   [ ] **Construir a Interface do Chat**: Desenvolver os componentes visuais para a caixa de diálogo do chat (input de texto, área de mensagens, etc.).
-   [ ] **Conectar com a API**: Implementar a lógica no frontend para chamar o endpoint `http://localhost:8000/ask` do backend.
-   [ ] **Gerenciar Estado do Chat**: Controlar o histórico de mensagens e o estado de "digitando..." na interface.
-   [ ] **Estilização Final**: Refinar o visual do chat para uma experiência de usuário agradável.

### Futuro e Melhorias
-   [ ] **Plugin WordPress**: Desenhar e desenvolver um plugin para integrar facilmente o chat MAF em sites WordPress.
-   [ ] **Arquitetura Multi-Tenant**: Evoluir o backend para suportar múltiplos clientes de forma segura e isolada.
-   [ ] **Suporte a Novos Formatos**: Expandir o `data_loader` para incluir PDFs, imagens e transcrição de áudio/vídeo. 