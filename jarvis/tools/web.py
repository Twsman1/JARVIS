import webbrowser
import requests
from bs4 import BeautifulSoup
import urllib.parse
from jarvis import core

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def search_web(query: str, max_results: int = 3) -> str:
    core.log.info(f"Pesquisando na web: {query}")
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        snippets = soup.select(".result__snippet")
        titles = soup.select(".result__title")
        
        for i in range(min(max_results, len(snippets))):
            title = titles[i].get_text(strip=True) if i < len(titles) else "Sem título"
            snippet = snippets[i].get_text(strip=True)[:200] + "..." if len(snippets[i].get_text(strip=True)) > 200 else snippets[i].get_text(strip=True)
            results.append(f"{i+1}. {title}\n{snippet}")
        
        if results:
            return f"Resultados para '{query}':\n\n" + "\n\n".join(results)
        else:
            return f"Nenhum resultado encontrado para '{query}'."
    except Exception as e:
        core.log.info(f"Erro na pesquisa web: {e}")
        return f"Erro na pesquisa web: {str(e)}"

def open_url(url: str) -> str:
    core.log.info(f"Abrindo URL: {url}")
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        webbrowser.open(url)
        return f"URL '{url}' aberta no navegador."
    except Exception as e:
        core.log.info(f"Erro ao abrir URL: {e}")
        return f"Erro ao abrir URL '{url}': {str(e)}"

def get_page_text(url: str, max_chars: int = 2000) -> str:
    core.log.info(f"Extraindo texto da página: {url}")
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remover scripts e estilos
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        return text
    except Exception as e:
        core.log.info(f"Erro ao extrair texto: {e}")
        return f"Erro ao extrair texto da página: {str(e)}"

def search_wikipedia(query: str) -> str:
    core.log.info(f"Pesquisando Wikipedia: {query}")
    try:
        url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        extract = data.get("extract", "")
        if len(extract) > 500:
            extract = extract[:500] + "..."
        
        return extract if extract else f"Nenhum resultado encontrado para '{query}' na Wikipedia."
    except Exception as e:
        core.log.info(f"Erro na pesquisa Wikipedia: {e}")
        return f"Erro na pesquisa Wikipedia: {str(e)}"