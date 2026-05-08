print("=== Testando Ferramentas ===\n")

from jarvis.tools import system, web, files, clipboard
import time

# Sistema
print("1. Abrindo bloco de notas...")
r = system.open_app("notepad")
print(f"   → {r}")

time.sleep(2)

print("2. Capturando tela...")
r = system.take_screenshot()
print(f"   → {r}")

print("3. Apps em execução...")
r = system.get_running_apps()
print(f"   → {r[:200]}...")

# Web
print("4. Pesquisando na web...")
r = web.search_web("Python programming language")
print(f"   → {r[:200]}...")

print("5. Buscando Wikipedia...")
r = web.search_wikipedia("Inteligência artificial")
print(f"   → {r[:200]}...")

# Arquivos
print("6. Criando arquivo de teste...")
r = files.write_file("Desktop/jarvis_test.txt", "Teste do JARVIS")
print(f"   → {r}")

print("7. Lendo arquivo criado...")
r = files.read_file("Desktop/jarvis_test.txt")
print(f"   → {r}")

# Clipboard
print("8. Escrevendo no clipboard...")
r = clipboard.write_clipboard("JARVIS testando clipboard")
print(f"   → {r}")

print("9. Lendo clipboard...")
r = clipboard.read_clipboard()
print(f"   → {r}")

print("\n✅ Todas as ferramentas testadas!")