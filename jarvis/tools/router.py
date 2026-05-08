import json
import re
from jarvis.tools import system, web, files, clipboard, vision_tools
from jarvis.tools import get_tools_description
from jarvis import core

TOOL_MAP = {
    "open_app":         system.open_app,
    "close_app":        system.close_app,
    "take_screenshot":  system.take_screenshot,
    "get_running_apps": system.get_running_apps,
    "type_text":        system.type_text,
    "press_key":        system.press_key,
    "set_volume":       system.set_volume,
    "lock_pc":          system.lock_pc,
    "shutdown_pc":      system.shutdown_pc,
    "search_web":       web.search_web,
    "open_url":         web.open_url,
    "get_page_text":    web.get_page_text,
    "search_wikipedia": web.search_wikipedia,
    "read_file":        files.read_file,
    "write_file":       files.write_file,
    "list_files":       files.list_files,
    "create_folder":    files.create_folder,
    "delete_file":      files.delete_file,
    "read_clipboard":   clipboard.read_clipboard,
    "write_clipboard":  clipboard.write_clipboard,
    "describe_screen":      vision_tools.describe_screen,
    "read_screen_text":     vision_tools.read_screen_text,
    "answer_about_screen":  vision_tools.answer_about_screen,
    "read_error_on_screen": vision_tools.read_error_on_screen,
    "click_on_text":        vision_tools.click_on_text,
    "monitor_screen_change": vision_tools.monitor_screen_change,

class ToolRouter:
    def __init__(self):
        self.tools_description = get_tools_description()
        core.log.info(f"{len(TOOL_MAP)} ferramentas registradas")

    def get_system_addon(self) -> str:
        return f"""
Quando precisar executar uma ação no computador, responda APENAS com JSON:
{{"tool": "nome_da_ferramenta", "args": {{"param": "valor"}}}}

Ferramentas disponíveis:
{self.tools_description}

REGRAS IMPORTANTES:
- Se não precisar de ferramenta, responda normalmente em texto
- Nunca misture JSON e texto na mesma resposta
- Use os nomes exatos das ferramentas listadas
- Após executar uma ferramenta, você receberá o resultado e deve formular resposta em texto
"""

    def parse_and_execute(self, llm_response: str) -> tuple[bool, str]:
        tool_call = self._try_parse_json(llm_response)
        if not tool_call or "tool" not in tool_call:
            return False, llm_response
        
        tool_name = tool_call["tool"]
        if tool_name not in TOOL_MAP:
            return True, "Ferramenta não reconhecida."
        
        args = tool_call.get("args", {})
        try:
            result = TOOL_MAP[tool_name](**args)
            return True, result
        except Exception as e:
            core.log.info(f"Erro na execução da ferramenta {tool_name}: {e}")
            return True, f"Erro: {str(e)}"

    def _try_parse_json(self, text: str) -> dict | None:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Tentar encontrar JSON no texto
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return None