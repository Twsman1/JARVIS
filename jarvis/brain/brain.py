from jarvis.brain.memory import Memory
from jarvis.brain.llm import LLM
from jarvis.brain.agent import Agent
from jarvis.brain.task_detector import is_complex_task
from jarvis.brain.scheduler import Scheduler
from jarvis.tools.router import ToolRouter
from jarvis import core
from jarvis.config import LLM_MODEL, LLM_ENGINE
from jarvis.hud import state

class Brain:
    def __init__(self, model: str = LLM_MODEL, engine: str = LLM_ENGINE, mock: bool = True):
        self.router = ToolRouter()
        self.memory = Memory(router=self.router)
        self.llm = LLM(model=model, engine=engine, mock=mock)
        self.agent = Agent(llm=self.llm, router=self.router)
        self.scheduler = Scheduler(speak_callback=core.speak)
        core.log.info("Cérebro JARVIS inicializado")

    def think(self, user_input: str) -> str:
        core.log.info(f"Processando: {user_input}")
        normalized = user_input.strip().lower()

        # 1. Verificar comandos especiais internos (sem LLM)
        if normalized in ["limpar memória", "esquecer tudo"]:
            return self.reset_memory()

        # 2. Verificar se é lembrete/agendamento
        is_reminder, reminder_response = self.scheduler.parse_reminder_command(user_input)
        if is_reminder:
            return reminder_response

        # 3. Decidir: tarefa complexa (Agent) ou simples (Brain)?
        if is_complex_task(user_input):
            core.log.info(f"[Brain] Tarefa complexa detectada → usando Agent")
            core.speak("Entendido, senhor. Iniciando execução.")
            final_response, execution_log = self.agent.run(
                task=user_input,
                session_context=self._get_session_summary()
            )
            # Adicionar ao log de memória como uma única interação
            self.memory.add_user(user_input)
            self.memory.add_assistant(final_response)
            return final_response

        # 4. Tarefa simples: fluxo normal com ferramentas (Fase 3)
        else:
            core.log.info(f"[Brain] Tarefa simples → usando Brain direto")
            return self._think_simple(user_input)

    def _get_session_summary(self) -> str:
        """Retorna resumo das últimas 3 interações da memória."""
        messages = self.memory.get_messages()
        if len(messages) < 6:  # Menos de 3 pares user/assistant
            return "Nenhuma conversa anterior."

        # Pegar últimas 3 interações (6 mensagens)
        recent = messages[-6:]
        summary = "Contexto recente:\n"
        for i in range(0, len(recent), 2):
            if i+1 < len(recent):
                user_msg = recent[i].get("content", "")[:100]
                assistant_msg = recent[i+1].get("content", "")[:100]
                summary += f"- Usuário: {user_msg}...\n- JARVIS: {assistant_msg}...\n"

        return summary.strip()

    def _think_simple(self, user_input: str) -> str:
        """Lógica de pensamento simples (Fases 2+3) movida para cá."""
        # Comandos especiais
        if user_input.strip().lower() in ["qual modelo", "que modelo"]:
            return f"Estou usando o modelo {self.llm.model}, senhor."

        # Novo fluxo com ferramentas
        self.memory.add_user(user_input)
        messages = self.memory.get_messages()
        state.set_state(state.THINKING, "consultando LLM")
        response_1 = self.llm.ask(messages)

        tool_used, tool_result = self.router.parse_and_execute(response_1)

        if tool_used:
            core.log.info(f"Ferramenta executada, resultado: {tool_result[:100]}...")
            state.set_state(state.ACTING, tool_result.split()[0] if tool_result else "tool")
            self.memory.add_assistant(response_1)
            self.memory.add_user(f"Resultado: {tool_result}")
            messages_2 = self.memory.get_messages()
            state.set_state(state.THINKING, "formulando resposta")
            response_2 = self.llm.ask(messages_2)
            self.memory.add_assistant(response_2)
            core.log.info(f"Resposta final: {response_2}")
            state.set_state(state.IDLE)
            return response_2
        else:
            self.memory.add_assistant(response_1)
            core.log.info(f"Resposta: {response_1}")
            state.set_state(state.IDLE)
            return response_1

    def reset_memory(self):
        self.memory.clear()
        return "Memória limpa, senhor. Podemos recomeçar."