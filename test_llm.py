from jarvis.brain.llm import LLM
from jarvis.brain.memory import Memory

print("Testando LLM...")
memory = Memory()
llm = LLM(model="llama3")

memory.add_user("Olá, quem é você?")
response = llm.ask(memory.get_messages())
print(f"Resposta: {response}")
assert len(response) > 0
print("✅ LLM OK")