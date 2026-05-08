# jarvis/brain/agent.py
#
# Agente autônomo com loop ReAct (Reason + Act)
# Implementa planejamento e execução de tarefas complexas

from jarvis.hud import state as hud_state
from jarvis import core
import json
import time

AGENT_SYSTEM_PROMPT = """Você é JARVIS, um agente autônomo de IA.
Você pode executar tarefas complexas usando ferramentas disponíveis.

MODO DE OPERAÇÃO:
Para cada etapa, escolha UMA das opções abaixo:

OPÇÃO 1 - Usar uma ferramenta (responda APENAS com JSON):
{{"tool": "nome_da_ferramenta", "args": {{"parametro": "valor"}}, "reason": "por que estou usando esta ferramenta"}}

OPÇÃO 2 - Resposta final ao usuário (quando a tarefa estiver concluída):
RESPOSTA_FINAL: Sua resposta aqui em linguagem natural.

REGRAS:
- Use no máximo {{max_steps}} ferramentas por tarefa
- Sempre use "reason" para explicar sua decisão (ajuda no log)
- Quando a tarefa estiver completa, use RESPOSTA_FINAL
- Se não conseguir completar a tarefa, explique o motivo com RESPOSTA_FINAL
- Responda sempre em português do Brasil

FERRAMENTAS DISPONÍVEIS:
{{tools_description}}

HISTÓRICO DA SESSÃO ATUAL:
{{session_context}}"""

class Agent:
    """
    Agente autônomo que implementa o loop ReAct.
    Recebe uma tarefa complexa e a executa através de múltiplas etapas.
    """

    def __init__(self, llm, router, max_steps=6):
        self.llm = llm
        self.router = router
        self.max_steps = max_steps
        self.execution_log = []

    def run(self, task: str, session_context: str = "") -> tuple[str, list]:
        """
        Executa o loop ReAct completo para uma tarefa complexa.
        Retorna (resposta_final, execution_log)
        """
        self.execution_log = []
        
        # Mostrar log de execução
        try:
            from jarvis.hud.renderer import _execution_log
            if _execution_log:
                _execution_log.show(task[:30])
        except ImportError:
            pass  # Widget não disponível durante testes
        
        messages = [
            {"role": "system", "content": self._build_system_prompt(session_context)},
            {"role": "user", "content": f"Tarefa: {task}"}
        ]

        for step in range(self.max_steps):
            # 1. Logar etapa atual
            core.log.info(f"[Agente] Etapa {step+1}/{self.max_steps}")
            hud_state.set_state(hud_state.THINKING, f"etapa {step+1}")

            # 2. Chamar LLM
            response = self.llm.ask(messages)

            # 3. Parsear resposta
            parsed = self._parse_response(response)

            # 4. Se RESPOSTA_FINAL → encerrar loop
            if parsed["type"] in ("final", "unknown"):
                final_text = parsed["content"].replace("RESPOSTA_FINAL:", "").strip()
                self.execution_log.append({
                    "step": step+1, "type": "final", "content": final_text
                })
                hud_state.set_state(hud_state.IDLE)
                if _execution_log:
                    _execution_log.hide_after(3)
                return final_text, self.execution_log

            # 5. Se tool → executar
            if parsed["type"] == "tool":
                tool_data = parsed["content"]   # é um dict com "tool", "args", "reason"
                tool_name = tool_data.get("tool", "")
                args = tool_data.get("args", {})
                reason = tool_data.get("reason", "")

                core.log.info(f"[Agente] Executando: {tool_name} | Motivo: {reason}")
                
                # Mostrar etapa no log visual
                try:
                    from jarvis.hud.renderer import _execution_log
                    if _execution_log:
                        _execution_log.add_step(step+1, tool_name, "running")
                except ImportError:
                    pass
                
                hud_state.set_state(hud_state.ACTING, tool_name)

                # Registrar no log de execução
                self.execution_log.append({
                    "step": step+1, "type": "tool",
                    "tool": tool_name, "args": args, "reason": reason
                })

                # Executar ferramenta
                _, tool_result = self.router.parse_and_execute(response)

                # Marcar etapa como concluída
                try:
                    from jarvis.hud.renderer import _execution_log
                    if _execution_log:
                        _execution_log.complete_step(step+1, True)
                except ImportError:
                    pass

                # Adicionar ao histórico do LLM
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": self._format_step_for_llm(step+1, tool_name, args, tool_result)
                })

        # 6. Se atingiu max_steps sem RESPOSTA_FINAL
        final = "Atingi o limite de etapas. Aqui está o que consegui fazer: " + \
                str([e.get("tool") for e in self.execution_log if e["type"] == "tool"])
        hud_state.set_state(hud_state.IDLE)
        try:
            from jarvis.hud.renderer import _execution_log
            if _execution_log:
                _execution_log.hide_after(3)
        except ImportError:
            pass
        return final, self.execution_log

    def _build_system_prompt(self, session_context: str) -> str:
        """Formata o prompt do sistema com informações dinâmicas."""
        # Obter descrição das ferramentas disponíveis
        tools_description = """
- search_web: Pesquisa na web (args: {"query": "termo de busca"})
- read_file: Lê conteúdo de arquivo (args: {"path": "caminho/arquivo"})
- write_file: Escreve conteúdo em arquivo (args: {"path": "caminho/arquivo", "content": "conteúdo"})
- list_dir: Lista arquivos em diretório (args: {"path": "caminho/diretório"})
- run_command: Executa comando do sistema (args: {"command": "comando"})
- get_clipboard: Obtém conteúdo da área de transferência (args: {})
- set_clipboard: Define conteúdo da área de transferência (args: {"text": "conteúdo"})
        """

        return AGENT_SYSTEM_PROMPT.format(
            max_steps=self.max_steps,
            tools_description=tools_description.strip(),
            session_context=session_context
        )

    def _parse_response(self, response: str) -> dict:
        """
        Parseia a resposta do LLM.
        Retorna: {"type": "final"|"tool"|"unknown", "content": ...}
        """
        response = response.strip()

        # Verificar se é resposta final
        if response.startswith("RESPOSTA_FINAL:"):
            return {"type": "final", "content": response}

        # Tentar parsear como JSON (ferramenta)
        try:
            tool_data = json.loads(response)
            if isinstance(tool_data, dict) and "tool" in tool_data:
                return {"type": "tool", "content": tool_data}
        except json.JSONDecodeError:
            pass

        # Caso contrário, tratar como resposta final desconhecida
        return {"type": "unknown", "content": response}

    def _format_step_for_llm(self, step_num, tool_name, args, result) -> str:
        """Formata o resultado de uma etapa para o histórico do LLM."""
        return f"[Etapa {step_num}] Ferramenta: {tool_name}\nArgumentos: {args}\nResultado: {result}"