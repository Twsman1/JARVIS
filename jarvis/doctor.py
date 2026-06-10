import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests

from jarvis.brain.llm import LLM
from jarvis.config import (
    JARVIS_OPENJARVIS_CONFIG,
    LLM_ENGINE,
    LLM_MODEL,
    OLLAMA_HOST,
    WHISPER_LOCAL_DIR,
    WHISPER_MODEL,
)

CLOUD_KEY_NAMES = [
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "OPENAI_API_ORG",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "AZURE_OPENAI_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "HUGGINGFACE_HUB_TOKEN",
]

PROHIBITED_MODEL_PREFIXES = (
    "gpt-",
    "claude-",
    "gemini-",
    "openrouter/",
    "chatgpt-",
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jarvis local health and maintenance diagnostics"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print diagnostics as JSON",
    )
    return parser.parse_args(argv)


def find_cloud_keys() -> list[str]:
    warnings = []
    for key in CLOUD_KEY_NAMES:
        if os.environ.get(key):
            warnings.append(key)
    return warnings


def whisper_status() -> dict[str, Any]:
    path = WHISPER_MODEL or WHISPER_LOCAL_DIR
    p = Path(path)
    status = {
        "configured_dir": str(WHISPER_LOCAL_DIR),
        "resolved_model_dir": str(path) if path else None,
        "exists": False,
        "model_bin": False,
        "is_cache_path": "huggingface" in str(path).lower() or "hub" in str(path).lower(),
    }

    if p.exists():
        status["exists"] = True
        status["model_bin"] = (p / "model.bin").is_file() if p.is_dir() else False
    return status


def llm_status() -> dict[str, Any]:
    model_is_local = not any(
        LLM_MODEL.lower().startswith(prefix)
        for prefix in PROHIBITED_MODEL_PREFIXES
    )
    status = {
        "engine": LLM_ENGINE,
        "model": LLM_MODEL,
        "model_is_local": model_is_local,
        "local_only": LLM_ENGINE.lower() in {"openjarvis", "ollama"},
        "engine_url": OLLAMA_HOST if LLM_ENGINE.lower() == "ollama" else None,
        "openjarvis_config": JARVIS_OPENJARVIS_CONFIG,
        "healthy": False,
        "available_models": [],
        "error": None,
    }

    try:
        llm = LLM(model=LLM_MODEL, engine=LLM_ENGINE)
        status["healthy"] = llm.health()
        status["available_models"] = llm.list_models()
    except Exception as exc:
        status["error"] = str(exc)

    return status


def build_report() -> dict[str, Any]:
    return {
        "whisper": whisper_status(),
        "llm": llm_status(),
        "cloud_keys": find_cloud_keys(),
    }


def print_human_report(report: dict[str, Any]) -> None:
    print("Jarvis local health check")
    print("========================")
    print()

    whisper = report["whisper"]
    print("Whisper ASR:")
    print(f"  configured_dir: {whisper['configured_dir']}")
    print(f"  resolved_model_dir: {whisper['resolved_model_dir']}")
    print(f"  exists: {whisper['exists']}")
    print(f"  model.bin found: {whisper['model_bin']}")
    print(f"  likely cache path: {whisper['is_cache_path']}")
    print()

    llm = report["llm"]
    print("LLM backend:")
    print(f"  engine: {llm['engine']}")
    print(f"  model: {llm['model']}")
    print(f"  model_is_local: {llm['model_is_local']}")
    print(f"  local_only: {llm['local_only']}")
    if llm["engine_url"]:
        print(f"  engine_url: {llm['engine_url']}")
    print(f"  openjarvis_config: {llm['openjarvis_config']}")
    print(f"  healthy: {llm['healthy']}")
    if llm["available_models"]:
        print(f"  available_models: {', '.join(llm['available_models'])}")
    if llm["error"]:
        print(f"  error: {llm['error']}")
    print()

    if report["cloud_keys"]:
        print("Cloud API key warnings:")
        for key in report["cloud_keys"]:
            print(f"  - {key}")
        print(
            "AVISO: variáveis de ambiente de nuvem estão definidas. "
            "Remova-as para manter Jarvis 100% offline."
        )
    else:
        print("Nenhuma variável de API de nuvem detectada.")
    print()

    print("Recommendations:")
    if not whisper["exists"] or not whisper["model_bin"]:
        print("  - Verifique o caminho local do Whisper e garanta que model.bin exista.")
    if not llm["healthy"]:
        print("  - Verifique se o backend LLM local está rodando e se o modelo está disponível.")
    if report["cloud_keys"]:
        print("  - Remova chaves de API de provedores em nuvem do ambiente.")
    if whisper["exists"] and whisper["model_bin"] and llm["healthy"] and not report["cloud_keys"]:
        print("  - Seu Jarvis local parece configurado corretamente.")


def main(argv=None) -> int:
    args = parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
