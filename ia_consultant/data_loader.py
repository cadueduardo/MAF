import os
import re
import json
from langchain_community.document_loaders import Docx2txtLoader, DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document

def format_product_data(product_name: str, properties: dict) -> str:
    """Cria uma Ficha Técnica de Produto em texto, clara e bem estruturada."""
    lines = [
        "--- INÍCIO DA FICHA TÉCNICA ---",
        f"PRODUTO: {product_name.strip().upper()}"
    ]
    
    # Adiciona as propriedades formatadas, garantindo que não haja valores vazios
    for key, value in properties.items():
        clean_key = key.replace('_', ' ').strip().title()
        clean_value = str(value).strip()
        if clean_key and clean_value and clean_key.lower() != 'produto':
            lines.append(f"{clean_key}: {clean_value}")
            
    lines.append("--- FIM DA FICHA TÉCNICA ---")
    return "\n".join(lines)

def parse_product_json(file_path: str) -> list[Document]:
    """Lê um arquivo JSON, extrai e achata suas propriedades para o formato de Ficha Técnica."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        product_name = data.get('Produto', os.path.basename(file_path).split('.')[0])
        properties = {}

        # Itera pelo JSON para achatar os dados em um dicionário simples
        for key, value in data.items():
            if isinstance(value, dict) and key == "Propriedades":
                for prop_category in value.values():
                    if isinstance(prop_category, list):
                        for item in prop_category:
                            if isinstance(item, dict) and 'Propriedade' in item and 'Valor' in item:
                                prop_name = item['Propriedade']
                                prop_value = item['Valor']
                                if prop_name and prop_value is not None:
                                    properties[prop_name] = prop_value
            elif value is not None:
                properties[key] = value

        page_content = format_product_data(product_name, properties)
        return [Document(page_content=page_content, metadata={"source": file_path})]

    except Exception as e:
        print(f"Erro ao processar o arquivo JSON {os.path.basename(file_path)}: {e}")
        return []

def parse_product_docx(file_path: str) -> list[Document]:
    """Lê uma Ficha Técnica DOCX e extrai suas propriedades de forma estruturada."""
    try:
        text = Docx2txtLoader(file_path).load()[0].page_content
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        product_name = os.path.basename(file_path).split('.')[0] # Fallback
        properties = {}

        # Procura por 'Produto: NOME_PRODUTO'
        for line in lines:
            if line.lower().startswith("produto:"):
                product_name = line.split(":", 1)[1].strip()
                break
        
        # Extrai outros pares chave:valor e dados da tabela
        in_table_section = False
        for line in lines:
            if re.match(r'propriedades|método|unidade|valores', line, re.I):
                in_table_section = True
                continue
            if 'observação' in line.lower():
                in_table_section = False

            if in_table_section:
                # Na tabela, a primeira e a última coluna são as mais importantes
                parts = re.split(r'\s{2,}', line) # Divide por 2+ espaços
                if len(parts) >= 2:
                    prop_name, prop_value = parts[0], parts[-1]
                    if prop_name and prop_value:
                        properties[prop_name] = prop_value
            else:
                # Pares simples como 'Cor: Preto'
                match = re.match(r'^([^:]+):\s*(.+)$', line)
                if match:
                    key, value = match.groups()
                    if key.lower() != 'produto':
                        properties[key] = value

        page_content = format_product_data(product_name, properties)
        return [Document(page_content=page_content, metadata={"source": file_path})]

    except Exception as e:
        print(f"Erro ao processar o arquivo DOCX {os.path.basename(file_path)}: {e}")
        return []

def load_documents(path: str):
    """Ponto de entrada que carrega e formata todos os documentos de produtos."""
    print("Iniciando o tradutor de Fichas Técnicas...")
    all_docs = []
    
    # Processa JSONs
    json_path = os.path.join(path, "json")
    if os.path.exists(json_path):
        print(f"Traduzindo arquivos de: {json_path}")
        for filename in sorted(os.listdir(json_path)): # 'sorted' para consistência
            if filename.endswith('.json'):
                all_docs.extend(parse_product_json(os.path.join(json_path, filename)))

    # Processa DOCX
    docx_path = os.path.join(path, "DTS")
    if os.path.exists(docx_path):
        print(f"Traduzindo arquivos de: {docx_path}")
        for filename in sorted(os.listdir(docx_path)):
            if filename.endswith('.docx'):
                all_docs.extend(parse_product_docx(os.path.join(docx_path, filename)))

    print(f"Tradução finalizada. {len(all_docs)} Fichas Técnicas prontas para a IA.")
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