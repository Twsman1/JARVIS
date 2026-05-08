import os
import shutil
import time
from pathlib import Path
from jarvis import core

USER_HOME = Path.home()
SAFE_BASE = USER_HOME

def _resolve_path(path_str: str) -> Path:
    """Resolve e valida um path."""
    if os.path.isabs(path_str):
        path = Path(path_str)
    else:
        path = USER_HOME / path_str
    
    # Resolver .. e .
    path = path.resolve()
    
    # Verificar se está dentro de SAFE_BASE
    try:
        path.relative_to(SAFE_BASE)
    except ValueError:
        raise ValueError(f"Caminho fora da área segura: {path}")
    
    return path

def read_file(path: str) -> str:
    core.log.info(f"Lendo arquivo: {path}")
    try:
        resolved_path = _resolve_path(path)
        if not resolved_path.exists():
            return f"Arquivo não encontrado: {path}"
        
        with open(resolved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > 5000:
            content = content[:5000] + "\n\n[Arquivo truncado - muito longo]"
        
        return content
    except Exception as e:
        core.log.info(f"Erro ao ler arquivo: {e}")
        return f"Erro ao ler arquivo '{path}': {str(e)}"

def write_file(path: str, content: str, append: bool = False) -> str:
    core.log.info(f"Escrevendo arquivo: {path}")
    try:
        resolved_path = _resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(resolved_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        action = "atualizado" if append else "criado"
        return f"Arquivo '{path}' {action} com sucesso."
    except Exception as e:
        core.log.info(f"Erro ao escrever arquivo: {e}")
        return f"Erro ao escrever arquivo '{path}': {str(e)}"

def list_files(path: str = ".", pattern: str = "*") -> str:
    core.log.info(f"Listando arquivos: {path}")
    try:
        resolved_path = _resolve_path(path)
        if not resolved_path.exists():
            return f"Diretório não encontrado: {path}"
        
        files = list(resolved_path.glob(pattern))
        files = files[:20]  # Máximo 20
        
        if not files:
            return f"Nenhum arquivo encontrado em {path}"
        
        result = f"Arquivos em {path}:\n"
        for file_path in files:
            try:
                stat = file_path.stat()
                size_kb = stat.st_size / 1024
                mtime = time.ctime(stat.st_mtime)
                result += f"- {file_path.name} ({size_kb:.1f} KB) - {mtime}\n"
            except Exception:
                result += f"- {file_path.name} (erro ao obter info)\n"
        
        return result.strip()
    except Exception as e:
        core.log.info(f"Erro ao listar arquivos: {e}")
        return f"Erro ao listar arquivos em '{path}': {str(e)}"

def create_folder(path: str) -> str:
    core.log.info(f"Criando pasta: {path}")
    try:
        resolved_path = _resolve_path(path)
        if resolved_path.exists():
            return f"Pasta '{path}' já existe."
        
        resolved_path.mkdir(parents=True, exist_ok=True)
        return f"Pasta '{path}' criada."
    except Exception as e:
        core.log.info(f"Erro ao criar pasta: {e}")
        return f"Erro ao criar pasta '{path}': {str(e)}"

def delete_file(path: str) -> str:
    core.log.info(f"Movendo para lixeira: {path}")
    try:
        resolved_path = _resolve_path(path)
        if not resolved_path.exists():
            return f"Arquivo não encontrado: {path}"
        
        # Criar pasta de lixeira
        trash_dir = USER_HOME / "JARVIS_Lixeira"
        trash_dir.mkdir(exist_ok=True)
        
        # Mover para lixeira
        trash_path = trash_dir / resolved_path.name
        counter = 1
        while trash_path.exists():
            stem = resolved_path.stem
            suffix = resolved_path.suffix
            trash_path = trash_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.move(str(resolved_path), str(trash_path))
        return f"Arquivo movido para a lixeira JARVIS."
    except Exception as e:
        core.log.info(f"Erro ao mover para lixeira: {e}")
        return f"Erro ao mover arquivo '{path}' para lixeira: {str(e)}"