import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    Docx2txtLoader,
    JSONLoader,
)
from langchain_core.documents import Document
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def load_individual_document_types(data_path: str):
    """Carrega documentos de subdiretórios específicos (json, DTS) para evitar erros."""
    all_docs = []
    
    # Define os caminhos e os loaders para cada tipo de arquivo
    configs = [
        {"path": os.path.join(data_path, "json"), "glob": "*.json", "loader_cls": JSONLoader, "loader_kwargs": {'jq_schema': '.', 'text_content': True}},
        {"path": os.path.join(data_path, "DTS"), "glob": "*.docx", "loader_cls": Docx2txtLoader, "loader_kwargs": {}},
        {"path": os.path.join(data_path, "DTS"), "glob": "*.pdf", "loader_cls": PyPDFLoader, "loader_kwargs": {}},
    ]

    for config in configs:
        if os.path.exists(config["path"]):
            loader = DirectoryLoader(
                config["path"],
                glob=config["glob"],
                loader_cls=config["loader_cls"],
                loader_kwargs=config.get("loader_kwargs", {}),
                show_progress=True,
                use_multithreading=True
            )
            try:
                docs = loader.load()
                all_docs.extend(docs)
                print(f"Carregados {len(docs)} documentos de {config['path']}/{config['glob']}")
            except Exception as e:
                print(f"Erro ao carregar documentos de {config['path']}: {e}")
        else:
            print(f"Diretório não encontrado, pulando: {config['path']}")
            
    return all_docs

def get_internal_links(url, domain):
    """Encontra todos os links internos de uma página."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        internal_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Ignora links de email, telefone, etc.
            if href.startswith(('mailto:', 'tel:')):
                continue
            full_url = urljoin(url, href)
            # Normaliza a URL para remover fragmentos (#)
            full_url = full_url.split('#')[0]
            if urlparse(full_url).netloc == domain:
                internal_links.add(full_url)
        return internal_links
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return set()

def scrape_page_content(url):
    """Extrai o conteúdo de texto de uma única página."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove tags de script, style, nav, footer, header
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script_or_style.decompose()

        # Pega o texto e limpa espaços em branco
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if text:
            return Document(page_content=text, metadata={"source": url})
        return None
    except requests.RequestException as e:
        print(f"Erro ao raspar a página {url}: {e}")
        return None

def load_documents_from_website(root_url: str):
    """Navega por um site, extrai conteúdo de todas as páginas internas e retorna como Documentos."""
    domain = urlparse(root_url).netloc
    pages_to_visit = {root_url}
    visited_pages = set()
    all_documents = []

    print(f"Iniciando a leitura do site: {root_url}")
    while pages_to_visit and len(visited_pages) < 100: # Limite de segurança para não ficar em loop
        url = pages_to_visit.pop()
        if url in visited_pages:
            continue

        print(f"Lendo página: {url}")
        visited_pages.add(url)
        
        document = scrape_page_content(url)
        if document:
            all_documents.append(document)

        new_links = get_internal_links(url, domain)
        pages_to_visit.update(new_links - visited_pages)
    
    print(f"Leitura do site finalizada. {len(all_documents)} páginas lidas.")
    return all_documents


def load_documents(path: str, website_url: str = None):
    """
    Carrega documentos de um diretório local e, opcionalmente, de um site.
    """
    print("Iniciando carregamento de documentos...")
    
    # Carrega dos arquivos locais
    local_docs = load_individual_document_types(path)
    
    # Carrega do site se a URL for fornecida
    website_docs = []
    if website_url:
        website_docs = load_documents_from_website(website_url)
    
    # Combina as duas fontes
    all_docs = local_docs + website_docs
    print(f"Total de {len(all_docs)} documentos carregados para processamento.")
    return all_docs

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