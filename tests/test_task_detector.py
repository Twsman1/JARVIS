# test_task_detector.py (temporário, deletar após teste)

from jarvis.brain.task_detector import is_complex_task

testes = [
    ("abra o notepad", False),
    ("qual é a capital do Brasil", False),
    ("boa tarde jarvis", False),
    ("pesquise sobre python e salve o resultado em um arquivo", True),
    ("abra o chrome e depois acesse o gmail", True),
    ("crie uma pasta chamada projetos e escreva um arquivo readme dentro dela", True),
    ("pesquise sobre machine learning e me mande um resumo", True),
]

print("Testando detector de tarefas complexas:")
print("=" * 50)

for text, esperado in testes:
    resultado = is_complex_task(text)
    status = "✅" if resultado == esperado else "❌"
    print(f"{status} '{text[:50]}' → complexo={resultado} (esperado={esperado})")

print("\nTeste concluído!")