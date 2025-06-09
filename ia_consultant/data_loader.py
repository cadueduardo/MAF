import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_core.documents import Document
import json

def format_product_json(data: dict) -> str:
    """
    Formata um dicionário JSON de um produto em uma string de texto legível,
    garantindo que o nome do produto e suas propriedades estejam claramente associados.
    """
    lines = []
    
    # Tenta encontrar o nome do produto com várias chaves possíveis, ignorando maiúsculas/minúsculas.
    product_name = ""
    # Chaves comuns para nomes de produtos em português e inglês.
    possible_name_keys = ['produto', 'nome do produto', 'nome', 'product', 'product name', 'código']
    
    found_name_key = None
    for key in possible_name_keys:
        for data_key in data.keys():
            if data_key.lower() == key:
                product_name = data[data_key]
                found_name_key = data_key
                break
        if product_name:
            break
            
    # Adiciona um cabeçalho claro para o LLM
    lines.append("--- Ficha Técnica do Produto ---")
    if product_name:
        lines.append(f"**Nome do Produto:** {product_name}")
    
    # Itera sobre todos os dados e os formata
    for key, value in data.items():
        if key == found_name_key:
            continue # Pula a chave do nome, pois já foi adicionada.
            
        formatted_key = key.replace('_', ' ').title()
        
        if isinstance(value, dict):
            lines.append(f"\n**{formatted_key}:**")
            for sub_key, sub_value in value.items():
                lines.append(f"  - {sub_key.replace('_', ' ').title()}: {sub_value}")
        elif isinstance(value, list):
            lines.append(f"\n**{formatted_key}:**")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"**{formatted_key}:** {value}")
            
    lines.append("--- Fim da Ficha Técnica ---")
    return "\n\n".join(lines)

def load_json_docs(path: str):
    """
    Carrega arquivos JSON de um diretório.
    Ele consegue processar tanto os JSONs de produtos (um objeto por arquivo)
    quanto os JSONs do web scraper (uma lista de documentos por arquivo).
    """
    json_docs = []
    if not os.path.exists(path):
        # Não imprime nada se o diretório não existe, pois é esperado
        # que o diretório 'scraped' possa não existir na primeira execução.
        return json_docs
        
    for filename in os.listdir(path):
        if filename.endswith('.json'):
            file_path = os.path.join(path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Se o JSON for uma lista de objetos (formato do scrape)
                    if isinstance(data, list):
                        for item in data:
                            if "page_content" in item and "metadata" in item:
                                json_docs.append(Document(page_content=item["page_content"], metadata=item["metadata"]))
                    # Se for um dicionário (formato original de produto)
                    elif isinstance(data, dict):
                        # MODIFICADO: Usa a nova função para formatar o JSON de produto em texto legível.
                        text_content = format_product_json(data)
                        json_docs.append(Document(page_content=text_content, metadata={"source": file_path}))

            except Exception as e:
                print(f"Erro ao carregar o arquivo JSON {filename}: {e}")
                
    if json_docs:
        print(f"Carregados {len(json_docs)} documentos de {path}")
    return json_docs

def load_individual_document_types(data_path: str):
    """Carrega documentos de subdiretórios específicos (json, DTS, e os novos 'scraped')."""
    all_docs = []
    
    # 1. Carrega JSONs de produtos
    json_path = os.path.join(data_path, "json")
    all_docs.extend(load_json_docs(json_path))
    
    # 2. Carrega o conteúdo da web previamente coletado
    scraped_path = os.path.join(data_path, "scraped")
    all_docs.extend(load_json_docs(scraped_path))
    
    # 3. Define os caminhos e os loaders para outros tipos de arquivo (DOCX, PDF)
    configs = [
        {"path": os.path.join(data_path, "DTS"), "glob": "*.docx", "loader_cls": Docx2txtLoader},
        {"path": os.path.join(data_path, "DTS"), "glob": "*.pdf", "loader_cls": PyPDFLoader},
    ]

    for config in configs:
        if os.path.exists(config["path"]):
            loader = DirectoryLoader(
                config["path"],
                glob=config["glob"],
                loader_cls=config["loader_cls"],
                show_progress=False, # Mantém False para logs limpos
                use_multithreading=True
            )
            try:
                docs = loader.load()
                print(f"Carregados {len(docs)} documentos de {config['path']}/{config['glob']}")
                all_docs.extend(docs)
            except Exception as e:
                print(f"Erro ao carregar documentos de {config['path']}/{config['glob']}: {e}")
        else:
            print(f"Diretório não encontrado, pulando: {config['path']}")
            
    return all_docs

def load_documents(path: str):
    """
    Ponto de entrada principal para carregar todos os documentos de fontes locais.
    """
    print("Iniciando carregamento de todos os documentos locais...")
    
    # Carrega todos os tipos de documentos das subpastas
    all_docs = load_individual_document_types(path)
    
    print(f"Total de {len(all_docs)} documentos carregados para processamento.")
    return all_docs

if __name__ == "__main__":
    # Exemplo de como usar a função
    caminho_produtos = "../CPE/produtos"
    if not os.path.exists(caminho_produtos):
        print(f"Caminho não encontrado: {caminho_produtos}")
        print("Por favor, ajuste a variável 'caminho_produtos' no final do script.")
    else:
        documentos = load_documents(caminho_produtos)
        print(f"Total de documentos carregados: {len(documentos)}")
        if documentos:
            # Tenta encontrar e exibir um exemplo de cada tipo de documento
            json_doc = next((doc for doc in documentos if ".json" in doc.metadata.get('source', '')), None)
            docx_doc = next((doc for doc in documentos if ".docx" in doc.metadata.get('source', '')), None)
            
            if json_doc:
                print("\n--- Exemplo de documento JSON ---")
                print(json_doc.page_content[:300] + "...")

            if docx_doc:
                print("\n--- Exemplo de documento DOCX ---")
                print(docx_doc.page_content[:300] + "...") 