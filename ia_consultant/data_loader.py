import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    JSONLoader,
    UnstructuredWordDocumentLoader,
)

def load_documents(data_path: str):
    """
    Carrega todos os documentos de um diretório, suportando .json e .docx.

    Args:
        data_path: O caminho para o diretório com as pastas 'json' e 'DTS'.

    Returns:
        Uma lista de documentos carregados pelo LangChain.
    """
    json_path = os.path.join(data_path, "json")
    docx_path = os.path.join(data_path, "DTS")

    # Loader para arquivos JSON
    # Apenas um exemplo de como extrair texto, pode ser ajustado
    json_loader = DirectoryLoader(
        json_path,
        glob="**/*.json",
        loader_cls=JSONLoader,
        loader_kwargs={'jq_schema': '.[]', 'text_content': False}, # Carrega o JSON inteiro
        show_progress=True,
    )

    # Loader para arquivos DOCX
    docx_loader = DirectoryLoader(
        docx_path,
        glob="**/*.docx",
        loader_cls=UnstructuredWordDocumentLoader,
        show_progress=True,
    )

    documents_json = json_loader.load()
    documents_docx = docx_loader.load()

    return documents_json + documents_docx

if __name__ == "__main__":
    # Exemplo de como usar a função
    # O caminho aponta para a pasta que contém 'json' e 'DTS'
    # Ajuste este caminho conforme a estrutura do seu projeto
    caminho_produtos = "../CPE/produtos"
    if not os.path.exists(caminho_produtos):
        print(f"Caminho não encontrado: {caminho_produtos}")
        print("Por favor, ajuste a variável 'caminho_produtos' no final do script.")
    else:
        documentos = load_documents(caminho_produtos)
        print(f"Total de documentos carregados: {len(documentos)}")
        if documentos:
            print("\nExemplo de documento carregado (JSON):")
            # Encontra o primeiro JSON para exibir
            json_doc = next((doc for doc in documentos if doc.metadata.get('source', '').endswith('.json')), None)
            if json_doc:
                print(json_doc.page_content[:500])
            
            print("\nExemplo de documento carregado (DOCX):")
            # Encontra o primeiro DOCX para exibir
            docx_doc = next((doc for doc in documentos if doc.metadata.get('source', '').endswith('.docx')), None)
            if docx_doc:
                print(docx_doc.page_content[:500]) 