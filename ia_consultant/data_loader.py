import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredFileLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Mapeamento de extensões para loaders
LOADER_MAPPING = {
    ".pdf": (PyPDFLoader, {}),
    ".docx": (Docx2txtLoader, {}),
    ".json": (UnstructuredFileLoader, {}),
    # Adicione outros mapeamentos conforme necessário
}

def load_documents_from_directory(path: str):
    """Carrega documentos de um diretório usando loaders específicos para cada tipo de arquivo."""
    loader = DirectoryLoader(
        path,
        glob="**/*",
        loader_cls=UnstructuredFileLoader, # Loader padrão para extensões não mapeadas
        use_multithreading=True
    )
    return loader.load()

def get_internal_links(url, domain):
    """Encontra todos os links internos de uma página."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        internal_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
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
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove tags de script e style
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header']):
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
    while pages_to_visit:
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
    local_docs = load_documents_from_directory(path)
    print(f"{len(local_docs)} documentos carregados do diretório.")
    
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