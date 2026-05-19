import os
import secrets
import string
import hashlib
import shutil
import pyzipper

def gerar_senha_segura(tamanho=16):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho))

def calcular_sha256(caminho_arquivo):
    sha256 = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for bloco in iter(lambda: f.read(4096), b""):
            sha256.update(bloco)
    return sha256.hexdigest()

def processar_anexos(pasta_base, protocolo, ano, numero_laudo, callback_status=None, callback_progresso=None):
    """
    Realiza o processamento:
    1. Calcula hash dos arquivos dentro do diretório de anexo e salva o hashes.txt no próprio diretório.
    2. Compacta todos os arquivos no diretório de anexo (com senha).
    3. Calcule a hash do arquivo compactado e gere o arquivo INFO.txt no diretório de anexo.
    """
    pasta_relatorios = os.path.join(pasta_base, 'Relatorios')
    pasta_anexo = os.path.join(pasta_relatorios, 'Anexo Digital')
    
    if not os.path.exists(pasta_anexo):
        os.makedirs(pasta_anexo, exist_ok=True)
        
    nome_zip = f"AnexoDigital_LP_{ano}.{numero_laudo}.zip"
    caminho_zip = os.path.join(pasta_anexo, nome_zip)
    arquivo_info = os.path.join(pasta_anexo, 'INFO.txt')
    arquivo_hashes = os.path.join(pasta_anexo, 'hashes.txt')
    
    # 1. Gerar Hashes dos arquivos em pasta_anexo (excluindo hashes.txt, INFO.txt e zips)
    if callback_progresso:
        callback_progresso(25, "Calculando hashes dos arquivos...")
    elif callback_status:
        callback_status("Calculando hashes dos arquivos...")
        
    # Remove hashes.txt anterior se existir para não dar erro
    if os.path.exists(arquivo_hashes):
        try:
            os.remove(arquivo_hashes)
        except Exception:
            pass
            
    with open(arquivo_hashes, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(pasta_anexo):
            for file in files:
                # Ignora hashes.txt, INFO.txt e qualquer ZIP
                if file in ['hashes.txt', 'INFO.txt'] or file.endswith('.zip'):
                    continue
                filepath = os.path.join(root, file)
                if os.path.isfile(filepath):
                    hash_val = calcular_sha256(filepath)
                    relpath = os.path.relpath(filepath, pasta_anexo)
                    f.write(f"{hash_val} *{relpath}\n")
    
    hash_do_hashes = calcular_sha256(arquivo_hashes) if os.path.exists(arquivo_hashes) else ""
    
    # 2. Compactar
    if callback_progresso:
        callback_progresso(50, "Compactando arquivos com senha...")
    elif callback_status:
        callback_status("Compactando e Criptografando...")
        
    senha = gerar_senha_segura(16)
    hash_diretorio = gerar_senha_segura(16) # Hash aleatorio pro storage
    
    # Se o zip já existe, remove antes de compactar
    if os.path.exists(caminho_zip):
        try:
            os.remove(caminho_zip)
        except Exception:
            pass
            
    with pyzipper.AESZipFile(caminho_zip, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(senha.encode('utf-8'))
        
        for root, dirs, files in os.walk(pasta_anexo):
            for file in files:
                # Ignora o próprio zip e INFO.txt
                if file == nome_zip or file == 'INFO.txt' or file.endswith('.zip.tmp'):
                    continue
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, pasta_anexo)
                zf.write(filepath, relpath)
                
    # 3. Hash do Compactado e Info
    if callback_progresso:
        callback_progresso(75, "Calculando hash do arquivo compactado...")
    elif callback_status:
        callback_status("Calculando hash do arquivo compactado...")
        
    hash_anexo = calcular_sha256(caminho_zip)
    tamanho_gb = round(os.path.getsize(caminho_zip) / (1024**3), 2)
    
    if callback_progresso:
        callback_progresso(100, "Gerando arquivo de informações (INFO.txt)...")
    elif callback_status:
        callback_status("Gerando arquivo de informações...")
        
    url_base = f"https://periciadigital.ssp.to.gov.br/laudos/{ano}/LP_{ano}.{numero_laudo}/{protocolo}/{hash_diretorio}/{nome_zip}"
    
    conteudo_info = f"""Laudo Pericial: LP_{ano}.{numero_laudo}
Protocolo: {protocolo}
Nome do Arquivo: {nome_zip}
URL Storage: {url_base}
Senha do Arquivo: {senha}
Hash SHA-256 do Arquivo Anexo Digital: {hash_anexo}
-----------------------------------------
Hash SHA-256 do arquivo de hashes.txt: {hash_do_hashes}
-----------------------------------------


========================================================================================================
INFORMAÇÕES DO LAUDO PERICIAL
========================================================================================================
Link do Anexo Digital:  
{url_base}

Hash SHA-256 do Arquivo Anexo Digital: 
{hash_anexo}

Hash do hashes.txt SHA-256:
{hash_do_hashes}


========================================================================================================
INFORMAÇÕES DO ANEXO DIGITAL DO GALILEU
========================================================================================================
Hash SHA-256 do Arquivo Anexo Digital: {hash_anexo}
Tamanho em GB: {tamanho_gb}
Link do Anexo Digital:  {url_base}
Senha do Arquivo: {senha}


========================================================================================================
INFORMAÇÕES DO ANEXO DIGITAL DO SGCFF
========================================================================================================
Link do Anexo Digital:  {url_base}
Senha do Arquivo: {senha}
"""
    with open(arquivo_info, 'w', encoding='utf-8') as f:
        f.write(conteudo_info)
        
    if callback_status: callback_status("Processamento concluído com sucesso!")
    
    return {
        'caminho_zip': caminho_zip,
        'hash_diretorio': hash_diretorio,
        'senha': senha,
        'nome_zip': nome_zip
    }

def testar_conexao_storage(storage_base):
    if not os.path.exists(storage_base):
        return False
    return True

def enviar_para_storage(caminho_zip, storage_base, ano, numero_laudo, protocolo, hash_diretorio, callback_status=None, confirmar_sobrescrever=None, cancel_event=None):
    if cancel_event and cancel_event.is_set():
        raise Exception("Envio cancelado pelo usuário.")

    if not testar_conexao_storage(storage_base):
        raise Exception(f"Não foi possível acessar o destino da rede:\n{storage_base}")
        
    if cancel_event and cancel_event.is_set():
        raise Exception("Envio cancelado pelo usuário.")

    dir_destino = os.path.join(storage_base, str(ano), f"LP_{ano}.{numero_laudo}", str(protocolo), hash_diretorio)
    destino_arquivo = os.path.join(dir_destino, os.path.basename(caminho_zip))
    
    # Verifica se o arquivo já existe no destino e solicita autorização para sobrescrever
    if os.path.exists(destino_arquivo):
        if cancel_event and cancel_event.is_set():
            raise Exception("Envio cancelado pelo usuário.")
        if confirmar_sobrescrever:
            sobrescrever = confirmar_sobrescrever(destino_arquivo)
            if not sobrescrever:
                if callback_status: callback_status("Envio cancelado pelo usuário.")
                raise Exception("O arquivo já existe no destino e o envio foi cancelado pelo usuário.")
        else:
            raise Exception("O arquivo já existe no destino.")
            
    if cancel_event and cancel_event.is_set():
        raise Exception("Envio cancelado pelo usuário.")

    if callback_status: callback_status(f"Criando diretório no servidor: {dir_destino}")
    os.makedirs(dir_destino, exist_ok=True)
    
    if cancel_event and cancel_event.is_set():
        raise Exception("Envio cancelado pelo usuário.")

    if callback_status: callback_status("Copiando arquivo para a rede (isso pode demorar)...")
    try:
        with open(caminho_zip, 'rb') as fsrc:
            with open(destino_arquivo, 'wb') as fdst:
                while True:
                    if cancel_event and cancel_event.is_set():
                        fdst.close()
                        try:
                            os.remove(destino_arquivo)
                        except Exception:
                            pass
                        raise Exception("Envio cancelado pelo usuário.")
                    buf = fsrc.read(1024 * 1024)
                    if not buf:
                        break
                    fdst.write(buf)
    except Exception as e:
        if os.path.exists(destino_arquivo) and cancel_event and cancel_event.is_set():
            try:
                os.remove(destino_arquivo)
            except Exception:
                pass
        raise e
    
    if callback_status: callback_status("Arquivo enviado com sucesso!")
    return destino_arquivo
