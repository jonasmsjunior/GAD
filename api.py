import os
import requests
import json
from tabulate import tabulate
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

TOKEN_API_GALILEU = os.getenv('TOKEN_API_GALILEU')
ENDERECO_GALILEU = os.getenv('ENDERECO_GALILEU', 'https://galileu.ssp.to.gov.br/galileiWebService')

def consultar_protocolo(protocolo):
    url = f"{ENDERECO_GALILEU}/procedimentopericial/{protocolo}/"
    
    headers = {
        "Authorization": f"Bearer {TOKEN_API_GALILEU}"
    }
    
    resultado = f"Consultando protocolo {protocolo} na URL: {url}...\n\n"
    sucesso = False
    dados_brutos = None
    chaves_retorno = []
    tabela_retorno = []
    
    try:
        response = requests.get(url, headers=headers)
        
        # Tratamento especial para 404
        if response.status_code == 404:
            resultado += "⚠️ PROTOCOLO NÃO ENCONTRADO ⚠️\n"
            return False, resultado, None, [], []
            
        response.raise_for_status()
        
        dados = response.json()
        dados_brutos = dados
        sucesso = True
        resultado += "✅ DADOS RECUPERADOS COM SUCESSO! ✅\n\n"
        
        # Função auxiliar para achatar dicionários aninhados para exibição em tabela
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    items.append((new_key, str(v)))
                else:
                    items.append((new_key, v))
            return dict(items)
            
        def is_empty(val):
            return val in (None, "", [], {})

        if isinstance(dados, dict):
            flat_dados = flatten_dict(dados)
            # Filtra chaves com valores vazios
            tabela = [[chave, valor] for chave, valor in flat_dados.items() if not is_empty(valor)]
            if tabela:
                chaves_retorno = ["Campo", "Valor"]
                tabela_retorno = tabela
                resultado += tabulate(tabela, headers=chaves_retorno, tablefmt="grid")
            else:
                resultado += "A API retornou dados, mas todos os campos estão vazios."
            
        elif isinstance(dados, list):
            if len(dados) > 0:
                flat_lista = [flatten_dict(item) for item in dados if isinstance(item, dict)]
                
                # Identifica chaves que possuem pelo menos um valor útil
                chaves_com_valor = set()
                for item in flat_lista:
                    for k, v in item.items():
                        if not is_empty(v):
                            chaves_com_valor.add(k)
                            
                # Mantém a ordem original das chaves
                todas_chaves_ordenadas = []
                for item in flat_lista:
                    for k in item.keys():
                        if k not in todas_chaves_ordenadas:
                            todas_chaves_ordenadas.append(k)
                            
                chaves = [k for k in todas_chaves_ordenadas if k in chaves_com_valor]
                
                tabela = []
                for item in flat_lista:
                    linha = [item.get(chave, "") for chave in chaves]
                    # Só adiciona a linha se tiver algo útil
                    if any(not is_empty(v) for v in linha):
                        tabela.append(linha)
                        
                if tabela:
                    chaves_retorno = chaves
                    tabela_retorno = tabela
                    resultado += tabulate(tabela, headers=chaves_retorno, tablefmt="grid")
                else:
                    resultado += "A API retornou uma lista, mas todos os campos estão vazios."
            else:
                resultado += "A API retornou uma lista vazia."
        else:
            resultado += f"Formato desconhecido retornado pela API:\n{dados}"
            
    except requests.exceptions.HTTPError as http_err:
        resultado += f"Erro na requisição: {http_err}\n"
        resultado += f"Detalhes: {response.text}"
    except requests.exceptions.RequestException as req_err:
        resultado += f"Erro de conexão: {req_err}"
    except json.JSONDecodeError:
        resultado += "A resposta da API não está em formato JSON válido.\n"
        resultado += response.text
        
    return sucesso, resultado, dados_brutos, chaves_retorno, tabela_retorno
