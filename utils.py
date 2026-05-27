import os
import json
import threading
from datetime import datetime

ARQUIVO_CONFIG = 'config.json'

def carregar_config():
    config = {}
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Erro ao ler {ARQUIVO_CONFIG}: {e}")
    if 'tipos_hash' not in config:
        config['tipos_hash'] = ["SHA-256"]
    return config

def salvar_config(config):
    try:
        with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Erro ao salvar config: {e}")
        return False

def obter_caminho_base(protocolo_str, dados, pasta_raiz):
    if not pasta_raiz or not os.path.isdir(pasta_raiz):
        return None
        
    ano = datetime.now().year
    if isinstance(dados, dict) and 'ano' in dados:
        ano = dados['ano']
    elif isinstance(dados, list) and len(dados) > 0 and isinstance(dados[0], dict) and 'ano' in dados[0]:
        ano = dados[0]['ano']
        
    protocolo_limpo = str(protocolo_str).replace('/', '_').replace('\\', '_')
    nome_pasta_principal = f"{ano}.Prot_{protocolo_limpo}"
    return os.path.join(pasta_raiz, nome_pasta_principal)

def formatar_tamanho(tamanho_bytes):
    tamanho_formatado = tamanho_bytes
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if tamanho_formatado < 1024.0:
            return f"{tamanho_formatado:.2f} {unit}"
        tamanho_formatado /= 1024.0
    return f"{tamanho_formatado:.2f} PB"

def salvar_resumo_txt(caminho_arquivo, protocolo, texto_resultado):
    """
    Salva o texto da consulta em um arquivo TXT amigável
    """
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(f"=== RESUMO DO PROTOCOLO {protocolo} ===\n")
            f.write(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            # Removemos algumas tags e avisos do texto bruto se necessário, ou gravamos como está.
            # texto_resultado contém as emojis e afins, que no txt UTF-8 funcionam bem.
            f.write(texto_resultado)
        return True
    except Exception as e:
        print(f"Erro ao salvar resumo TXT: {e}")
        return False

# ---------------------------------------------------------------------------
# ProtocoloContext – objeto central de estado
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ProtocoloContext:
    """Armazena todas as informações relevantes ao protocolo em execução.
    Essa classe substitui variáveis globais espalhadas pelo código.
    """
    protocolo: str = ""
    dados: Optional[Dict[str, Any]] = None
    caminho_base: str = ""
    texto_resultado: str = ""
    # Campo para armazenar o texto bruto da consulta (usado na UI)
    ano: int = 0
    hash_diretorio: str = ""
    caminho_zip: str = ""
    senha: str = ""
    auto_enviar: bool = True
    numero_laudo: str = ""
    cancel_event: Optional[threading.Event] = None
    caminho_hash_existente: str = ""

    def reset(self):
        """Reseta todos os campos para o estado inicial."""
        self.protocolo = ""
        self.dados = None
        self.caminho_base = ""
        self.numero_laudo = ""
        self.ano = 0
        self.hash_diretorio = ""
        self.caminho_zip = ""
        self.senha = ""
        self.auto_enviar = True
        self.caminho_hash_existente = ""
        if self.cancel_event:
            self.cancel_event.clear()

def tentar_restaurar_processamento(ctx: ProtocoloContext) -> bool:
    """Verifica se o protocolo já possui anexo digital processado e restaura os dados do INFO.txt no contexto.
    Retorna True se conseguir restaurar com sucesso, False caso contrário.
    """
    if not ctx.caminho_base or not os.path.isdir(ctx.caminho_base):
        return False
        
    pasta_anexo = os.path.join(ctx.caminho_base, 'Relatorios', 'Anexo Digital')
    arquivo_info = os.path.join(pasta_anexo, 'INFO.txt')
    
    if not os.path.exists(arquivo_info):
        return False
        
    try:
        nome_zip = None
        senha = None
        url_storage = None
        
        with open(arquivo_info, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                if linha.startswith("Nome do Arquivo:"):
                    nome_zip = linha.split(":", 1)[1].strip()
                elif linha.startswith("Senha do Arquivo:"):
                    senha = linha.split(":", 1)[1].strip()
                elif linha.startswith("URL Storage:"):
                    # split limit handles double slashes in URL
                    url_storage = linha.split(":", 1)[1].strip()
                    
        if nome_zip and senha and url_storage:
            caminho_zip = os.path.join(pasta_anexo, nome_zip)
            if os.path.exists(caminho_zip):
                ctx.caminho_zip = caminho_zip
                ctx.senha = senha
                # Extrai o hash_diretorio da URL
                partes = url_storage.split('/')
                if len(partes) >= 2:
                    ctx.hash_diretorio = partes[-2]
                return True
    except Exception as e:
        print(f"Erro ao tentar restaurar processamento do INFO.txt: {e}")
        
    return False
