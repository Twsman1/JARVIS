from jarvis.tools import system, web, files, clipboard, vision_tools

def get_all_tools() -> list:
    """Retorna lista de todas ferramentas disponíveis."""
    return [
        # System tools
        {
            "name": "open_app",
            "description": "Abre um aplicativo pelo nome (ex: notepad, chrome, calculator)",
            "parameters": {
                "name": {
                    "type": "string",
                    "description": "Nome do aplicativo a abrir",
                    "required": True
                }
            }
        },
        {
            "name": "close_app",
            "description": "Fecha um aplicativo pelo nome do processo",
            "parameters": {
                "name": {
                    "type": "string",
                    "description": "Nome do processo a fechar",
                    "required": True
                }
            }
        },
        {
            "name": "take_screenshot",
            "description": "Captura uma screenshot da tela atual",
            "parameters": {
                "filename": {
                    "type": "string",
                    "description": "Nome do arquivo (opcional, usa timestamp se não fornecido)",
                    "required": False
                }
            }
        },
        {
            "name": "get_running_apps",
            "description": "Lista os aplicativos em execução com uso de CPU",
            "parameters": {}
        },
        {
            "name": "type_text",
            "description": "Digita texto na janela ativa",
            "parameters": {
                "text": {
                    "type": "string",
                    "description": "Texto a digitar",
                    "required": True
                }
            }
        },
        {
            "name": "press_key",
            "description": "Pressiona uma tecla ou combinação (ex: enter, ctrl+c, alt+f4)",
            "parameters": {
                "key": {
                    "type": "string",
                    "description": "Tecla ou combinação a pressionar",
                    "required": True
                }
            }
        },
        {
            "name": "set_volume",
            "description": "Ajusta o volume do sistema (0-100)",
            "parameters": {
                "level": {
                    "type": "integer",
                    "description": "Nível de volume (0-100)",
                    "required": True
                }
            }
        },
        {
            "name": "lock_pc",
            "description": "Bloqueia a tela do computador",
            "parameters": {}
        },
        {
            "name": "shutdown_pc",
            "description": "Agenda o desligamento do PC",
            "parameters": {
                "delay_seconds": {
                    "type": "integer",
                    "description": "Segundos até o desligamento (padrão 30)",
                    "required": False
                }
            }
        },
        # Web tools
        {
            "name": "search_web",
            "description": "Pesquisa na web usando DuckDuckGo",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Termo de pesquisa",
                    "required": True
                },
                "max_results": {
                    "type": "integer",
                    "description": "Número máximo de resultados (padrão 3)",
                    "required": False
                }
            }
        },
        {
            "name": "open_url",
            "description": "Abre uma URL no navegador padrão",
            "parameters": {
                "url": {
                    "type": "string",
                    "description": "URL a abrir",
                    "required": True
                }
            }
        },
        {
            "name": "get_page_text",
            "description": "Extrai o texto de uma página web",
            "parameters": {
                "url": {
                    "type": "string",
                    "description": "URL da página",
                    "required": True
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Máximo de caracteres (padrão 2000)",
                    "required": False
                }
            }
        },
        {
            "name": "search_wikipedia",
            "description": "Busca resumo na Wikipedia em português",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Termo de pesquisa",
                    "required": True
                }
            }
        },
        # File tools
        {
            "name": "read_file",
            "description": "Lê o conteúdo de um arquivo texto",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "Caminho do arquivo",
                    "required": True
                }
            }
        },
        {
            "name": "write_file",
            "description": "Escreve ou cria um arquivo texto",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "Caminho do arquivo",
                    "required": True
                },
                "content": {
                    "type": "string",
                    "description": "Conteúdo a escrever",
                    "required": True
                },
                "append": {
                    "type": "boolean",
                    "description": "Se deve adicionar ao final (padrão false)",
                    "required": False
                }
            }
        },
        {
            "name": "list_files",
            "description": "Lista arquivos em um diretório",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "Caminho do diretório (padrão .)",
                    "required": False
                },
                "pattern": {
                    "type": "string",
                    "description": "Padrão de busca (padrão *)",
                    "required": False
                }
            }
        },
        {
            "name": "create_folder",
            "description": "Cria uma pasta",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "Caminho da pasta a criar",
                    "required": True
                }
            }
        },
        {
            "name": "delete_file",
            "description": "Move arquivo para lixeira (não deleta definitivamente)",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "Caminho do arquivo",
                    "required": True
                }
            }
        },
        # Clipboard tools
        {
            "name": "read_clipboard",
            "description": "Lê o conteúdo do clipboard",
            "parameters": {}
        },
        {
            "name": "write_clipboard",
            "description": "Escreve texto no clipboard",
            "parameters": {
                "text": {
                    "type": "string",
                    "description": "Texto a copiar",
                    "required": True
                }
            }        },
        # Vision tools
        {
            "name": "describe_screen",
            "description": "Descreve detalhadamente o que está visível na tela atual usando IA multimodal",
            "parameters": {}
        },
        {
            "name": "read_screen_text",
            "description": "Extrai todo o texto legível na tela usando OCR",
            "parameters": {}
        },
        {
            "name": "answer_about_screen",
            "description": "Responde uma pergunta sobre o conteúdo visível da tela",
            "parameters": {
                "question": {
                    "type": "string",
                    "description": "Pergunta sobre o que está na tela",
                    "required": True
                }
            }
        },
        {
            "name": "read_error_on_screen",
            "description": "Detecta e descreve qualquer mensagem de erro visível na tela",
            "parameters": {}
        },
        {
            "name": "click_on_text",
            "description": "Clica em um elemento na tela identificado por seu texto visível",
            "parameters": {
                "target_text": {
                    "type": "string",
                    "description": "Texto do elemento a clicar",
                    "required": True
                }
            }
        },
        {
            "name": "monitor_screen_change",
            "description": "Monitora a tela até detectar uma mudança visual",
            "parameters": {
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Tempo máximo de espera em segundos (padrão: 30)",
                    "required": False
                }
            }        }
    ]

def get_tools_description() -> str:
    """Retorna descrição formatada de todas as ferramentas para o prompt do LLM."""
    tools = get_all_tools()
    descriptions = []
    for tool in tools:
        params = []
        for param_name, param_info in tool["parameters"].items():
            required = " (obrigatório)" if param_info.get("required", False) else ""
            params.append(f"{param_name}: {param_info['description']}{required}")
        params_str = ", ".join(params) if params else "sem parâmetros"
        descriptions.append(f"- {tool['name']}({params_str}): {tool['description']}")
    return "\n".join(descriptions)