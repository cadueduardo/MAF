import os
import re
import json
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, DirectoryLoader
from langchain_core.documents import Document

def format_product_data(product_name: str, properties: dict) -> str:
    """Cria uma string de Ficha Técnica estruturada para um produto."""
    lines = [
        "--- INÍCIO DA FICHA TÉCNICA DO PRODUTO ---",
        f"**PRODUTO: {product_name.strip().upper()}**\n"
    ]
    
    # Adiciona as propriedades formatadas
    for key, value in properties.items():
        if str(value).strip(): # Garante que não adicionemos valores vazios
            lines.append(f"**{key.strip().title()}:** {str(value).strip()}")
            
    lines.append(f"\n**FIM DA FICHA TÉCNICA DO PRODUTO: {product_name.strip().upper()}**")
    lines.append("--- FIM DA FICHA TÉCNICA ---")
    return "\n".join(lines)

def load_product_json(file_path: str) -> list[Document]:
    """Lê um arquivo JSON de produto e o transforma em um Documento LangChain formatado."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        product_name = ""
        possible_keys = ['produto', 'nome do produto', 'nome', 'product', 'product name', 'código']
        for key in possible_keys:
            for data_key in data.keys():
                if key == data_key.lower():
                    product_name = data.pop(data_key) # Remove a chave do nome para não duplicar
                    break
            if product_name:
                break
        
        if not product_name:
            print(f"Aviso: Nome do produto não encontrado no JSON {os.path.basename(file_path)}, pulando.")
            return []

        page_content = format_product_data(product_name, data)
        return [Document(page_content=page_content, metadata={"source": file_path})]
    except Exception as e:
        print(f"Erro ao processar o arquivo JSON {os.path.basename(file_path)}: {e}")
        return []

def load_product_docx(file_path: str) -> list[Document]:
    """Lê uma Ficha Técnica DOCX, extrai o nome do produto e suas propriedades de forma estruturada."""
    try:
        loader = Docx2txtLoader(file_path)
        text = loader.load()[0].page_content
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        product_name = "Nome Desconhecido"
        properties = {}

        # Procura pelo nome do produto de forma mais robusta
        for line in lines:
            match = re.search(r"Produto:\s*(.*?)(?:\s*Cor:.*)?$", line, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                break
        
        # Se não achou, usa a primeira linha como último recurso
        if product_name == "Nome Desconhecido" and lines:
            product_name = lines[0]

        # Extrai todos os pares "Chave: Valor" e os dados da tabela
        in_table = False
        for line in lines:
            # Pares simples (ex: "Cor: Jet Black")
            match_kv = re.match(r'^([^:]+):\s*(.+)$', line)
            if match_kv:
                key, value = match_kv.groups()
                # Ignora o próprio nome do produto e cabeçalhos de seção
                if key.strip().lower() not in ['produto', 'propriedades', 'mecânicas', 'impacto', 'térmicas', 'outros']:
                    properties[key.strip()] = value.strip()

            # Lógica para entrar na tabela de propriedades
            if any(header in line.lower() for header in ['método', 'unidade', 'valores típicos']):
                in_table = True
                continue
            if "observação" in line.lower():
                in_table = False # Fim da tabela

            # Se estamos na tabela, extrai os dados dela
            if in_table:
                parts = re.split(r'\s{2,}', line) # Divide por 2 ou mais espaços
                if len(parts) >= 2:
                    prop_name = parts[0].strip()
                    prop_value = parts[-1].strip()
                    if prop_name and prop_value:
                        properties[prop_name] = prop_value
        
        if product_name == "Nome Desconhecido":
            print(f"Aviso: Não foi possível determinar o nome do produto em {os.path.basename(file_path)}. Pulando.")
            return []
        
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
        "DTS": load_product_docx,
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
                    # Chama a função específica para o tipo de arquivo
                    if subdir == "DTS" and filename.endswith('.docx'):
                        all_docs.extend(load_product_docx(file_path))
                    elif subdir == "json":
                        all_docs.extend(load_product_json(file_path))
                    elif subdir == "scraped":
                         all_docs.extend(load_scraped_json(file_path))

    # Carrega PDFs de forma genérica, se existirem na pasta DTS
    pdf_path = os.path.join(path, "DTS")
    if os.path.exists(pdf_path):
        pdf_loader = DirectoryLoader(pdf_path, glob="*.pdf", loader_cls=PyPDFLoader, silent_errors=True, show_progress=False, use_multithreading=True)
        pdf_docs = pdf_loader.load()
        if pdf_docs:
            print(f"Carregados {len(pdf_docs)} documentos PDF de forma genérica.")
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