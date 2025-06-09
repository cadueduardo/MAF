import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Este LangChain Document não é o mesmo que o Pydantic Document.
# É uma estrutura específica do LangChain para guardar texto e metadados.
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

# Este código foi movido de data_loader.py para desacoplar a raspagem da web
# da inicialização do servidor, tornando a aplicação mais rápida e estável.

def get_internal_links(url, domain):
    """Encontra todos os links internos de uma página."""
    try:
        # Timeout aumentado para dar mais tempo para o site responder
        response = requests.get(url, timeout=15)
        response.raise_for_status() # Lança um erro para status HTTP 4xx/5xx
        soup = BeautifulSoup(response.content, 'html.parser')
        internal_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # NOVO: Ignora links que contêm parâmetros de idioma para inglês ou espanhol.
            if '?lang=en' in href or '?lang=es' in href:
                continue

            # Ignora links que não são de páginas web
            if href.startswith(('mailto:', 'tel:', '#')):
                continue
            full_url = urljoin(url, href)
            # Normaliza a URL para remover âncoras (#) e parâmetros
            full_url = full_url.split('#')[0]
            if urlparse(full_url).netloc == domain:
                internal_links.add(full_url)
        return internal_links
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return set()

def scrape_page_content(url):
    """Extrai o conteúdo de texto limpo de uma única página."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove partes do site que não contêm conteúdo principal (menus, rodapés, etc.)
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()

        # Extrai o texto e limpa espaços em branco e linhas vazias
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if text:
            # Retorna um objeto Document, o formato que o LangChain espera
            return Document(page_content=text, metadata={"source": url})
        return None
    except requests.RequestException as e:
        print(f"Erro ao raspar a página {url}: {e}")
        return None

def load_documents_from_website(root_url: str, max_pages: int = 100):
    """Navega por um site, extrai conteúdo de todas as páginas internas e retorna como Documentos."""
    domain = urlparse(root_url).netloc
    pages_to_visit = {root_url}
    visited_pages = set()
    all_documents = []

    print(f"--- Iniciando a leitura do site: {root_url} ---")
    while pages_to_visit and len(visited_pages) < max_pages:
        url = pages_to_visit.pop()

        # NOVO: Pula a página se for uma versão em inglês ou espanhol.
        if '?lang=en' in url or '?lang=es' in url:
            continue

        if url in visited_pages:
            continue

        print(f"Lendo página: {url} ({len(visited_pages) + 1}/{max_pages})")
        visited_pages.add(url)
        
        document = scrape_page_content(url)
        if document:
            all_documents.append(document)

        # Adiciona novos links para visitar, se houver espaço
        if len(visited_pages) < max_pages:
            new_links = get_internal_links(url, domain)
            pages_to_visit.update(new_links - visited_pages)
    
    print(f"--- Leitura do site finalizada. {len(all_documents)} páginas lidas. ---")
    return all_documents

def save_documents_to_json(documents, path):
    """Salva uma lista de objetos Document em um arquivo JSON."""
    # Garante que o diretório de destino exista
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Converte a lista de objetos Document para uma lista de dicionários
    docs_as_dicts = [
        {"page_content": doc.page_content, "metadata": doc.metadata}
        for doc in documents
    ]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(docs_as_dicts, f, indent=2, ensure_ascii=False)
    print(f"Conteúdo da web salvo com sucesso em: {path}")


if __name__ == "__main__":
    # --- Configuração ---
    # Altere a URL aqui para o site que deseja usar como fonte de contexto
    SITE_URL = "http://cpe.ind.br" 
    # O caminho de saída para o conteúdo raspado. Não precisa mudar.
    OUTPUT_PATH = "../CPE/produtos/scraped/website_content.json"
    # Limite de páginas a serem lidas para não demorar demais.
    MAX_PAGES_TO_SCRAPE = 100
    
    print("--- Iniciando Script de Coleta de Conteúdo Web ---")
    
    # Carrega os documentos do site
    scraped_docs = load_documents_from_website(SITE_URL, max_pages=MAX_PAGES_TO_SCRAPE)
    
    # Salva os documentos em um arquivo JSON se algum conteúdo foi coletado
    if scraped_docs:
        save_documents_to_json(scraped_docs, OUTPUT_PATH)
    else:
        print("Nenhum documento foi coletado do site.")
        
    print("--- Script de Coleta Finalizado ---") 