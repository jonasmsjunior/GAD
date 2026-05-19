import os
import threading
from typing import Dict
import utils
import anexos

class ServiceError(Exception):
    pass

def processar_anexos(ctx: utils.ProtocoloContext, callback_status=None, callback_progresso=None) -> None:
    """Processa os anexos usando o contexto fornecido.
    Atualiza os campos do contexto com caminho_zip, hash_diretorio e senha.
    """
    if not ctx.caminho_base or not os.path.isdir(ctx.caminho_base):
        raise ServiceError("Diretório base não encontrado.")
    if not ctx.numero_laudo:
        raise ServiceError("Número do laudo não definido.")
    try:
        resultados = anexos.processar_anexos(
            ctx.caminho_base,
            ctx.protocolo,
            ctx.ano,
            ctx.numero_laudo,
            callback_status=callback_status,
            callback_progresso=callback_progresso
        )
        ctx.caminho_zip = resultados.get('caminho_zip', '')
        ctx.hash_diretorio = resultados.get('hash_diretorio', '')
        ctx.senha = resultados.get('senha', '')
    except Exception as e:
        raise ServiceError(str(e))

def enviar_ao_storage(ctx: utils.ProtocoloContext, confirmar_sobrescrever=None, cancel_event=None) -> None:
    """Envia o zip gerado ao storage utilizando informações do contexto."""
    if not ctx.caminho_zip:
        raise ServiceError("Nenhum zip a ser enviado.")
    storage_base = utils.carregar_config().get('destino_storage', r'\\periciadigital.ssp.to.gov.br\Web\laudos')
    try:
        destino = anexos.enviar_para_storage(
            ctx.caminho_zip,
            storage_base,
            ctx.ano,
            ctx.numero_laudo,
            ctx.protocolo,
            ctx.hash_diretorio,
            callback_status=None,
            confirmar_sobrescrever=confirmar_sobrescrever,
            cancel_event=cancel_event
        )
        return destino
    except Exception as e:
        raise ServiceError(str(e))
