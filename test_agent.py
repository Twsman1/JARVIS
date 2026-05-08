# test_agent.py (temporário, deletar após teste)

from jarvis.brain.llm import LLM
from jarvis.brain.agent import Agent
from jarvis.tools.router import ToolRouter

llm = LLM(mock=True)
router = ToolRouter()
agent = Agent(llm=llm, router=router, max_steps=4)

# Teste 1: tarefa simples de 2 passos
print("\nTeste 1: Pesquisar e salvar")
result, log = agent.run("Pesquise sobre a linguagem Python e escreva um resumo de 3 linhas no arquivo Desktop/python.txt")
print(f"Resposta: {result}")
print(f"Etapas executadas: {len(log)}")
for step in log:
    print(f"  Etapa {step['step']}: {step.get('tool', step.get('type'))}")

# Teste 2: tarefa de informação (deve usar 0 ferramentas e responder direto)
print("\nTeste 2: Pergunta direta")
result, log = agent.run("Qual é a capital da França?")
print(f"Resposta: {result}")
print(f"Etapas: {len(log)}")