from jarvis.brain.brain import Brain

brain = Brain()

# Teste: abrir app
r = brain.think("Abra o bloco de notas")
print(f"Abrir notepad: {r}")

# Teste: pesquisar
r = brain.think("Pesquise na web sobre python")
print(f"Pesquisa: {r}")

# Teste: screenshot
r = brain.think("Tire um print da tela")
print(f"Screenshot: {r}")

# Teste: pergunta normal (sem ferramenta)
r = brain.think("Qual é a capital do Brasil?")
print(f"Pergunta normal: {r}")