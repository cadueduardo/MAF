import os
import re
import json
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, DirectoryLoader
from langchain_core.documents import Document

def format_product_data(product_name: str, properties: dict) -> str:
    """Cria uma string formatada e estruturada para a ficha técnica de um produto."""
    lines = [
        "--- Ficha Técnica do Produto ---",
        f"**PRODUTO: {product_name.strip()}**\n"
    ]
    for key, value in properties.items():
        # Ignora campos de nome/código redundantes
        if key.lower() in ['produto', 'nome', 'código']:
            continue
        
        # Formata a chave e o valor de forma limpa
        formatted_key = key.replace('_', ' ').title()
        lines.append(f"**{formatted_key}:** {value}")
        
    lines.append("--- Fim da Ficha Técnica ---\n")
    return "\n".join(lines)

def load_product_json(file_path: str) -> list[Document]:
    """Lê um arquivo JSON de produto e o transforma em um Documento LangChain formatado."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontra o nome do produto em chaves comuns
        product_name = ""
        possible_keys = ['produto', 'nome do produto', 'nome', 'product', 'product name', 'código']
        for key in possible_keys:
            if key in data:
                product_name = data[key]
                break
        
        if not product_name:
            # Se não encontrar um nome óbvio, pula o arquivo para evitar dados ruins.
            print(f"Aviso: Nome do produto não encontrado no arquivo {os.path.basename(file_path)}, pulando.")
            return []

        page_content = format_product_data(product_name, data)
        return [Document(page_content=page_content, metadata={"source": file_path})]
    except Exception as e:
        print(f"Erro ao processar o arquivo JSON {os.path.basename(file_path)}: {e}")
        return []

def load_product_docx(file_path: str) -> list[Document]:
    """Lê um arquivo DOCX, extrai o nome do produto do título e formata suas propriedades."""
    try:
        # Usa o Docx2txtLoader para pegar o texto puro
        loader = Docx2txtLoader(file_path)
        text = loader.load()[0].page_content

        # Pega o nome do produto da primeira linha (geralmente é o título)
        lines = text.split('\n')
        product_name = lines[0].strip() if lines else "Nome Desconhecido"
        
        # Cria um dicionário com as propriedades encontradas no texto
        properties = {}
        for line in lines[1:]:
            line = line.strip()
            # Procura por padrões como "Chave: Valor"
            match = re.match(r'([^:]+):\s*(.*)', line)
            if match:
                key, value = match.groups()
                properties[key.strip()] = value.strip()
        
        if not properties:
            # Se não encontrou propriedades estruturadas, usa o texto como está, mas com o nome do produto no topo
            page_content = f"**PRODUTO: {product_name}**\n\n{text}"
        else:
            page_content = format_product_data(product_name, properties)
            
        return [Document(page_content=page_content, metadata={"source": file_path})]
    except Exception as e:
        print(f"Erro ao processar o arquivo DOCX {os.path.basename(file_path)}: {e}")
        return []

def load_scraped_json(file_path: str) -> list[Document]:
    """Lê o JSON gerado pelo web scraper."""
    docs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if "page_content" in item and "metadata" in item:
                    docs.append(Document(page_content=item["page_content"], metadata=item["metadata"]))
        return docs
    except Exception as e:
        print(f"Erro ao processar o arquivo raspado {os.path.basename(file_path)}: {e}")
        return []

def load_documents(path: str):
    """Ponto de entrada principal para carregar e formatar todos os documentos locais."""
    print("Iniciando carregamento e formatação de todos os documentos...")
    all_docs = []
    
    # Mapeia os diretórios para as funções de processamento corretas
    directory_map = {
        "json": load_product_json,
        "DTS": load_product_docx, # Supondo que DOCX estejam em DTS
        "scraped": load_scraped_json,
    }

    # Itera sobre os diretórios e processa os arquivos
    for subdir, loader_func in directory_map.items():
        full_path = os.path.join(path, subdir)
        if os.path.exists(full_path):
            print(f"Processando diretório: {full_path}")
            for filename in os.listdir(full_path):
                file_path = os.path.join(full_path, filename)
                if os.path.isfile(file_path):
                    # Chama a função específica para cada tipo de arquivo
                    processed_docs = loader_func(file_path)
                    all_docs.extend(processed_docs)
    
    # Carrega PDFs de forma genérica, se existirem
    pdf_path = os.path.join(path, "DTS")
    if os.path.exists(pdf_path):
        pdf_loader = DirectoryLoader(pdf_path, glob="*.pdf", loader_cls=PyPDFLoader, silent_errors=True)
        pdf_docs = pdf_loader.load()
        if pdf_docs:
            print(f"Carregados {len(pdf_docs)} documentos PDF de {pdf_path}")
            all_docs.extend(pdf_docs)

    print(f"Total de {len(all_docs)} documentos carregados e formatados para processamento.")
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