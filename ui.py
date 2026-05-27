import os
import sys
import shutil
import json
import threading
from datetime import datetime

import utils
import api
import anexos
import services

# Dynamic fallback import for PySide6 or PyQt6
try:
    from PySide6.QtCore import QThread, Signal, Qt, QEventLoop, QTimer
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                    QLabel, QLineEdit, QPushButton, QCheckBox, QTableWidget, 
                                    QTableWidgetItem, QTextEdit, QProgressBar, QDialog, QFileDialog, 
                                    QHeaderView, QMessageBox, QMenu, QComboBox)
    from PySide6.QtGui import QFont, QColor, QTextCursor, QAction, QPixmap, QIcon
except ImportError:
    from PyQt6.QtCore import QThread, pyqtSignal as Signal, Qt, QEventLoop, QTimer
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                    QLabel, QLineEdit, QPushButton, QCheckBox, QTableWidget, 
                                    QTableWidgetItem, QTextEdit, QProgressBar, QDialog, QFileDialog, 
                                    QHeaderView, QMessageBox, QMenu)
    from PyQt6.QtGui import QFont, QColor, QTextCursor, QAction, QPixmap, QIcon

def obter_caminho_recurso(caminho_relativo):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller e modo de desenvolvimento """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, caminho_relativo)
    return os.path.join(os.path.dirname(__file__), caminho_relativo)

# ---------------------------------------------------------------------------
# QSS Stylesheet - Premium Dark Theme
# ---------------------------------------------------------------------------
STYLING = """
QMainWindow, QDialog {
    background-color: #121214;
    color: #e1e1e6;
}
QWidget {
    color: #e1e1e6;
    font-family: "Segoe UI", "Segoe UI Semibold", sans-serif;
    font-size: 10pt;
}
QLabel {
    color: #c4c4cc;
}
QLabel#lbl_titulo {
    color: #00ADB5;
    font-size: 16pt;
    font-weight: bold;
}
QLineEdit {
    background-color: #202024;
    border: 1px solid #323238;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #00ADB5;
}
QPushButton {
    background-color: #29292e;
    border: 1px solid #323238;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: bold;
    color: #ffffff;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #323238;
    border-color: #00ADB5;
}
QPushButton:pressed {
    background-color: #121214;
}
    QMenu, QMenuBar {
        background-color: #2a2a2a;
        color: #ffffff;
        font-size: 12px;
    }
    QMenu::item {
        padding: 8px 24px;
    }
    QMenu::item:selected {
        background-color: #444444;
        color: #ffffff;
    }

/* Accent Buttons */
QPushButton#btn_consultar {
    background-color: #00ADB5;
    color: #121214;
    border: none;
}
QPushButton#btn_consultar:hover {
    background-color: #00FFF0;
}
QPushButton#btn_criar {
    background-color: #04D361;
    color: #121214;
    border: none;
}
QPushButton#btn_criar:hover {
    background-color: #00FF7F;
}
QPushButton#btn_recriar {
    background-color: #E23E3E;
    color: #ffffff;
    border: none;
}
QPushButton#btn_recriar:hover {
    background-color: #FF5A5A;
}
QPushButton#btn_processar {
    background-color: #9B59B6;
    color: #ffffff;
    border: none;
}
QPushButton#btn_processar:hover {
    background-color: #AF7AC5;
}
QPushButton#btn_enviar {
    background-color: #FF8C00;
    color: #121214;
    border: none;
}
QPushButton#btn_enviar:hover {
    background-color: #FFA500;
}
QPushButton#btn_cancelar {
    background-color: #202024;
    border: 1px solid #E23E3E;
    color: #E23E3E;
}
QPushButton#btn_cancelar:hover {
    background-color: #E23E3E;
    color: #ffffff;
}

QTableWidget {
    background-color: #18181b;
    alternate-background-color: #202024;
    border: 1px solid #323238;
    gridline-color: #323238;
    border-radius: 6px;
}
QTableWidget::item:selected {
    background-color: #29292e;
    border: 1px solid #00ADB5;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #202024;
    color: #c4c4cc;
    border: 1px solid #323238;
    padding: 6px;
    font-weight: bold;
}
QProgressBar {
    background-color: #202024;
    border: 1px solid #323238;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ADB5, stop:1 #00FFF0);
    border-radius: 5px;
}
QTextEdit {
    background-color: #18181b;
    border: 1px solid #323238;
    border-radius: 6px;
    font-family: "Courier New", monospace;
    font-size: 10pt;
    padding: 8px;
    color: #e1e1e6;
}
QScrollBar:vertical {
    background-color: #121214;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #29292e;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background-color: #323238;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #202024;
    border: 1px solid #323238;
    border-radius: 4px;
}
QCheckBox::indicator:hover {
    border-color: #00ADB5;
}
QCheckBox::indicator:checked {
    background-color: #00ADB5;
    border: 4px solid #202024;
}
"""

# Light mode stylesheet (minimal premium)
LIGHT_STYLING = """
QMainWindow, QDialog {
    background-color: #f5f5f5;
    color: #212121;
}
QWidget {
    color: #212121;
    font-family: "Segoe UI", "Segoe UI Semibold", sans-serif;
    font-size: 10pt;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    color: #212121;
}
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #b0b0b0;
    color: #212121;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QMenu, QMenuBar {
    background-color: #e0e0e0;
    color: #212121;
    font-size: 14px;
}
QMenu::item:selected {
    background-color: #c0c0c0;
}
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f0f0f0;
}
QHeaderView::section {
    background-color: #e0e0e0;
    color: #212121;
}
"""

# ---------------------------------------------------------------------------
# Background Workers (QThread implementations)
# ---------------------------------------------------------------------------

class QueryWorker(QThread):
    finished_signal = Signal(bool, str, object, list, list)

    def __init__(self, protocolo):
        super().__init__()
        self.protocolo = protocolo

    def run(self):
        try:
            sucesso, resultado, dados_brutos, chaves, tabela = api.consultar_protocolo(self.protocolo)
            self.finished_signal.emit(sucesso, resultado, dados_brutos, chaves, tabela)
        except Exception as e:
            self.finished_signal.emit(False, f"Erro inesperado na consulta: {e}", None, [], [])


class ProcessWorker(QThread):
    progress_signal = Signal(int, str)
    log_signal = Signal(str, str) # (message, type) -> success, error, warning, info
    finished_signal = Signal(bool, str)

    def __init__(self, ctx, auto_enviar, parent_window):
        super().__init__()
        self.ctx = ctx
        self.auto_enviar = auto_enviar
        self.parent_window = parent_window
        self.ultima_etapa = None

    def progresso_callback(self, pct, desc):
        etapa_str = ""
        if pct == 25:
            etapa_str = "[Etapa 1/4] "
        elif pct == 50:
            etapa_str = "[Etapa 2/4] "
        elif pct == 75:
            etapa_str = "[Etapa 3/4] "
        elif pct == 100:
            etapa_str = "[Etapa 4/4] "
        self.progress_signal.emit(pct, f"{etapa_str}{desc}")
        
        # Se havia uma etapa anterior sendo processada, finaliza com OK
        if self.ultima_etapa:
            self.log_signal.emit(f"   └─ Concluído com sucesso! [OK]", "success")
            
        self.log_signal.emit(f"-> {etapa_str}{desc} ...", "info")
        self.ultima_etapa = desc

    def run(self):
        try:
            self.log_signal.emit("Iniciando processamento de anexos...\n", "info")
            services.processar_anexos(self.ctx, callback_progresso=self.progresso_callback)
            
            # Conclui a última etapa do processamento antes de prosseguir
            if self.ultima_etapa:
                self.log_signal.emit(f"   └─ Concluído com sucesso! [OK]", "success")
                self.ultima_etapa = None
                
            if self.auto_enviar:
                self.progress_signal.emit(100, "Copiando arquivo para a rede...")
                self.log_signal.emit("-> [Envio] Copiando arquivo para a rede ...", "info")
                self.ctx.cancel_event.clear()
                
                destino = services.enviar_ao_storage(
                    self.ctx, 
                    confirmar_sobrescrever=self.parent_window.perguntar_sobrescrever, 
                    cancel_event=self.ctx.cancel_event
                )
                
                if not (self.ctx.cancel_event and self.ctx.cancel_event.is_set()):
                    self.log_signal.emit(f"   └─ Concluído com sucesso! [OK]", "success")
                    self.log_signal.emit(f"\n[SUCESSO] Processamento e envio concluídos!\nSalvo em rede: {destino}\n", "success")
                    self.finished_signal.emit(True, destino)
                else:
                    self.log_signal.emit("\n[AVISO] Envio cancelado pelo usuário.\n", "warning")
                    self.finished_signal.emit(False, "Cancelado")
            else:
                self.log_signal.emit("\n[SUCESSO] Processamento de anexos concluído localmente!\n", "success")
                self.finished_signal.emit(True, "Local")
        except Exception as e:
            self.log_signal.emit(f"\n[ERRO] Falha no processamento: {e}\n", "error")
            self.finished_signal.emit(False, str(e))


class UploadWorker(QThread):
    log_signal = Signal(str, str)
    finished_signal = Signal(bool, str)

    def __init__(self, ctx, parent_window):
        super().__init__()
        self.ctx = ctx
        self.parent_window = parent_window

    def run(self):
        self.ctx.cancel_event.clear()
        try:
            destino = services.enviar_ao_storage(
                self.ctx, 
                confirmar_sobrescrever=self.parent_window.perguntar_sobrescrever, 
                cancel_event=self.ctx.cancel_event
            )
            if not (self.ctx.cancel_event and self.ctx.cancel_event.is_set()):
                self.finished_signal.emit(True, destino)
            else:
                self.finished_signal.emit(False, "Cancelado")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class SizeCalculatorWorker(QThread):
    item_calculated = Signal(str, str) # name, formatted size
    finished_signal = Signal()

    def __init__(self, pasta_raiz):
        super().__init__()
        self.pasta_raiz = pasta_raiz

    def run(self):
        if not self.pasta_raiz or not os.path.isdir(self.pasta_raiz):
            self.finished_signal.emit()
            return
        
        try:
            for nome_pasta in os.listdir(self.pasta_raiz):
                caminho_completo = os.path.join(self.pasta_raiz, nome_pasta)
                if os.path.isdir(caminho_completo):
                    tamanho_bytes = 0
                    for dirpath, _, filenames in os.walk(caminho_completo):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            if not os.path.islink(fp):
                                try:
                                    tamanho_bytes += os.path.getsize(fp)
                                except OSError:
                                    pass
                    tamanho_formatado = utils.formatar_tamanho(tamanho_bytes)
                    self.item_calculated.emit(nome_pasta, tamanho_formatado)
        except Exception as e:
            print(f"Erro ao calcular tamanhos: {e}")
        self.finished_signal.emit()


class BatchWorker(QThread):
    progress_signal = Signal(int, str) # pct, description
    log_signal = Signal(str, str)      # message, style
    finished_signal = Signal(int, int) # sucessos, erros
    
    def __init__(self, task_type, selected_folders, pasta_raiz, destino_storage, destino_backup, auto_enviar, parent_dlg):
        super().__init__()
        self.task_type = task_type
        self.selected_folders = selected_folders
        self.pasta_raiz = pasta_raiz
        self.destino_storage = destino_storage
        self.destino_backup = destino_backup
        self.auto_enviar = auto_enviar
        self.parent_dlg = parent_dlg
        self.cancel_event = threading.Event()

    def obter_contexto_pasta(self, nome_pasta):
        caminho_pasta = os.path.join(self.pasta_raiz, nome_pasta)
        protocolo = ""
        if ".Prot_" in nome_pasta:
            protocolo = nome_pasta.split(".Prot_")[1]
        
        caminho_json = os.path.join(caminho_pasta, 'Laudo', 'dados_protocolo.json')
        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                local_ctx = utils.ProtocoloContext()
                local_ctx.dados = dados
                local_ctx.protocolo = protocolo
                local_ctx.caminho_base = caminho_pasta
                utils.tentar_restaurar_processamento(local_ctx)
                return local_ctx
            except Exception:
                return None
        return None

    def run(self):
        sucessos = 0
        erros = 0
        pulados = 0
        total = len(self.selected_folders)

        if total == 0:
            self.finished_signal.emit(0, 0)
            return

        self.log_signal.emit(f"Iniciando execução em lote de {total} processo(s)...", "info")

        for i, nome_pasta in enumerate(self.selected_folders):
            if self.cancel_event.is_set():
                self.log_signal.emit("\n[AVISO] Operação em lote cancelada pelo usuário.", "warning")
                break

            pct_base = int((i / total) * 100)
            self.log_signal.emit(f"\n========================================\n[{i+1}/{total}] PROCESSO: {nome_pasta}\n========================================", "info")
            
            # --- TAREFA: LIMPAR EXTRAÇÃO ---
            if self.task_type == 'clear':
                self.progress_signal.emit(pct_base, f"[{i+1}/{total}] {nome_pasta} - Limpando extração...")
                self.log_signal.emit("-> Limpando pasta de extração...", "info")
                local_ctx = self.obter_contexto_pasta(nome_pasta)
                if not local_ctx or not local_ctx.caminho_base:
                    self.log_signal.emit("   └─ [ERRO] Contexto da pasta inválido.", "error")
                    erros += 1
                    continue
                caminho_extracao = os.path.join(local_ctx.caminho_base, 'Extração')
                try:
                    if os.path.exists(caminho_extracao):
                        shutil.rmtree(caminho_extracao)
                    os.makedirs(caminho_extracao, exist_ok=True)
                    self.log_signal.emit("   └─ Limpeza concluída com sucesso! [OK]", "success")
                    sucessos += 1
                except Exception as e:
                    self.log_signal.emit(f"   └─ [ERRO] Falha ao limpar: {e}", "error")
                    erros += 1

            # --- TAREFA: RECOMPILAR / RECOMPACTAR E BACKUP ---
            elif self.task_type == 'backup':
                self.log_signal.emit("-> Executando Backup & Limpeza...", "info")
                local_ctx = self.obter_contexto_pasta(nome_pasta)
                if not local_ctx or not local_ctx.caminho_base:
                    self.log_signal.emit("   └─ [ERRO] Contexto da pasta inválido.", "error")
                    erros += 1
                    continue
                caminho_zip_local = os.path.join(self.pasta_raiz, f"{nome_pasta}.zip")
                caminho_backup_final = os.path.join(self.destino_backup, f"{nome_pasta}.zip")
                
                if os.path.exists(caminho_backup_final):
                    self.log_signal.emit(f"   [!] O arquivo '{nome_pasta}.zip' já existe no backup. Aguardando confirmação...", "warning")
                    # Solicita resposta da thread principal
                    sobrescrever = self.parent_dlg.perguntar_sobrescrever_backup_lote(nome_pasta)
                    if not sobrescrever:
                        self.log_signal.emit("   [!] Sobrescrita negada. Pulando este processo.", "warning")
                        pulados += 1
                        continue
                    else:
                        self.log_signal.emit("   [!] Sobrescrita confirmada.", "info")
                
                try:
                    self.progress_signal.emit(int((i * 100 + 20) / total), f"[{i+1}/{total}] {nome_pasta} - Compactando pasta...")
                    self.log_signal.emit("   -> Criando arquivo ZIP local...", "info")
                    shutil.make_archive(
                        base_name=os.path.join(self.pasta_raiz, nome_pasta),
                        format='zip',
                        root_dir=self.pasta_raiz,
                        base_dir=nome_pasta
                    )
                    
                    self.progress_signal.emit(int((i * 100 + 40) / total), f"[{i+1}/{total}] {nome_pasta} - Copiando p/ Backup...")
                    self.log_signal.emit("   -> Copiando ZIP para o destino de backup...", "info")
                    shutil.copy2(caminho_zip_local, caminho_backup_final)
                    
                    self.progress_signal.emit(int((i * 100 + 60) / total), f"[{i+1}/{total}] {nome_pasta} - Verificando integridade...")
                    self.log_signal.emit("   -> Verificando integridade do backup...", "info")
                    if os.path.exists(caminho_backup_final) and os.path.getsize(caminho_backup_final) == os.path.getsize(caminho_zip_local):
                        self.progress_signal.emit(int((i * 100 + 80) / total), f"[{i+1}/{total}] {nome_pasta} - Removendo originais...")
                        self.log_signal.emit("   -> Removendo pasta local original e ZIP temporário...", "info")
                        shutil.rmtree(local_ctx.caminho_base)
                        if os.path.exists(caminho_zip_local):
                            os.remove(caminho_zip_local)
                        self.log_signal.emit("   └─ Backup e Limpeza concluídos com sucesso! [OK]", "success")
                        sucessos += 1
                    else:
                        raise Exception("Erro de validação de tamanho no backup")
                except Exception as e:
                    self.log_signal.emit(f"   └─ [ERRO] Falha no Backup: {e}", "error")
                    try:
                        if os.path.exists(caminho_zip_local):
                            os.remove(caminho_zip_local)
                    except Exception:
                        pass
                    erros += 1

            # --- TAREFA: RE-CRIAR DIRETÓRIOS ---
            elif self.task_type == 'recreate':
                self.progress_signal.emit(pct_base, f"[{i+1}/{total}] {nome_pasta} - Recriando diretórios...")
                self.log_signal.emit("-> Recriando estrutura de diretórios GAD...", "info")
                local_ctx = self.obter_contexto_pasta(nome_pasta)
                if not local_ctx:
                    self.log_signal.emit("   └─ [ERRO] Não foi possível obter o contexto da pasta.", "error")
                    erros += 1
                    continue
                resumo_txt = ""
                caminho_txt = os.path.join(local_ctx.caminho_base, 'Laudo', 'Resumo_Laudo.txt')
                if os.path.exists(caminho_txt):
                    try:
                        with open(caminho_txt, 'r', encoding='utf-8') as f_txt:
                            resumo_txt = f_txt.read()
                    except Exception:
                        pass
                try:
                    shutil.rmtree(local_ctx.caminho_base)
                    pastas_para_criar = ['Extração', 'Fotos', 'Laudo', 'Relatorios', 'Relatorios/Anexo Digital']
                    os.makedirs(local_ctx.caminho_base, exist_ok=True)
                    for p in pastas_para_criar:
                        os.makedirs(os.path.join(local_ctx.caminho_base, p), exist_ok=True)
                    caminho_json = os.path.join(local_ctx.caminho_base, 'Laudo', 'dados_protocolo.json')
                    with open(caminho_json, 'w', encoding='utf-8') as f:
                        json.dump(local_ctx.dados, f, indent=4, ensure_ascii=False)
                    if resumo_txt:
                        utils.salvar_resumo_txt(caminho_txt, local_ctx.protocolo, resumo_txt)
                    self.log_signal.emit("   └─ Diretórios recriados com sucesso! [OK]", "success")
                    sucessos += 1
                except Exception as e:
                    self.log_signal.emit(f"   └─ [ERRO] Falha ao recriar: {e}", "error")
                    erros += 1

            # --- TAREFA: PROCESSAR ANEXOS ---
            elif self.task_type == 'process':
                local_ctx = self.obter_contexto_pasta(nome_pasta)
                if not local_ctx:
                    self.log_signal.emit("   └─ [ERRO] Não foi possível carregar o contexto da pasta.", "error")
                    erros += 1
                    continue

                laudo_criado = False
                num_laudo = None
                ano_laudo = None
                if isinstance(local_ctx.dados, dict) and 'laudo' in local_ctx.dados and local_ctx.dados['laudo']:
                    numero_completo = local_ctx.dados['laudo'].get('numeroCompleto')
                    if numero_completo:
                        laudo_criado = True
                        if '.' in numero_completo:
                            partes = numero_completo.split('.')
                            try:
                                ano_laudo = int(partes[0])
                            except ValueError:
                                pass
                            num_laudo = partes[1]
                        else:
                            num_laudo = str(numero_completo)
                
                if not laudo_criado or not num_laudo:
                    self.log_signal.emit("   └─ [ERRO] Nenhum laudo associado no Galileu para este protocolo.", "error")
                    erros += 1
                    continue

                local_ctx.numero_laudo = num_laudo
                local_ctx.ano = ano_laudo if ano_laudo else datetime.now().year
                local_ctx.auto_enviar = self.auto_enviar
                local_ctx.cancel_event = self.cancel_event

                self.log_signal.emit(f"-> Processando anexos para o Laudo: LP_{local_ctx.ano}.{local_ctx.numero_laudo}", "info")

                def local_cb(pct, desc):
                    prog_pct = int((i * 100 + pct) / total)
                    self.progress_signal.emit(prog_pct, f"[{i+1}/{total}] {nome_pasta} - {desc}")
                    self.log_signal.emit(f"   -> {desc} ...", "info")

                try:
                    services.processar_anexos(local_ctx, callback_progresso=local_cb)
                    self.log_signal.emit("   └─ Concluído com sucesso! [OK]", "success")
                    sucessos += 1
                    
                    if self.auto_enviar:
                        self.progress_signal.emit(int(((i + 0.5) * 100) / total), f"[{i+1}/{total}] {nome_pasta} - Enviando Storage...")
                        self.log_signal.emit("   -> Enviando arquivo compactado ao Storage...", "info")
                        destino = services.enviar_ao_storage(
                            local_ctx, 
                            confirmar_sobrescrever=self.parent_dlg.perguntar_sobrescrever_storage_lote, 
                            cancel_event=self.cancel_event
                        )
                        self.log_signal.emit(f"   └─ Enviado ao Storage com sucesso: {destino} [OK]", "success")
                except Exception as e:
                    self.log_signal.emit(f"   └─ [ERRO] Falha no processamento/envio: {e}", "error")
                    erros += 1

            # --- TAREFA: ENVIAR PARA STORAGE ---
            elif self.task_type == 'upload':
                self.progress_signal.emit(pct_base, f"[{i+1}/{total}] {nome_pasta} - Enviando Storage...")
                self.log_signal.emit("-> Iniciando upload ao Storage...", "info")
                local_ctx = self.obter_contexto_pasta(nome_pasta)
                if not local_ctx:
                    self.log_signal.emit("   └─ [ERRO] Não foi possível obter o contexto da pasta.", "error")
                    erros += 1
                    continue
                if not local_ctx.caminho_zip or not os.path.exists(local_ctx.caminho_zip):
                    utils.tentar_restaurar_processamento(local_ctx)
                    if not local_ctx.caminho_zip or not os.path.exists(local_ctx.caminho_zip):
                        self.log_signal.emit("   └─ [ERRO] Arquivo RAR do anexo digital não foi encontrado localmente. Processe primeiro.", "error")
                        erros += 1
                        continue

                laudo_criado = False
                num_laudo = None
                ano_laudo = None
                if isinstance(local_ctx.dados, dict) and 'laudo' in local_ctx.dados and local_ctx.dados['laudo']:
                    numero_completo = local_ctx.dados['laudo'].get('numeroCompleto')
                    if numero_completo:
                        laudo_criado = True
                        if '.' in numero_completo:
                            partes = numero_completo.split('.')
                            try:
                                ano_laudo = int(partes[0])
                            except ValueError:
                                pass
                            num_laudo = partes[1]
                        else:
                            num_laudo = str(numero_completo)
                
                if not num_laudo:
                    self.log_signal.emit("   └─ [ERRO] Nenhum laudo associado no Galileu.", "error")
                    erros += 1
                    continue
                
                local_ctx.numero_laudo = num_laudo
                local_ctx.ano = ano_laudo if ano_laudo else datetime.now().year
                local_ctx.cancel_event = self.cancel_event

                self.log_signal.emit(f"   -> Copiando '{os.path.basename(local_ctx.caminho_zip)}' para a rede...", "info")

                try:
                    destino = services.enviar_ao_storage(
                        local_ctx, 
                        confirmar_sobrescrever=self.parent_dlg.perguntar_sobrescrever_storage_lote, 
                        cancel_event=self.cancel_event
                    )
                    self.log_signal.emit(f"   └─ Upload concluído com sucesso: {destino} [OK]", "success")
                    sucessos += 1
                except Exception as e:
                    self.log_signal.emit(f"   └─ [ERRO] Falha no upload: {e}", "error")
                    erros += 1

        self.log_signal.emit(f"\n>>> EXECUÇÃO FINALIZADA. Sucessos: {sucessos}, Erros: {erros}.", "success" if erros == 0 else "warning")
        self.finished_signal.emit(sucessos, erros)


# ---------------------------------------------------------------------------
# Settings Dialog (Configurações)
# ---------------------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sistema do GAD")
        self.setMinimumWidth(550)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Pasta Raiz Local
        layout.addWidget(QLabel("<b>Pasta Raiz Local:</b>"))
        h_layout1 = QHBoxLayout()
        self.entry_raiz = QLineEdit()
        self.btn_buscar_raiz = QPushButton("Buscar")
        self.btn_buscar_raiz.clicked.connect(self.buscar_raiz)
        h_layout1.addWidget(self.entry_raiz)
        h_layout1.addWidget(self.btn_buscar_raiz)
        layout.addLayout(h_layout1)

        # Destino Storage
        layout.addWidget(QLabel("<b>Destino Storage (Rede):</b>"))
        self.entry_storage = QLineEdit()
        layout.addWidget(self.entry_storage)

        # Destino Backup
        layout.addWidget(QLabel("<b>Destino de Backup:</b>"))
        h_layout2 = QHBoxLayout()
        self.entry_backup = QLineEdit()
        self.btn_buscar_backup = QPushButton("Buscar")
        self.btn_buscar_backup.clicked.connect(self.buscar_backup)
        h_layout2.addWidget(self.entry_backup)
        h_layout2.addWidget(self.btn_buscar_backup)
        layout.addLayout(h_layout2)

        # Tipos de Hash
        layout.addWidget(QLabel("<b>Tipos de Hash a Calcular:</b>"))
        h_layout_hashes = QHBoxLayout()
        self.chk_md5 = QCheckBox("MD5")
        self.chk_sha1 = QCheckBox("SHA-1")
        self.chk_sha256 = QCheckBox("SHA-256")
        self.chk_sha512 = QCheckBox("SHA-512")
        h_layout_hashes.addWidget(self.chk_md5)
        h_layout_hashes.addWidget(self.chk_sha1)
        h_layout_hashes.addWidget(self.chk_sha256)
        h_layout_hashes.addWidget(self.chk_sha512)
        h_layout_hashes.addStretch()
        layout.addLayout(h_layout_hashes)

        # Tema (Dark / Light)
        layout.addWidget(QLabel("<b>Tema:</b>"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Dark", "Light"])
        layout.addWidget(self.combo_tema)

        # Buttons
        h_buttons = QHBoxLayout()
        h_buttons.addStretch()
        self.btn_salvar = QPushButton("Salvar Sistema")
        self.btn_salvar.setObjectName("btn_consultar") # cyan accent
        self.btn_salvar.clicked.connect(self.salvar)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        h_buttons.addWidget(self.btn_cancelar)
        h_buttons.addWidget(self.btn_salvar)
        
        layout.addSpacing(10)
        layout.addLayout(h_buttons)

        self.carregar_configuracoes()  # permanece, método mantém nome

    def carregar_configuracoes(self):
        config = utils.carregar_config()
        self.entry_raiz.setText(config.get('pasta_raiz', ''))
        self.entry_storage.setText(config.get('destino_storage', r'\\periciadigital.ssp.to.gov.br\Web\laudos'))
        self.entry_backup.setText(config.get('destino_backup', ''))
        self.combo_tema.setCurrentText(config.get('tema', 'Dark'))
        
        tipos_hash = config.get('tipos_hash', ["SHA-256"])
        self.chk_md5.setChecked("MD5" in tipos_hash)
        self.chk_sha1.setChecked("SHA-1" in tipos_hash)
        self.chk_sha256.setChecked("SHA-256" in tipos_hash)
        self.chk_sha512.setChecked("SHA-512" in tipos_hash)

    def buscar_raiz(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Raiz")
        if dir_path:
            self.entry_raiz.setText(dir_path)

    def buscar_backup(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Backup")
        if dir_path:
            self.entry_backup.setText(dir_path)

    def salvar(self):
        tipos_hash = []
        if self.chk_md5.isChecked():
            tipos_hash.append("MD5")
        if self.chk_sha1.isChecked():
            tipos_hash.append("SHA-1")
        if self.chk_sha256.isChecked():
            tipos_hash.append("SHA-256")
        if self.chk_sha512.isChecked():
            tipos_hash.append("SHA-512")
            
        if not tipos_hash:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione ao menos um tipo de Hash a ser calculado.")
            return

        config = {
            'pasta_raiz': self.entry_raiz.text().strip(),
            'destino_storage': self.entry_storage.text().strip(),
            'destino_backup': self.entry_backup.text().strip(),
            'tema': self.combo_tema.currentText(),
            'tipos_hash': tipos_hash
        }
        if utils.salvar_config(config):
            QMessageBox.information(self, "Sucesso", "Sistema salvo com sucesso!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar o sistema.")


# ---------------------------------------------------------------------------
# Processes Manager Dialog (Processos Locais)
# ---------------------------------------------------------------------------

class ProcessesDialog(QDialog):
    sig_perguntar_sobrescrever_storage = Signal(str)
    sig_perguntar_sobrescrever_backup = Signal(str)

    def __init__(self, main_ctx, config, parent=None):
        super().__init__(parent)
        self.main_ctx = main_ctx
        self.config = config
        self.setWindowTitle("Processos Locais")
        self.resize(850, 520)
        
        self.batch_worker = None
        self.calc_worker = None
        self.sobrescrever_storage_result = False
        self.sobrescrever_storage_event = threading.Event()
        self.sobrescrever_backup_result = False
        self.sobrescrever_backup_event = threading.Event()

        self.sig_perguntar_sobrescrever_storage.connect(self._on_perguntar_storage)
        self.sig_perguntar_sobrescrever_backup.connect(self._on_perguntar_backup)

        # Timer para animações de loading nos status
        self.loading_timer = QTimer(self)
        self.loading_timer.setInterval(400)
        self.loading_timer.timeout.connect(self.atualizar_animacao_status)
        self.base_status_text = ""
        self.loading_state = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Status Label
        self.lbl_status = QLabel("Carregando processos... aguarde.")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #00ADB5;")
        layout.addWidget(self.lbl_status)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["", "Nome da Pasta", "Tamanho Ocupado", "Situação"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.ao_selecionar_pasta)
        self.table.itemChanged.connect(self.ao_alterar_item)
        layout.addWidget(self.table)

        # Seleção em lote
        h_selecao = QHBoxLayout()
        self.btn_selecionar_todos = QPushButton("Selecionar Todos")
        self.btn_selecionar_todos.clicked.connect(self.selecionar_todos)
        self.btn_desmarcar_todos = QPushButton("Limpar Seleção")
        self.btn_desmarcar_todos.clicked.connect(self.desmarcar_todos)
        h_selecao.addWidget(self.btn_selecionar_todos)
        h_selecao.addWidget(self.btn_desmarcar_todos)
        h_selecao.addStretch()
        layout.addLayout(h_selecao)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Action Buttons Layout
        self.frame_acoes = QHBoxLayout()
        
        self.btn_recriar = QPushButton("ReCriar Diretórios")
        self.btn_recriar.clicked.connect(self.recriar_diretorios_lote)
        
        self.btn_processar = QPushButton("1. Processar Anexos")
        self.btn_processar.setObjectName("btn_processar")
        self.btn_processar.clicked.connect(self.processar_anexos_lote)

        self.btn_reprocessar = QPushButton("ReProcessar")
        self.btn_reprocessar.clicked.connect(self.processar_anexos_lote)

        self.btn_abrir = QPushButton("Abrir Pasta")
        self.btn_abrir.clicked.connect(self.abrir_pasta)

        self.btn_enviar = QPushButton("2. Enviar p/ Storage")
        self.btn_enviar.setObjectName("btn_enviar")
        self.btn_enviar.clicked.connect(self.enviar_storage_lote)

        self.btn_limpar = QPushButton("Limpar Extração")
        self.btn_limpar.clicked.connect(self.limpar_extracao_lote)

        self.btn_backup = QPushButton("Backup & Limpar")
        self.btn_backup.clicked.connect(self.backup_limpar_lote)

        self.chk_auto = QCheckBox("Auto Enviar")
        self.chk_auto.setChecked(True)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.cancelar_lote)

        self.frame_acoes.addWidget(self.chk_auto)
        self.frame_acoes.addWidget(self.btn_recriar)
        self.frame_acoes.addWidget(self.btn_processar)
        self.frame_acoes.addWidget(self.btn_reprocessar)
        self.frame_acoes.addWidget(self.btn_abrir)
        self.frame_acoes.addWidget(self.btn_enviar)
        self.frame_acoes.addWidget(self.btn_limpar)
        self.frame_acoes.addWidget(self.btn_backup)
        self.frame_acoes.addWidget(self.btn_cancelar)

        layout.addLayout(self.frame_acoes)

        # Console Log para Lote
        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setPlaceholderText("Logs da execução em lote serão exibidos aqui...")
        self.txt_console.setMinimumHeight(150)
        self.txt_console.setMaximumHeight(220)
        layout.addWidget(self.txt_console)

        self.atualizar_tamanhos_tabela()
        self.atualizar_botoes()

    def ao_alterar_item(self, item):
        if item.column() == 0:
            self.atualizar_botoes()

    def selecionar_todos(self):
        self.table.itemChanged.disconnect(self.ao_alterar_item)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
        self.table.itemChanged.connect(self.ao_alterar_item)
        self.atualizar_botoes()

    def desmarcar_todos(self):
        self.table.itemChanged.disconnect(self.ao_alterar_item)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.table.itemChanged.connect(self.ao_alterar_item)
        self.atualizar_botoes()

    def log_lote(self, text, style="info"):
        cursor = self.txt_console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        color = "#e1e1e6" # default
        font_weight = "normal"
        if style == "success":
            color = "#04D361"
            font_weight = "bold"
        elif style == "error":
            color = "#E23E3E"
            font_weight = "bold"
        elif style == "warning":
            color = "#FF8C00"
            font_weight = "bold"
            
        html = f'<span style="color: {color}; font-weight: {font_weight};">{text}</span>'
        cursor.insertHtml(html)
        cursor.insertText("\n")
        self.txt_console.setTextCursor(cursor)
        self.txt_console.ensureCursorVisible()

    def popular_linha_tabela(self, nome_pasta, tamanho_formatado):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.itemChanged.disconnect(self.ao_alterar_item)
        
        item_check = QTableWidgetItem()
        item_check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item_check.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, item_check)
        
        item_nome = QTableWidgetItem(nome_pasta)
        item_nome.setFlags(item_nome.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, item_nome)
        
        item_tam = QTableWidgetItem(tamanho_formatado)
        item_tam.setFlags(item_tam.flags() ^ Qt.ItemFlag.ItemIsEditable)
        item_tam.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 2, item_tam)
        
        local_ctx = self.obter_contexto_pasta(nome_pasta)
        situacao = "Não Processado"
        if local_ctx:
            processado = utils.tentar_restaurar_processamento(local_ctx)
            if processado:
                if self.verificar_se_ja_enviado(local_ctx):
                    situacao = "Enviado"
                else:
                    situacao = "Processado"
        
        item_sit = QTableWidgetItem(situacao)
        item_sit.setFlags(item_sit.flags() ^ Qt.ItemFlag.ItemIsEditable)
        if situacao == "Enviado":
            item_sit.setForeground(QColor("#04D361"))
        elif situacao == "Processado":
            item_sit.setForeground(QColor("#9B59B6"))
        else:
            item_sit.setForeground(QColor("#FF8C00"))
        self.table.setItem(row, 3, item_sit)
        
        self.table.itemChanged.connect(self.ao_alterar_item)

    def atualizar_animacao_status(self):
        if not self.base_status_text:
            return
        frames = [" .  ", " .. ", " ...", "   "]
        frame = frames[self.loading_state % len(frames)]
        self.loading_state += 1
        
        texto_base = self.base_status_text.rstrip(" .")
        self.lbl_status.setText(f"{texto_base}{frame}")

    def calc_finished(self):
        self.loading_timer.stop()
        self.lbl_status.setText("Cálculo concluído.")
        self.atualizar_botoes()

    def atualizar_tamanhos_tabela(self):
        self.table.setRowCount(0)
        self.base_status_text = "Calculando tamanhos dos diretórios..."
        self.lbl_status.setText(self.base_status_text)
        self.loading_timer.start(300)
        
        pasta_raiz = self.config.get('pasta_raiz')
        if not pasta_raiz or not os.path.isdir(pasta_raiz):
            self.loading_timer.stop()
            self.lbl_status.setText("Pasta raiz local inválida.")
            return

        self.calc_worker = SizeCalculatorWorker(pasta_raiz)
        self.calc_worker.item_calculated.connect(self.popular_linha_tabela)
        self.calc_worker.finished_signal.connect(self.calc_finished)
        self.calc_worker.start()

    def obter_contexto_pasta(self, nome_pasta):
        pasta_raiz = self.config.get('pasta_raiz')
        caminho_pasta = os.path.join(pasta_raiz, nome_pasta)
        protocolo = ""
        if ".Prot_" in nome_pasta:
            protocolo = nome_pasta.split(".Prot_")[1]
        
        caminho_json = os.path.join(caminho_pasta, 'Laudo', 'dados_protocolo.json')
        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                local_ctx = utils.ProtocoloContext()
                local_ctx.dados = dados
                local_ctx.protocolo = protocolo
                local_ctx.caminho_base = caminho_pasta
                utils.tentar_restaurar_processamento(local_ctx)
                return local_ctx
            except Exception:
                return None
        return None

    def ao_selecionar_pasta(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.atualizar_botoes()
            return
        
        # O primeiro item selecionado
        row = selected_items[0].row()
        nome_pasta = self.table.item(row, 1).text()
        
        pasta_raiz = self.config.get('pasta_raiz')
        caminho_pasta = os.path.join(pasta_raiz, nome_pasta)
        
        protocolo = ""
        if ".Prot_" in nome_pasta:
            protocolo = nome_pasta.split(".Prot_")[1]
        
        caminho_json = os.path.join(caminho_pasta, 'Laudo', 'dados_protocolo.json')
        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self.main_ctx.dados = dados
                self.main_ctx.protocolo = protocolo
                self.main_ctx.caminho_base = caminho_pasta
                self.main_ctx.caminho_zip = ""
                self.main_ctx.senha = ""
                self.main_ctx.hash_diretorio = ""
                self.main_ctx.ano = 0
                self.main_ctx.numero_laudo = ""
                utils.tentar_restaurar_processamento(self.main_ctx)
                
                caminho_txt = os.path.join(caminho_pasta, 'Laudo', 'Resumo_Laudo.txt')
                if os.path.exists(caminho_txt):
                    with open(caminho_txt, 'r', encoding='utf-8') as f_txt:
                        self.main_ctx.texto_resultado = f_txt.read()
                else:
                    self.main_ctx.texto_resultado = ""
            except Exception as e:
                print(f"Erro ao carregar dados do diretório selecionado: {e}")
        self.atualizar_botoes()

    def obter_pastas_selecionadas(self):
        folders = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                folders.append(self.table.item(r, 1).text())
        return folders

    def verificar_se_ja_enviado(self, local_ctx):
        if not local_ctx.caminho_base or not os.path.exists(local_ctx.caminho_base):
            return False
            
        pasta_relatorios = os.path.join(local_ctx.caminho_base, 'Relatorios')
        arquivo_info = os.path.join(pasta_relatorios, 'INFO.txt')
        if not os.path.exists(arquivo_info):
            return False
            
        url_storage = None
        try:
            with open(arquivo_info, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if linha.startswith("URL Storage:"):
                        url_storage = linha.split(":", 1)[1].strip()
                        break
        except Exception:
            return False
            
        if not url_storage or "/laudos/" not in url_storage:
            return False
            
        caminho_relativo = url_storage.split("/laudos/", 1)[1]
        partes = caminho_relativo.split('/')
        
        storage_base = self.config.get('destino_storage', r'\\periciadigital.ssp.to.gov.br\Web\laudos')
        destino_arquivo = os.path.join(storage_base, *partes)
        
        try:
            return os.path.exists(destino_arquivo)
        except Exception:
            return False

    def atualizar_botoes(self):
        folders = self.obter_pastas_selecionadas()
        qtd = len(folders)
        
        # Oculta/Mostra botões com base no número de pastas selecionadas
        self.btn_recriar.setVisible(qtd > 0)
        self.btn_processar.setVisible(qtd > 1)
        self.btn_reprocessar.setVisible(qtd > 0)
        self.btn_abrir.setVisible(qtd == 1)
        self.btn_enviar.setVisible(qtd > 0)
        self.btn_limpar.setVisible(qtd > 0)
        self.btn_backup.setVisible(qtd > 0)
        self.chk_auto.setVisible(qtd > 0)

        if qtd == 1:
            nome_pasta = folders[0]
            local_ctx = self.obter_contexto_pasta(nome_pasta)
            
            # Decide se exibe "Processar" ou "Reprocessar"
            processado = False
            if local_ctx:
                processado = utils.tentar_restaurar_processamento(local_ctx)
                
            self.btn_processar.setVisible(not processado)
            self.btn_reprocessar.setVisible(processado)
            
            if processado and local_ctx:
                if self.verificar_se_ja_enviado(local_ctx):
                    self.btn_enviar.setText("Reenviar p/ Storage")
                else:
                    self.btn_enviar.setText("2. Enviar p/ Storage")
            else:
                self.btn_enviar.setText("2. Enviar p/ Storage")
        elif qtd > 1:
            self.btn_enviar.setText("2. Enviar p/ Storage")

    def bloquear_controles(self, bloquear):
        state = not bloquear
        self.btn_recriar.setEnabled(state)
        self.btn_processar.setEnabled(state)
        self.btn_reprocessar.setEnabled(state)
        self.btn_abrir.setEnabled(state)
        self.btn_enviar.setEnabled(state)
        self.btn_limpar.setEnabled(state)
        self.btn_backup.setEnabled(state)
        self.chk_auto.setEnabled(state)
        self.table.setEnabled(state)
        self.btn_selecionar_todos.setEnabled(state)
        self.btn_desmarcar_todos.setEnabled(state)

    def iniciar_execucao_lote(self, task_type, selected_folders):
        pasta_raiz = self.config.get('pasta_raiz')
        destino_storage = self.config.get('destino_storage')
        destino_backup = self.config.get('destino_backup')
        
        self.bloquear_controles(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.btn_cancelar.setVisible(True)

        self.txt_console.clear()

        self.base_status_text = "Iniciando execução em lote..."
        self.lbl_status.setText(self.base_status_text)
        self.loading_timer.start(300)

        self.batch_worker = BatchWorker(
            task_type, 
            selected_folders, 
            pasta_raiz, 
            destino_storage, 
            destino_backup, 
            self.chk_auto.isChecked(), 
            self
        )
        self.batch_worker.progress_signal.connect(self.atualizar_progresso_lote)
        self.batch_worker.log_signal.connect(self.log_lote)
        self.batch_worker.finished_signal.connect(self.finalizar_execucao_lote)
        self.batch_worker.start()

    def atualizar_progresso_lote(self, pct, desc):
        self.progress_bar.setValue(pct)
        self.base_status_text = desc
        self.lbl_status.setText(desc)
        if desc.strip().endswith("..."):
            if not self.loading_timer.isActive():
                self.loading_timer.start(300)
        else:
            self.loading_timer.stop()

    def finalizar_execucao_lote(self, sucessos, erros):
        self.loading_timer.stop()
        self.progress_bar.setVisible(False)
        self.btn_cancelar.setVisible(False)
        self.bloquear_controles(False)
        
        self.lbl_status.setText(f"Execução concluída. Sucessos: {sucessos}, Erros: {erros}.")
        
        if self.batch_worker and self.batch_worker.task_type == 'backup':
            QMessageBox.information(
                self, 
                "Backup Concluído", 
                f"O processo de backup foi finalizado com sucesso!\n\nSucessos: {sucessos}\nErros: {erros}"
            )

        self.atualizar_tamanhos_tabela()

    def cancelar_lote(self):
        reply = QMessageBox.question(
            self, 
            "Confirmar Cancelamento", 
            "Deseja realmente cancelar a execução em lote?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.batch_worker:
                self.loading_timer.stop()
                self.batch_worker.cancel_event.set()
                self.lbl_status.setText("Execução cancelada pelo usuário.")
                self.progress_bar.setVisible(False)
                self.btn_cancelar.setVisible(False)
                self.bloquear_controles(False)

    def perguntar_sobrescrever_storage_lote(self, caminho):
        self.sig_perguntar_sobrescrever_storage.emit(caminho)
        self.sobrescrever_storage_event.wait()
        return self.sobrescrever_storage_result

    def _on_perguntar_storage(self, caminho):
        reply = QMessageBox.question(
            self, 
            "Confirmar Sobrescrita", 
            f"O arquivo já existe no destino:\n{caminho}\n\nDeseja sobrescrevê-lo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        self.sobrescrever_storage_result = (reply == QMessageBox.StandardButton.Yes)
        self.sobrescrever_storage_event.set()

    def perguntar_sobrescrever_backup_lote(self, nome_pasta):
        self.sig_perguntar_sobrescrever_backup.emit(nome_pasta)
        self.sobrescrever_backup_event.wait()
        return self.sobrescrever_backup_result

    def _on_perguntar_backup(self, nome_pasta):
        reply = QMessageBox.question(
            self, 
            "Sobrescrever Backup", 
            f"O arquivo de backup '{nome_pasta}.zip' já existe na pasta de destino.\nDeseja sobrescrevê-lo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        self.sobrescrever_backup_result = (reply == QMessageBox.StandardButton.Yes)
        self.sobrescrever_backup_event.set()

    # --- AÇÕES EM LOTE ---

    def limpar_extracao_lote(self):
        folders = self.obter_pastas_selecionadas()
        if not folders:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Limpeza",
            f"Deseja realmente limpar a pasta 'Extração' de todos os {len(folders)} processos selecionados?\nEsta ação apagará permanentemente todos os arquivos contidos nessa pasta.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.iniciar_execucao_lote('clear', folders)

    def backup_limpar_lote(self):
        folders = self.obter_pastas_selecionadas()
        if not folders:
            return
            
        destino_backup = self.config.get('destino_backup')
        if not destino_backup or not os.path.isdir(destino_backup):
            QMessageBox.critical(self, "Erro", "Destino de backup não configurado ou inválido nas configurações.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Backup & Limpeza",
            f"Deseja realmente compactar e fazer backup de todos os {len(folders)} processos selecionados?\nApós a conclusão, as pastas locais originais e os arquivos compactados locais serão APAGADOS permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.iniciar_execucao_lote('backup', folders)

    def recriar_diretorios_lote(self):
        folders = self.obter_pastas_selecionadas()
        if not folders:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Recriação em Lote",
            f"Deseja realmente RECRIAR os diretórios dos {len(folders)} processos selecionados?\nTodos os arquivos existentes nestas pastas serão apagados permanentemente!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.iniciar_execucao_lote('recreate', folders)

    def processar_anexos_lote(self):
        folders = self.obter_pastas_selecionadas()
        if not folders:
            return
        self.iniciar_execucao_lote('process', folders)

    def enviar_storage_lote(self):
        folders = self.obter_pastas_selecionadas()
        if not folders:
            return
        self.iniciar_execucao_lote('upload', folders)

    def abrir_pasta(self):
        folders = self.obter_pastas_selecionadas()
        if len(folders) == 1:
            pasta_raiz = self.config.get('pasta_raiz')
            caminho_base = os.path.join(pasta_raiz, folders[0])
            if os.path.exists(caminho_base):
                os.startfile(caminho_base)


# ---------------------------------------------------------------------------
# Main Application Window (Janela Principal GAD)
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    sig_perguntar_sobrescrever = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GAD (Gerenciador de Anexo Digital)")
        self.resize(950, 700)
        
        self.ctx = utils.ProtocoloContext()
        self.ctx.cancel_event = threading.Event()
        self.config = utils.carregar_config()

        self.query_worker = None
        self.process_worker = None
        self.upload_worker = None
        
        # Thread communication for overwrite prompt
        self.sobrescrever_result = False
        self.sobrescrever_event = threading.Event()
        self.sig_perguntar_sobrescrever.connect(self._on_perguntar_sobrescrever)

        # Timer para animações de loading nos logs
        self.loading_timer = QTimer(self)
        self.loading_timer.setInterval(400)
        self.loading_timer.timeout.connect(self.atualizar_animacao_loading)
        self.ultimo_texto_carregando = ""
        self.ultimo_estilo_carregando = "info"
        self.loading_state = 0

        self.init_ui()

    def init_ui(self):
        # Menu Bar
        menu_bar = self.menuBar()
        menu_config = menu_bar.addMenu("Sistema")
        
        action_config = QAction("Sistema...", self)
        action_config.triggered.connect(self.abrir_configuracoes)
        
        action_lista = QAction("Processos locais...", self)
        action_lista.triggered.connect(self.listar_diretorios)
        
        menu_config.addAction(action_config)
        menu_config.addSeparator()
        menu_config.addAction(action_lista)

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Header Title
        self.lbl_titulo = QLabel("SISTEMA GAD")
        self.lbl_titulo.setObjectName("lbl_titulo")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_titulo)
        # Logo Image
        self.lbl_logo = QLabel()
        logo_path = obter_caminho_recurso(os.path.join("assets", "logo.png"))
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Optionally scale the pixmap to a reasonable size
            pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_logo.setPixmap(pixmap)
            self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_logo)

        # Top area (Query Protocol)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        self.lbl_protocolo = QLabel("Número do Protocolo:")
        self.entry_protocolo = QLineEdit()
        self.entry_protocolo.setPlaceholderText("Digite o protocolo...")
        self.entry_protocolo.returnPressed.connect(self.realizar_consulta)
        
        self.btn_consultar = QPushButton("Consultar Protocolo")
        self.btn_consultar.setObjectName("btn_consultar") # cyan accent
        self.btn_consultar.clicked.connect(self.realizar_consulta)

        self.chk_exibir_tabela = QCheckBox("Exibir Tabela de Dados")
        self.chk_exibir_tabela.setChecked(False)
        self.chk_exibir_tabela.stateChanged.connect(self.toggle_tabela)

        top_layout.addWidget(self.lbl_protocolo)
        top_layout.addWidget(self.entry_protocolo, 1)
        top_layout.addWidget(self.btn_consultar)
        top_layout.addWidget(self.chk_exibir_tabela)
        
        layout.addLayout(top_layout)

        # Action Buttons Layout (Horizontal)
        self.frame_botoes = QHBoxLayout()
        self.frame_botoes.setSpacing(8)

        self.btn_criar_dir = QPushButton("Criar Diretórios GAD")
        self.btn_criar_dir.setObjectName("btn_criar")
        self.btn_criar_dir.clicked.connect(self.criar_diretorios)
        self.btn_criar_dir.setVisible(False)

        self.btn_recriar_dir = QPushButton("Recriar Diretórios")
        self.btn_recriar_dir.setObjectName("btn_recriar")
        self.btn_recriar_dir.clicked.connect(self.recriar_diretorios)
        self.btn_recriar_dir.setVisible(False)

        self.btn_processar = QPushButton("1. Processar Anexos (RAR/Hash)")
        self.btn_processar.setObjectName("btn_processar")
        self.btn_processar.clicked.connect(self.processar_anexos_gui)
        self.btn_processar.setVisible(False)

        self.btn_reprocessar = QPushButton("Reprocessar")
        self.btn_reprocessar.clicked.connect(self.processar_anexos_gui)
        self.btn_reprocessar.setVisible(False)

        self.btn_abrir_dir = QPushButton("Abrir Pasta")
        self.btn_abrir_dir.clicked.connect(self.abrir_pasta_atual)
        self.btn_abrir_dir.setVisible(False)

        self.btn_enviar = QPushButton("2. Enviar p/ Storage")
        self.btn_enviar.setObjectName("btn_enviar")
        self.btn_enviar.clicked.connect(self.enviar_storage_gui)
        self.btn_enviar.setVisible(False)

        self.btn_cancelar_envio = QPushButton("Cancelar Envio")
        self.btn_cancelar_envio.setObjectName("btn_cancelar")
        self.btn_cancelar_envio.clicked.connect(self.cancelar_envio_gui)
        self.btn_cancelar_envio.setVisible(False)

        self.chk_auto = QCheckBox("Enviar automaticamente ao Storage")
        self.chk_auto.setChecked(True)
        self.chk_auto.stateChanged.connect(self.sync_auto)
        self.chk_auto.setVisible(False)

        self.frame_botoes.addWidget(self.chk_auto)
        self.frame_botoes.addWidget(self.btn_criar_dir)
        self.frame_botoes.addWidget(self.btn_recriar_dir)
        self.frame_botoes.addWidget(self.btn_processar)
        self.frame_botoes.addWidget(self.btn_reprocessar)
        self.frame_botoes.addWidget(self.btn_abrir_dir)
        self.frame_botoes.addWidget(self.btn_enviar)
        self.frame_botoes.addWidget(self.btn_cancelar_envio)
        self.frame_botoes.addStretch()

        layout.addLayout(self.frame_botoes)

        # Layout para Opções de Hashes Existentes
        self.layout_hash_existente = QHBoxLayout()
        self.layout_hash_existente.setSpacing(8)
        
        self.chk_hash_existente = QCheckBox("Usar arquivo de hashes pré-existente (não recalcular)")
        self.chk_hash_existente.setChecked(False)
        self.chk_hash_existente.setVisible(False)
        self.chk_hash_existente.stateChanged.connect(self.toggle_hash_existente_widgets)
        
        self.lbl_caminho_hash = QLabel("Arquivo:")
        self.lbl_caminho_hash.setVisible(False)
        
        self.entry_caminho_hash = QLineEdit()
        self.entry_caminho_hash.setReadOnly(True)
        self.entry_caminho_hash.setPlaceholderText("Selecione o arquivo de hashes existente...")
        self.entry_caminho_hash.setVisible(False)
        
        self.btn_selecionar_hash = QPushButton("Selecionar")
        self.btn_selecionar_hash.setVisible(False)
        self.btn_selecionar_hash.clicked.connect(self.selecionar_arquivo_hash)
        
        self.layout_hash_existente.addWidget(self.chk_hash_existente)
        self.layout_hash_existente.addWidget(self.lbl_caminho_hash)
        self.layout_hash_existente.addWidget(self.entry_caminho_hash, 1)
        self.layout_hash_existente.addWidget(self.btn_selecionar_hash)
        self.layout_hash_existente.addStretch()
        
        layout.addLayout(self.layout_hash_existente)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Text Console Output
        self.txt_resultado = QTextEdit()
        self.txt_resultado.setReadOnly(True)
        self.txt_resultado.setPlaceholderText("Resultados e logs de processamento serão exibidos aqui...")
        layout.addWidget(self.txt_resultado)

        # Table Viewer
        self.table_dados = QTableWidget()
        self.table_dados.setVisible(False)
        layout.addWidget(self.table_dados)

        self.sync_auto()

    def sync_auto(self):
        self.ctx.auto_enviar = self.chk_auto.isChecked()

    def toggle_tabela(self, state):
        self.table_dados.setVisible(self.chk_exibir_tabela.isChecked())

    def toggle_hash_existente_widgets(self, state):
        visible = self.chk_hash_existente.isChecked() and self.chk_hash_existente.isVisible()
        self.lbl_caminho_hash.setVisible(visible)
        self.entry_caminho_hash.setVisible(visible)
        self.btn_selecionar_hash.setVisible(visible)

    def selecionar_arquivo_hash(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Hashes", "", "Arquivos de Texto (*.txt);;Todos os Arquivos (*.*)")
        if file_path:
            self.entry_caminho_hash.setText(file_path)

    def log(self, text, style="info"):
        if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
            self.finalizar_animacao_loading()

        limpo_text = text.strip()
        if limpo_text.endswith("..."):
            self.ultimo_texto_carregando = text.strip()
            self.ultimo_estilo_carregando = style
            self.loading_state = 0
            
            # Se o texto original tem uma quebra de linha inicial, preservamos escrevendo ela antes
            if text.startswith("\n"):
                self.escrever_linha_log("", style) # apenas insere newline
                
            self.escrever_linha_log(self.ultimo_texto_carregando, style)
            self.loading_timer.start(300)
        else:
            self.escrever_linha_log(text, style)

    def escrever_linha_log(self, text, style="info"):
        cursor = self.txt_resultado.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        color = "#e1e1e6" # default
        font_weight = "normal"
        if style == "success":
            color = "#04D361"
            font_weight = "bold"
        elif style == "error":
            color = "#E23E3E"
            font_weight = "bold"
        elif style == "warning":
            color = "#FF8C00"
            font_weight = "bold"
            
        html = f'<span style="color: {color}; font-weight: {font_weight};">{text}</span>'
        cursor.insertHtml(html)
        cursor.insertText("\n")
        self.txt_resultado.setTextCursor(cursor)
        self.txt_resultado.ensureCursorVisible()

    def substituir_ultima_linha_log(self, text, style="info"):
        cursor = self.txt_resultado.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if cursor.atBlockStart() and cursor.position() > 0:
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        
        color = "#e1e1e6" # default
        font_weight = "normal"
        if style == "success":
            color = "#04D361"
            font_weight = "bold"
        elif style == "error":
            color = "#E23E3E"
            font_weight = "bold"
        elif style == "warning":
            color = "#FF8C00"
            font_weight = "bold"
            
        html = f'<span style="color: {color}; font-weight: {font_weight};">{text}</span>'
        cursor.insertHtml(html)
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.txt_resultado.setTextCursor(cursor)
        self.txt_resultado.ensureCursorVisible()

    def atualizar_animacao_loading(self):
        if not self.ultimo_texto_carregando:
            return
        frames = [" [|]", " [/]", " [-]", " [\\]"]
        frame = frames[self.loading_state % len(frames)]
        self.loading_state += 1
        self.substituir_ultima_linha_log(f"{self.ultimo_texto_carregando}{frame}", self.ultimo_estilo_carregando)

    def finalizar_animacao_loading(self):
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
        if self.ultimo_texto_carregando:
            self.substituir_ultima_linha_log(self.ultimo_texto_carregando, self.ultimo_estilo_carregando)
            self.ultimo_texto_carregando = ""

    # --- CONSULTA ---

    def realizar_consulta(self):
        protocolo = self.entry_protocolo.text().strip()
        if not protocolo:
            QMessageBox.warning(self, "Aviso", "Por favor, informe o número do protocolo.")
            return

        self.btn_consultar.setEnabled(False)
        self.entry_protocolo.setEnabled(False)
        
        # Oculta botões antigos
        self.btn_criar_dir.setVisible(False)
        self.btn_recriar_dir.setVisible(False)
        self.btn_processar.setVisible(False)
        self.btn_reprocessar.setVisible(False)
        self.btn_abrir_dir.setVisible(False)
        self.btn_enviar.setVisible(False)
        self.btn_cancelar_envio.setVisible(False)
        self.chk_auto.setVisible(False)

        self.txt_resultado.clear()
        self.log("Consultando o protocolo...", "info")

        self.query_worker = QueryWorker(protocolo)
        self.query_worker.finished_signal.connect(self.consulta_concluida)
        self.query_worker.start()

    def consulta_concluida(self, sucesso, resultado, dados_brutos, chaves, tabela):
        self.finalizar_animacao_loading()
        self.btn_consultar.setEnabled(True)
        self.entry_protocolo.setEnabled(True)
        self.txt_resultado.clear()

        # Extrai apenas as mensagens de status (tudo antes da tabela ASCII)
        if '+' in resultado:
            status_text = resultado.split('+')[0].strip() + '\n'
        else:
            status_text = resultado

        # Aplica realce na mensagem
        if "✅ DADOS RECUPERADOS COM SUCESSO! ✅" in status_text:
            partes = status_text.split("✅ DADOS RECUPERADOS COM SUCESSO! ✅")
            self.log(partes[0], "info")
            self.log("✅ DADOS RECUPERADOS COM SUCESSO! ✅", "success")
            if len(partes) > 1:
                self.log(partes[1], "info")
        elif "⚠️ PROTOCOLO NÃO ENCONTRADO ⚠️" in status_text:
            partes = status_text.split("⚠️ PROTOCOLO NÃO ENCONTRADO ⚠️")
            self.log(partes[0], "info")
            self.log("⚠️ PROTOCOLO NÃO ENCONTRADO ⚠️", "error")
            if len(partes) > 1:
                self.log(partes[1], "info")
        else:
            self.log(status_text, "info")

        # Configura tabela
        self.table_dados.setRowCount(0)
        self.table_dados.setColumnCount(len(chaves))
        self.table_dados.setHorizontalHeaderLabels(chaves)
        
        for col_idx, col in enumerate(chaves):
            self.table_dados.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeMode.ResizeToContents)
            
        for row_idx, row_data in enumerate(tabela):
            self.table_dados.insertRow(row_idx)
            for col_idx, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table_dados.setItem(row_idx, col_idx, item)

        if sucesso:
            self.ctx.dados = dados_brutos
            self.ctx.protocolo = self.entry_protocolo.text().strip()
            self.ctx.texto_resultado = resultado
            self.ctx.caminho_base = utils.obter_caminho_base(self.ctx.protocolo, dados_brutos, self.config.get('pasta_raiz'))
            self.chk_auto.setVisible(True)
            self.atualizar_botoes_gui()
            
            if self.ctx.caminho_base and os.path.exists(self.ctx.caminho_base):
                aviso_msg = f"\nℹ️ AVISO: O diretório para este protocolo já existe em:\n{self.ctx.caminho_base}\n"
                self.log(aviso_msg, "warning")
        else:
            self.ctx.reset()
            self.atualizar_botoes_gui()

    # --- PROCESSAMENTO ---

    def processar_anexos_gui(self):
        if not self.ctx.dados or not self.ctx.protocolo:
            return
            
        caminho_base = utils.obter_caminho_base(self.ctx.protocolo, self.ctx.dados, self.config.get('pasta_raiz'))
        if not caminho_base or not os.path.exists(caminho_base):
            QMessageBox.critical(self, "Erro", "O diretório do protocolo ainda não foi criado.")
            return
            
        laudo_criado = False
        num_laudo = None
        ano_laudo = None
        
        if isinstance(self.ctx.dados, dict):
            laudo = self.ctx.dados.get('laudo')
            if isinstance(laudo, dict):
                numero_completo = laudo.get('numeroCompleto')
                if numero_completo:
                    laudo_criado = True
                    partes = str(numero_completo).split('.')
                    if len(partes) == 2:
                        try:
                            ano_laudo = int(partes[0])
                        except ValueError:
                            pass
                        num_laudo = partes[1]
                    else:
                        num_laudo = str(numero_completo)
                        
        if not laudo_criado or not num_laudo:
            QMessageBox.warning(
                self, 
                "Aviso", 
                "Não foi encontrado nenhum laudo criado para este protocolo no Galileu.\nPor favor, primeiro crie um número de laudo no Galileu."
            )
            return
            
        # Verifica se deve usar hash existente e valida o arquivo
        if self.chk_hash_existente.isChecked():
            caminho_hash = self.entry_caminho_hash.text().strip()
            if not caminho_hash or not os.path.exists(caminho_hash):
                QMessageBox.warning(self, "Aviso", "Por favor, selecione um arquivo de hashes pré-existente válido.")
                return
            self.ctx.caminho_hash_existente = caminho_hash
        else:
            self.ctx.caminho_hash_existente = ""

        self.ctx.numero_laudo = num_laudo
        self.ctx.ano = ano_laudo if ano_laudo else (self.ctx.dados.get('ano', datetime.now().year) if isinstance(self.ctx.dados, dict) else datetime.now().year)

        # Salva dados atualizados
        caminho_json = os.path.join(caminho_base, 'Laudo', 'dados_protocolo.json')
        try:
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(self.ctx.dados, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados_protocolo.json: {e}")

        # Bloqueia botões
        self.definir_estado_controles(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.txt_resultado.clear()

        if self.chk_auto.isChecked():
            self.btn_cancelar_envio.setVisible(True)

        self.process_worker = ProcessWorker(self.ctx, self.chk_auto.isChecked(), self)
        self.process_worker.progress_signal.connect(self.progresso_processo)
        self.process_worker.log_signal.connect(self.log)
        self.process_worker.finished_signal.connect(self.processo_concluido)
        self.process_worker.start()

    def progresso_processo(self, pct, desc):
        self.progress_bar.setValue(pct)

    def processo_concluido(self, sucesso, message):
        self.finalizar_animacao_loading()
        self.progress_bar.setVisible(False)
        self.btn_cancelar_envio.setVisible(False)
        self.definir_estado_controles(True)
        self.atualizar_botoes_gui()

    # --- UPLOAD ---

    def enviar_storage_gui(self):
        self.definir_estado_controles(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.btn_cancelar_envio.setVisible(True)
        self.log("\n-> [Envio] Copiando arquivo para a rede...", "info")

        self.upload_worker = UploadWorker(self.ctx, self)
        self.upload_worker.log_signal.connect(self.log)
        self.upload_worker.finished_signal.connect(self.upload_concluido)
        self.upload_worker.start()

    def upload_concluido(self, sucesso, destino_ou_erro):
        self.finalizar_animacao_loading()
        self.progress_bar.setVisible(False)
        self.btn_cancelar_envio.setVisible(False)
        self.definir_estado_controles(True)
        self.atualizar_botoes_gui()

        if sucesso:
            self.log(f"\n[SUCESSO] Arquivo enviado com sucesso!\nSalvo em rede: {destino_ou_erro}\n", "success")
            QMessageBox.information(self, "Upload Concluído", f"Arquivo enviado com sucesso para a rede:\n{destino_ou_erro}")
        else:
            if destino_ou_erro == "Cancelado":
                self.log("\n[AVISO] Envio cancelado pelo usuário.\n", "warning")
            else:
                self.log(f"\n[ERRO] Falha ao enviar para o Storage:\n{destino_ou_erro}\n", "error")
                QMessageBox.critical(self, "Erro de Rede", f"Falha ao enviar para o Storage:\n{destino_ou_erro}")

    def cancelar_envio_gui(self):
        reply = QMessageBox.question(
            self, 
            "Confirmar Cancelamento", 
            "Deseja realmente cancelar o envio para o Storage?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.finalizar_animacao_loading()
            self.ctx.cancel_event.set()
            self.definir_estado_controles(True)
            self.btn_cancelar_envio.setVisible(False)
            self.progress_bar.setVisible(False)

    # --- SOBRESCRITA CALLBACK (THREAD-SAFE) ---

    def perguntar_sobrescrever(self, caminho):
        self.sobrescrever_event.clear()
        self.sig_perguntar_sobrescrever.emit(caminho)
        self.sobrescrever_event.wait()
        return self.sobrescrever_result

    def _on_perguntar_sobrescrever(self, caminho):
        reply = QMessageBox.question(
            self, 
            "Confirmar Sobrescrita", 
            f"O arquivo já existe no destino:\n{caminho}\n\nDeseja sobrescrevê-lo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        self.sobrescrever_result = (reply == QMessageBox.StandardButton.Yes)
        self.sobrescrever_event.set()

    # --- OUTROS CONTROLES ---

    def criar_diretorios(self):
        if not self.ctx.dados or not self.ctx.protocolo:
            QMessageBox.critical(self, "Erro", "Não há dados de protocolo para criar os diretórios.")
            return
            
        pasta_raiz = self.config.get('pasta_raiz')
        if not pasta_raiz or not os.path.isdir(pasta_raiz):
            QMessageBox.warning(self, "Aviso", "Pasta raiz não configurada ou inválida.\nPor favor, selecione-a agora.")
            self.abrir_configuracoes()
            pasta_raiz = self.config.get('pasta_raiz')
            if not pasta_raiz or not os.path.isdir(pasta_raiz):
                return

        caminho_base = utils.obter_caminho_base(self.ctx.protocolo, self.ctx.dados, pasta_raiz)
        if not caminho_base:
            return
        
        if os.path.exists(caminho_base):
            QMessageBox.information(self, "Aviso", "O diretório para este protocolo já existe.")
            self.btn_criar_dir.setVisible(False)
            return
            
        pastas_para_criar = ['Extração', 'Fotos', 'Laudo', 'Relatorios', 'Relatorios/Anexo Digital']
        try:
            os.makedirs(caminho_base, exist_ok=True)
            for pasta in pastas_para_criar:
                os.makedirs(os.path.join(caminho_base, pasta), exist_ok=True)
            
            caminho_json = os.path.join(caminho_base, 'Laudo', 'dados_protocolo.json')
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(self.ctx.dados, f, indent=4, ensure_ascii=False)
            
            if self.ctx.texto_resultado:
                caminho_txt = os.path.join(caminho_base, 'Laudo', 'Resumo_Laudo.txt')
                utils.salvar_resumo_txt(caminho_txt, self.ctx.protocolo, self.ctx.texto_resultado)
            
            QMessageBox.information(self, "Sucesso", f"Diretórios criados com sucesso em:\n{caminho_base}")
            self.ctx.caminho_zip = ""
            self.ctx.senha = ""
            self.ctx.hash_diretorio = ""
            self.atualizar_botoes_gui()
            os.startfile(caminho_base)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar diretórios: {e}")

    def recriar_diretorios(self):
        if not self.ctx.dados or not self.ctx.protocolo:
            QMessageBox.critical(self, "Erro", "Não há dados de protocolo para recriar os diretórios.")
            return
            
        pasta_raiz = self.config.get('pasta_raiz')
        if not pasta_raiz or not os.path.isdir(pasta_raiz):
            QMessageBox.warning(self, "Aviso", "Pasta raiz não configurada ou inválida.\nPor favor, selecione-a agora.")
            self.abrir_configuracoes()
            pasta_raiz = self.config.get('pasta_raiz')
            if not pasta_raiz or not os.path.isdir(pasta_raiz):
                return

        caminho_base = utils.obter_caminho_base(self.ctx.protocolo, self.ctx.dados, pasta_raiz)
        if not caminho_base:
            return
            
        if os.path.exists(caminho_base):
            reply = QMessageBox.question(
                self,
                "Confirmar Recriação", 
                f"O diretório já existe em:\n{caminho_base}\n\nTem certeza de que deseja RECRIAR? Todos os arquivos existentes nesta pasta serão apagados permanentemente!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            
            try:
                shutil.rmtree(caminho_base)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao apagar o diretório existente: {e}")
                return
                
        pastas_para_criar = ['Extração', 'Fotos', 'Laudo', 'Relatorios', 'Relatorios/Anexo Digital']
        try:
            os.makedirs(caminho_base, exist_ok=True)
            for pasta in pastas_para_criar:
                os.makedirs(os.path.join(caminho_base, pasta), exist_ok=True)
            
            caminho_json = os.path.join(caminho_base, 'Laudo', 'dados_protocolo.json')
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(self.ctx.dados, f, indent=4, ensure_ascii=False)
            
            if self.ctx.texto_resultado:
                caminho_txt = os.path.join(caminho_base, 'Laudo', 'Resumo_Laudo.txt')
                utils.salvar_resumo_txt(caminho_txt, self.ctx.protocolo, self.ctx.texto_resultado)
            
            QMessageBox.information(self, "Sucesso", f"Diretórios recriados com sucesso em:\n{caminho_base}")
            self.ctx.caminho_zip = ""
            self.ctx.senha = ""
            self.ctx.hash_diretorio = ""
            self.atualizar_botoes_gui()
            os.startfile(caminho_base)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao recriar diretórios: {e}")

    def abrir_pasta_atual(self):
        if self.ctx.caminho_base and os.path.exists(self.ctx.caminho_base):
            os.startfile(self.ctx.caminho_base)

    def verificar_se_ja_enviado(self, local_ctx):
        if not local_ctx.caminho_base or not os.path.exists(local_ctx.caminho_base):
            return False
            
        pasta_relatorios = os.path.join(local_ctx.caminho_base, 'Relatorios')
        arquivo_info = os.path.join(pasta_relatorios, 'INFO.txt')
        if not os.path.exists(arquivo_info):
            return False
            
        url_storage = None
        try:
            with open(arquivo_info, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if linha.startswith("URL Storage:"):
                        url_storage = linha.split(":", 1)[1].strip()
                        break
        except Exception:
            return False
            
        if not url_storage or "/laudos/" not in url_storage:
            return False
            
        caminho_relativo = url_storage.split("/laudos/", 1)[1]
        partes = caminho_relativo.split('/')
        
        storage_base = self.config.get('destino_storage', r'\\periciadigital.ssp.to.gov.br\Web\laudos')
        destino_arquivo = os.path.join(storage_base, *partes)
        
        try:
            return os.path.exists(destino_arquivo)
        except Exception:
            return False

    def atualizar_botoes_gui(self):
        # Esconde todos primeiro
        self.btn_criar_dir.setVisible(False)
        self.btn_recriar_dir.setVisible(False)
        self.btn_processar.setVisible(False)
        self.btn_reprocessar.setVisible(False)
        self.btn_abrir_dir.setVisible(False)
        self.btn_enviar.setVisible(False)
        self.chk_auto.setVisible(False)
        self.chk_hash_existente.setVisible(False)
        self.toggle_hash_existente_widgets(0)

        if self.ctx.caminho_base:
            self.chk_auto.setVisible(True)
            if os.path.exists(self.ctx.caminho_base):
                self.btn_recriar_dir.setVisible(True)
                self.btn_abrir_dir.setVisible(True)
                if utils.tentar_restaurar_processamento(self.ctx):
                    self.btn_reprocessar.setVisible(True)
                    self.chk_hash_existente.setVisible(True)
                    self.toggle_hash_existente_widgets(0)
                    self.btn_enviar.setVisible(True)
                    self.btn_enviar.setEnabled(True)
                    if self.verificar_se_ja_enviado(self.ctx):
                        self.btn_enviar.setText("Reenviar p/ Storage")
                    else:
                        self.btn_enviar.setText("2. Enviar p/ Storage")
                else:
                    self.btn_processar.setVisible(True)
                    self.chk_hash_existente.setVisible(True)
                    self.toggle_hash_existente_widgets(0)
            else:
                self.btn_criar_dir.setVisible(True)
                self.btn_criar_dir.setEnabled(True)

    def definir_estado_controles(self, ativo):
        self.entry_protocolo.setEnabled(ativo)
        self.btn_consultar.setEnabled(ativo)
        self.btn_criar_dir.setEnabled(ativo)
        self.btn_recriar_dir.setEnabled(ativo)
        self.btn_processar.setEnabled(ativo)
        self.btn_reprocessar.setEnabled(ativo)
        self.btn_enviar.setEnabled(ativo)
        self.chk_auto.setEnabled(ativo)
        self.chk_hash_existente.setEnabled(ativo)
        self.btn_selecionar_hash.setEnabled(ativo)

    def abrir_configuracoes(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config = utils.carregar_config()

    def listar_diretorios(self):
        dlg = ProcessesDialog(self.ctx, self.config, self)
        dlg.exec()
        # Atualiza botões da janela principal quando fechar a lista
        self.atualizar_botoes_gui()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def iniciar_interface():
    # Hack para forçar o ícone correto na barra de tarefas do Windows
    if sys.platform == 'win32':
        import ctypes
        try:
            myappid = 'jonasmsjunior.gad.app.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    # Define o ícone global da aplicação
    icon_path = obter_caminho_recurso(os.path.join("assets", "gad.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Carrega tema salvo (Dark padrão)
    cfg = utils.carregar_config()
    tema = cfg.get('tema', 'Dark')
    if tema == 'Light':
        app.setStyleSheet(LIGHT_STYLING)
    else:
        app.setStyleSheet(STYLING)
    
    window = MainWindow()
    window.show()
    
    app.exec()
