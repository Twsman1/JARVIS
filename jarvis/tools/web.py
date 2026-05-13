import webbrowser
import requests
from bs4 import BeautifulSoup
import urllib.parse
from jarvis import core

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Enhanced browser automation using Playwright patterns from OpenJarvis
class BrowserSession:
    """Manages a shared browser session for web automation."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    def _ensure_browser(self):
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._page = self._browser.new_page()
        except ImportError:
            core.log.warning("Playwright não instalado. Instale com: pip install playwright")
            raise ImportError("playwright not installed")

    @property
    def page(self):
        self._ensure_browser()
        return self._page

    def close(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._playwright = self._browser = self._page = None

# Global browser session
_browser_session = BrowserSession()

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

def browse_page(url: str, wait_for: str = "load", extract_text: bool = True) -> str:
    """
    Browse a page using Playwright for better rendering and interaction.
    Enhanced from OpenJarvis browser tool patterns.

    Args:
        url: URL to navigate to
        wait_for: Wait condition ('load', 'domcontentloaded', 'networkidle')
        extract_text: Whether to extract and return page text content

    Returns:
        Page title and content information
    """
    core.log.info(f"Navegando para: {url}")
    try:
        page = _browser_session.page

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        response = page.goto(url, wait_until=wait_for)
        title = page.title()
        status = response.status if response else None

        result = f"Título: {title}\nStatus: {status}\nURL: {url}"

        if extract_text:
            text_content = page.inner_text("body")
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "\n\n[Conteúdo truncado]"
            result += f"\n\nConteúdo:\n{text_content}"

        return result

    except ImportError:
        return "Playwright não instalado. Use get_page_text() como alternativa."
    except Exception as exc:
        core.log.info(f"Erro na navegação: {exc}")
        return f"Erro ao navegar para {url}: {exc}"

def click_element(url: str, selector: str, by_text: bool = False) -> str:
    """
    Click an element on a web page using Playwright.
    Enhanced from OpenJarvis browser click tool.

    Args:
        url: URL of the page
        selector: CSS selector or text content to click
        by_text: If True, click by text content instead of CSS selector

    Returns:
        Result of the click operation
    """
    core.log.info(f"Clicando em elemento: {selector} na página {url}")
    try:
        page = _browser_session.page

        # Navigate first if not already on the page
        if page.url != url:
            page.goto(url, wait_until="load")

        if by_text:
            # Click by text content
            page.get_by_text(selector).click()
            return f"Clicado no texto '{selector}' na página {url}"
        else:
            # Click by CSS selector
            page.click(selector)
            return f"Clicado no seletor '{selector}' na página {url}"

    except ImportError:
        return "Playwright não instalado. Não é possível clicar em elementos."
    except Exception as exc:
        core.log.info(f"Erro ao clicar: {exc}")
        return f"Erro ao clicar no elemento: {exc}"

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

def close_browser_session():
    """Close the shared browser session to free resources."""
    _browser_session.close()