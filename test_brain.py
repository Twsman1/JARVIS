from jarvis.brain.brain import Brain

brain = Brain()

# Teste 1: pergunta simples
r1 = brain.think("Qual é a capital do Brasil?")
print(f"R1: {r1}")

# Teste 2: contexto (deve lembrar da pergunta anterior)
r2 = brain.think("E qual é a população dessa cidade?")
print(f"R2: {r2}")

# Teste 3: comando especial
r3 = brain.think("limpar memória")
print(f"R3: {r3}")

print("✅ Brain OK")