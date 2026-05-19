import os
import shutil
import json
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinter.scrolledtext import ScrolledText
import threading
from datetime import datetime

import utils
import api
import anexos
import services

from tkinter import simpledialog

def iniciar_interface():
    # Instância central de estado
    ctx = utils.ProtocoloContext()
    ctx.cancel_event = threading.Event()
    config = utils.carregar_config()
    
    # Variáveis de UI que não são estado de protocolo
    lbl_progresso = None  # will be replaced by progress_bar later

    def realizar_consulta():
        # nonlocal removed – using ctx instead

        
        protocolo = entry_protocolo.get().strip()
        if not protocolo:
            messagebox.showwarning("Aviso", "Por favor, informe o número do protocolo.")
            return
            
        btn_consultar.config(state=tk.DISABLED)
        btn_criar_dir.pack_forget()
        chk_auto.pack_forget()
        btn_processar.pack_forget()
        btn_enviar.pack_forget()
        btn_cancelar_envio.pack_forget()
        txt_resultado.delete(1.0, tk.END)
        txt_resultado.insert(tk.END, "Consultando... aguarde.")
        
        def thread_consulta():
            # removed nonlocal – ctx used instead
            sucesso, resultado, dados_brutos, chaves, tabela = api.consultar_protocolo(protocolo)
            
            def atualizar_gui():
                # removed nonlocal – ctx used instead
                # Limpa logs
                txt_resultado.delete(1.0, tk.END)
                
                # Extrai apenas as mensagens de status (tudo antes da tabela ASCII)
                # Como tabulate usa '+---' e '|', podemos quebrar o texto na primeira ocorrência de '+'
                if '+' in resultado:
                    status_text = resultado.split('+')[0].strip() + '\n'
                else:
                    status_text = resultado
                    
                txt_resultado.insert(tk.END, status_text)
                btn_consultar.config(state=tk.NORMAL)
                
                # Aplica realce na mensagem de sucesso
                pos_sucesso = txt_resultado.search("✅ DADOS RECUPERADOS COM SUCESSO! ✅", "1.0", tk.END)
                if pos_sucesso:
                    txt_resultado.tag_add("sucesso", pos_sucesso, f"{pos_sucesso} lineend")
                    
                # Aplica realce na mensagem de erro
                pos_err = txt_resultado.search("⚠️ PROTOCOLO NÃO ENCONTRADO ⚠️", "1.0", tk.END)
                if pos_err:
                    txt_resultado.tag_add("erro", pos_err, f"{pos_err} lineend")
                
                # Limpa a Treeview
                tree_dados.delete(*tree_dados.get_children())
                tree_dados["columns"] = chaves
                
                # Configura os cabeçalhos e colunas da Treeview
                for col in chaves:
                    tree_dados.heading(col, text=col)
                    tree_dados.column(col, width=150, anchor=tk.W)
                    
                for linha in tabela:
                    tree_dados.insert("", tk.END, values=linha)
                
                if sucesso:
                    ctx.dados = dados_brutos
                    ctx.protocolo = protocolo
                    ctx.texto_resultado = resultado
                    ctx.caminho_base = utils.obter_caminho_base(protocolo, dados_brutos, config.get('pasta_raiz'))
                    chk_auto.pack(side=tk.LEFT, padx=5)
                    atualizar_botoes_gui()
                    if ctx.caminho_base and os.path.exists(ctx.caminho_base):
                        aviso_msg = f"ℹ️ AVISO: O diretório para este protocolo já existe em:\n{ctx.caminho_base}\n\n"
                        if pos_sucesso:
                            pos_insercao = f"{pos_sucesso} lineend + 2 chars"
                            txt_resultado.insert(pos_insercao, aviso_msg, "aviso")
                        else:
                            txt_resultado.insert(tk.END, "\n\n" + aviso_msg, "aviso")
                else:
                    ctx.dados = None
                    ctx.protocolo = None
                    ctx.texto_resultado = None
                    atualizar_botoes_gui()
                    btn_cancelar_envio.pack_forget()
                    
            txt_resultado.after(0, atualizar_gui)
            
        threading.Thread(target=thread_consulta, daemon=True).start()

    def abrir_configuracoes():
        janela_config = tk.Toplevel(janela)
        janela_config.title("Configurações do GAD")
        janela_config.geometry("500x320")
        janela_config.grab_set() 
        
        ttk.Label(janela_config, text="Pasta Raiz Local:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(15, 5))
        frame_raiz = ttk.Frame(janela_config)
        frame_raiz.pack(fill=tk.X, padx=20)
        
        entry_raiz = ttk.Entry(frame_raiz)
        entry_raiz.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry_raiz.insert(0, config.get('pasta_raiz', ''))
        
        def buscar_raiz():
            d = filedialog.askdirectory()
            if d:
                entry_raiz.delete(0, tk.END)
                entry_raiz.insert(0, d)
        
        ttk.Button(frame_raiz, text="Buscar", command=buscar_raiz).pack(side=tk.LEFT, padx=(5,0))
        
        ttk.Label(janela_config, text="Destino Storage (Rede):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 5))
        entry_storage = ttk.Entry(janela_config)
        entry_storage.pack(fill=tk.X, padx=20)
        entry_storage.insert(0, config.get('destino_storage', r'\\periciadigital.ssp.to.gov.br\Web\laudos'))

        ttk.Label(janela_config, text="Destino de Backup:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 5))
        frame_backup = ttk.Frame(janela_config)
        frame_backup.pack(fill=tk.X, padx=20)
        
        entry_backup = ttk.Entry(frame_backup)
        entry_backup.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry_backup.insert(0, config.get('destino_backup', ''))
        
        def buscar_backup():
            d = filedialog.askdirectory()
            if d:
                entry_backup.delete(0, tk.END)
                entry_backup.insert(0, d)
        
        ttk.Button(frame_backup, text="Buscar", command=buscar_backup).pack(side=tk.LEFT, padx=(5,0))
        
        def salvar_configs():
            config['pasta_raiz'] = entry_raiz.get().strip()
            config['destino_storage'] = entry_storage.get().strip()
            config['destino_backup'] = entry_backup.get().strip()
            utils.salvar_config(config)

            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            janela_config.destroy()
            
        ttk.Button(janela_config, text="Salvar Configurações", command=salvar_configs).pack(pady=20)
            
    def listar_diretorios():
        pasta_raiz = config.get('pasta_raiz')
        if not pasta_raiz or not os.path.isdir(pasta_raiz):
            messagebox.showwarning("Aviso", "Pasta raiz não configurada ou inválida.\nPor favor, configure-a primeiro.")
            return
            
        janela_lista = tk.Toplevel(janela)
        janela_lista.title("Processos Locais")
        janela_lista.geometry("750x480")
        
        frame_tree = tk.Frame(janela_lista)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        colunas = ("Pasta", "Tamanho")
        tree = ttk.Treeview(frame_tree, columns=colunas, show="headings", selectmode="extended")
        tree.heading("Pasta", text="Nome da Pasta")
        tree.heading("Tamanho", text="Tamanho Ocupado")
        tree.column("Pasta", width=500)
        tree.column("Tamanho", width=150, anchor=tk.E)
        
        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        janela.tree_list = tree

        cancel_event_list = threading.Event()

        def obter_contexto_pasta(nome_pasta):
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

        def ao_selecionar_pasta(event):
            selected_items = tree.selection()
            if not selected_items:
                return
            item = selected_items[0]
            valores = tree.item(item, "values")
            if not valores:
                return
            nome_pasta = valores[0]
            caminho_pasta = os.path.join(pasta_raiz, nome_pasta)
            
            protocolo = ""
            if ".Prot_" in nome_pasta:
                protocolo = nome_pasta.split(".Prot_")[1]
            
            caminho_json = os.path.join(caminho_pasta, 'Laudo', 'dados_protocolo.json')
            if os.path.exists(caminho_json):
                try:
                    with open(caminho_json, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    ctx.dados = dados
                    ctx.protocolo = protocolo
                    ctx.caminho_base = caminho_pasta
                    ctx.caminho_zip = ""
                    ctx.senha = ""
                    ctx.hash_diretorio = ""
                    ctx.ano = 0
                    ctx.numero_laudo = ""
                    utils.tentar_restaurar_processamento(ctx)
                    caminho_txt = os.path.join(caminho_pasta, 'Laudo', 'Resumo_Laudo.txt')
                    if os.path.exists(caminho_txt):
                        with open(caminho_txt, 'r', encoding='utf-8') as f_txt:
                            ctx.texto_resultado = f_txt.read()
                    else:
                        ctx.texto_resultado = ""
                except Exception as e:
                    print(f"Erro ao carregar dados do diretório selecionado: {e}")
            atualizar_botoes_gui()

        tree.bind("<<TreeviewSelect>>", ao_selecionar_pasta)

        frame_acoes = ttk.Frame(janela_lista)
        frame_acoes.pack(fill=tk.X, pady=5, padx=20)

        janela.btn_recriar_dir_list = ttk.Button(frame_acoes, text="ReCriar diretórios", style="Process.TButton", command=lambda: recriar_diretorios_lote())
        janela.btn_processar_list = ttk.Button(frame_acoes, text="1. Processar Anexos (ZIP/Hash)", style="Process.TButton", command=lambda: processar_anexos_lote())
        janela.btn_reprocessar_list = ttk.Button(frame_acoes, text="ReProcessar", style="Process.TButton", command=lambda: processar_anexos_lote())
        janela.btn_abrir_dir_list = ttk.Button(frame_acoes, text="Abrir Pasta", style="Action.TButton", command=lambda: os.startfile(ctx.caminho_base) if ctx.caminho_base else None)
        janela.btn_enviar_list = ttk.Button(frame_acoes, text="2. Enviar p/ Storage", style="Upload.TButton", command=lambda: enviar_storage_lote())
        janela.btn_limpar_extracao_list = ttk.Button(frame_acoes, text="Limpar Extração", style="Danger.TButton", command=lambda: limpar_extracao_lote())
        janela.btn_backup_list = ttk.Button(frame_acoes, text="Backup & Limpar", style="Upload.TButton", command=lambda: backup_limpar_lote())
        janela.chk_auto_list = ttk.Checkbutton(frame_acoes, text="Enviar automaticamente ao Storage", variable=auto_enviar)

        progress_bar_list = ttk.Progressbar(frame_acoes, mode='indeterminate')
        btn_cancelar_list = ttk.Button(frame_acoes, text="Cancelar", style="Danger.TButton", command=lambda: cancelar_list_gui())

        def ao_fechar_lista(event):
            if event.widget == janela_lista:
                for attr in ['btn_recriar_dir_list', 'btn_processar_list', 'btn_reprocessar_list', 'btn_abrir_dir_list', 'btn_enviar_list', 'chk_auto_list', 'tree_list', 'btn_limpar_extracao_list', 'btn_backup_list']:
                    if hasattr(janela, attr):
                        try:
                            delattr(janela, attr)
                        except Exception:
                            pass
        janela_lista.bind("<Destroy>", ao_fechar_lista)
        
        lbl_status = tk.Label(janela_lista, text="Calculando tamanhos... por favor aguarde.")
        lbl_status.pack(pady=5)

        def bloquear_controles_list(bloquear):
            state = tk.DISABLED if bloquear else tk.NORMAL
            janela.btn_recriar_dir_list.config(state=state)
            janela.btn_processar_list.config(state=state)
            janela.btn_reprocessar_list.config(state=state)
            janela.btn_enviar_list.config(state=state)
            janela.chk_auto_list.config(state=state)
            janela.btn_limpar_extracao_list.config(state=state)
            janela.btn_backup_list.config(state=state)
            tree.config(selectmode="none" if bloquear else "extended")

        def finalizar_lote():
            janela_lista.after(0, lambda: progress_bar_list.stop())
            janela_lista.after(0, lambda: progress_bar_list.pack_forget())
            janela_lista.after(0, lambda: btn_cancelar_list.pack_forget())
            janela_lista.after(0, lambda: bloquear_controles_list(False))

        def perguntar_sobrescrever_lote(caminho):
            import queue
            q = queue.Queue()
            def ask():
                res = messagebox.askyesno(
                    "Confirmar Sobrescrita", 
                    f"O arquivo já existe no destino:\n{caminho}\n\nDeseja sobrescrevê-lo?",
                    parent=janela_lista
                )
                q.put(res)
            janela_lista.after(0, ask)
            return q.get()

        def cancelar_list_gui():
            if messagebox.askyesno("Confirmar Cancelamento", "Deseja realmente cancelar a execução em lote?", parent=janela_lista):
                cancel_event_list.set()
                finalizar_lote()
                lbl_status.config(text="Execução em lote cancelada pelo usuário.")

        def limpar_extracao_lote():
            selected = tree.selection()
            if not selected:
                return
            confirmacao = messagebox.askyesno(
                "Confirmar Limpeza",
                f"Deseja realmente limpar a pasta 'Extração' de todos os {len(selected)} processos selecionados?\nEsta ação apagará permanentemente todos os arquivos contidos nessa pasta.",
                parent=janela_lista
            )
            if not confirmacao:
                return
                
            bloquear_controles_list(True)
            cancel_event_list.clear()
            progress_bar_list.pack(side=tk.LEFT, padx=5)
            progress_bar_list.start()
            btn_cancelar_list.pack(side=tk.LEFT, padx=5)

            def thread_run():
                sucessos = 0
                erros = 0
                for i, item in enumerate(selected):
                    if cancel_event_list.is_set():
                        break
                    valores = tree.item(item, "values")
                    nome_pasta = valores[0]
                    janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: lbl_status.config(text=f"Limpando Extração {idx} de {tot}: {name}..."))
                    
                    local_ctx = obter_contexto_pasta(nome_pasta)
                    if not local_ctx or not local_ctx.caminho_base:
                        erros += 1
                        continue
                        
                    caminho_extracao = os.path.join(local_ctx.caminho_base, 'Extração')
                    try:
                        if os.path.exists(caminho_extracao):
                            shutil.rmtree(caminho_extracao)
                        os.makedirs(caminho_extracao, exist_ok=True)
                        sucessos += 1
                    except Exception as e:
                        print(f"Erro ao limpar Extração em {nome_pasta}: {e}")
                        erros += 1
                        
                janela_lista.after(0, lambda: lbl_status.config(text=f"Limpeza concluída. Sucessos: {sucessos}, Erros: {erros}."))
                finalizar_lote()
                janela_lista.after(0, atualizar_tamanhos_tabela)
                
            threading.Thread(target=thread_run, daemon=True).start()

        def backup_limpar_lote():
            selected = tree.selection()
            if not selected:
                return
                
            destino_backup = config.get('destino_backup')
            if not destino_backup or not os.path.isdir(destino_backup):
                messagebox.showerror("Erro", "Destino de backup não configurado ou inválido nas configurações.", parent=janela_lista)
                return

            confirmacao = messagebox.askyesno(
                "Confirmar Backup & Limpeza",
                f"Deseja realmente compactar e fazer backup de todos os {len(selected)} processos selecionados?\nApós a conclusão bem-sucedida, as pastas locais originais e os arquivos ZIP locais serão APAGADOS permanentemente.",
                parent=janela_lista
            )
            if not confirmacao:
                return
                
            bloquear_controles_list(True)
            cancel_event_list.clear()
            progress_bar_list.pack(side=tk.LEFT, padx=5)
            progress_bar_list.config(mode='determinate', maximum=100, value=0)
            btn_cancelar_list.pack(side=tk.LEFT, padx=5)

            def thread_run():
                import queue
                sucessos = 0
                pulados = 0
                erros = 0
                for i, item in enumerate(selected):
                    if cancel_event_list.is_set():
                        break
                    valores = tree.item(item, "values")
                    nome_pasta = valores[0]
                    
                    local_ctx = obter_contexto_pasta(nome_pasta)
                    if not local_ctx or not local_ctx.caminho_base:
                        erros += 1
                        continue
                        
                    caminho_zip_local = os.path.join(pasta_raiz, f"{nome_pasta}.zip")
                    caminho_backup_final = os.path.join(destino_backup, f"{nome_pasta}.zip")
                    
                    if os.path.exists(caminho_backup_final):
                        q = queue.Queue()
                        def perguntar(q=q, name=nome_pasta):
                            res = messagebox.askyesno(
                                "Sobrescrever Backup",
                                f"O arquivo de backup '{name}.zip' já existe na pasta de destino.\nDeseja sobrescrevê-lo?",
                                parent=janela_lista
                            )
                            q.put(res)
                        janela_lista.after(0, perguntar)
                        sobrescrever = q.get()
                        if not sobrescrever:
                            pulados += 1
                            continue
                    
                    try:
                        # Etapa 1: Compactando pasta
                        janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: (
                            lbl_status.config(text=f"[{idx}/{tot}] {name} - Etapa 1/5: Compactando pasta..."),
                            progress_bar_list.config(value=20)
                        ))
                        shutil.make_archive(
                            base_name=os.path.join(pasta_raiz, nome_pasta),
                            format='zip',
                            root_dir=pasta_raiz,
                            base_dir=nome_pasta
                        )
                        
                        # Etapa 2: Copiando para destino de backup
                        janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: (
                            lbl_status.config(text=f"[{idx}/{tot}] {name} - Etapa 2/5: Copiando para destino de backup..."),
                            progress_bar_list.config(value=40)
                        ))
                        shutil.copy2(caminho_zip_local, caminho_backup_final)
                        
                        # Etapa 3: Verificando integridade
                        janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: (
                            lbl_status.config(text=f"[{idx}/{tot}] {name} - Etapa 3/5: Verificando integridade..."),
                            progress_bar_list.config(value=60)
                        ))
                        
                        if os.path.exists(caminho_backup_final) and os.path.getsize(caminho_backup_final) == os.path.getsize(caminho_zip_local):
                            # Etapa 4: Removendo pasta local original
                            janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: (
                                lbl_status.config(text=f"[{idx}/{tot}] {name} - Etapa 4/5: Removendo pasta local original..."),
                                progress_bar_list.config(value=80)
                            ))
                            shutil.rmtree(local_ctx.caminho_base)
                            
                            # Etapa 5: Removendo compactado temporário
                            janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: (
                                lbl_status.config(text=f"[{idx}/{tot}] {name} - Etapa 5/5: Removendo compactado temporário..."),
                                progress_bar_list.config(value=100)
                            ))
                            if os.path.exists(caminho_zip_local):
                                os.remove(caminho_zip_local)
                            sucessos += 1
                        else:
                            raise Exception("Falha ao confirmar o tamanho do arquivo de backup copiado.")
                    except Exception as e:
                        print(f"Erro no backup de {nome_pasta}: {e}")
                        try:
                            if os.path.exists(caminho_zip_local):
                                os.remove(caminho_zip_local)
                        except Exception:
                            pass
                        erros += 1
                        
                janela_lista.after(0, lambda: lbl_status.config(text=f"Backup concluído. Sucessos: {sucessos}, Pulados: {pulados}, Erros: {erros}."))
                janela_lista.after(0, lambda: messagebox.showinfo("Backup Concluído", f"O processo de backup foi finalizado com sucesso!\n\nSucessos: {sucessos}\nPulados (não sobrescritos): {pulados}\nErros: {erros}", parent=janela_lista))
                finalizar_lote()
                janela_lista.after(0, atualizar_tamanhos_tabela)
                
            threading.Thread(target=thread_run, daemon=True).start()

        def atualizar_tamanhos_tabela():
            tree.delete(*tree.get_children())
            lbl_status.config(text="Recalculando tamanhos... por favor aguarde.")
            threading.Thread(target=popular_tree, daemon=True).start()

        def recriar_diretorios_lote():
            selected = tree.selection()
            if not selected:
                return
            confirmacao = messagebox.askyesno(
                "Confirmar Recriação em Lote",
                f"Deseja realmente RECRIAR os diretórios dos {len(selected)} processos selecionados?\nTodos os arquivos existentes nestas pastas serão apagados permanentemente!",
                parent=janela_lista
            )
            if not confirmacao:
                return
                
            bloquear_controles_list(True)
            cancel_event_list.clear()
            progress_bar_list.pack(side=tk.LEFT, padx=5)
            progress_bar_list.config(mode='indeterminate')
            progress_bar_list.start()
            btn_cancelar_list.pack(side=tk.LEFT, padx=5)

            def thread_run():
                sucessos = 0
                erros = 0
                for i, item in enumerate(selected):
                    if cancel_event_list.is_set():
                        break
                    valores = tree.item(item, "values")
                    nome_pasta = valores[0]
                    janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: lbl_status.config(text=f"Recriando {idx} de {tot}: {name}..."))
                    
                    local_ctx = obter_contexto_pasta(nome_pasta)
                    if not local_ctx:
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
                        sucessos += 1
                    except Exception as e:
                        print(f"Erro ao recriar {nome_pasta}: {e}")
                        erros += 1
                        
                janela_lista.after(0, lambda: lbl_status.config(text=f"Recriação concluída. Sucessos: {sucessos}, Erros: {erros}."))
                finalizar_lote()
                janela_lista.after(0, atualizar_tamanhos_tabela)
                
            threading.Thread(target=thread_run, daemon=True).start()

        def processar_anexos_lote():
            selected = tree.selection()
            if not selected:
                return
                
            bloquear_controles_list(True)
            cancel_event_list.clear()
            progress_bar_list.pack(side=tk.LEFT, padx=5)
            progress_bar_list.config(mode='determinate', maximum=100, value=0)
            btn_cancelar_list.pack(side=tk.LEFT, padx=5)

            def thread_run():
                sucessos = 0
                erros = 0
                for i, item in enumerate(selected):
                    if cancel_event_list.is_set():
                        break
                    valores = tree.item(item, "values")
                    nome_pasta = valores[0]
                    
                    def local_callback_progresso(pct, desc, idx=i, tot=len(selected), name=nome_pasta):
                        progresso_total = int((idx * 100 + pct) / tot)
                        janela_lista.after(0, lambda p=progresso_total, d=desc: (
                            lbl_status.config(text=f"[{idx+1}/{tot}] {name} - {d}"),
                            progress_bar_list.config(value=p)
                        ))
                    
                    local_ctx = obter_contexto_pasta(nome_pasta)
                    if not local_ctx:
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
                        erros += 1
                        continue
                        
                    local_ctx.numero_laudo = num_laudo
                    local_ctx.ano = ano_laudo if ano_laudo else datetime.now().year
                    local_ctx.auto_enviar = auto_enviar.get()
                    local_ctx.cancel_event = cancel_event_list
                    
                    try:
                        services.processar_anexos(local_ctx, callback_progresso=local_callback_progresso)
                        sucessos += 1
                        if local_ctx.auto_enviar:
                            janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: lbl_status.config(text=f"[{idx}/{tot}] {name} - Enviando ao Storage..."))
                            services.enviar_ao_storage(local_ctx, confirmar_sobrescrever=perguntar_sobrescrever_lote, cancel_event=cancel_event_list)
                    except Exception as e:
                        print(f"Erro ao processar/enviar {nome_pasta}: {e}")
                        erros += 1
                        
                janela_lista.after(0, lambda: lbl_status.config(text=f"Processamento concluído. Sucessos: {sucessos}, Erros: {erros}."))
                finalizar_lote()
                janela_lista.after(0, atualizar_tamanhos_tabela)
                janela_lista.after(0, atualizar_botoes_gui)
                
            threading.Thread(target=thread_run, daemon=True).start()

        def enviar_storage_lote():
            selected = tree.selection()
            if not selected:
                return
                
            bloquear_controles_list(True)
            cancel_event_list.clear()
            progress_bar_list.pack(side=tk.LEFT, padx=5)
            progress_bar_list.config(mode='indeterminate')
            progress_bar_list.start()
            btn_cancelar_list.pack(side=tk.LEFT, padx=5)

            def thread_run():
                sucessos = 0
                erros = 0
                for i, item in enumerate(selected):
                    if cancel_event_list.is_set():
                        break
                    valores = tree.item(item, "values")
                    nome_pasta = valores[0]
                    janela_lista.after(0, lambda idx=i+1, tot=len(selected), name=nome_pasta: lbl_status.config(text=f"Enviando {idx} de {tot}: {name}..."))
                    
                    local_ctx = obter_contexto_pasta(nome_pasta)
                    if not local_ctx:
                        erros += 1
                        continue
                    
                    if not local_ctx.caminho_zip or not os.path.exists(local_ctx.caminho_zip):
                        utils.tentar_restaurar_processamento(local_ctx)
                        if not local_ctx.caminho_zip or not os.path.exists(local_ctx.caminho_zip):
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
                        erros += 1
                        continue
                    local_ctx.numero_laudo = num_laudo
                    local_ctx.ano = ano_laudo if ano_laudo else datetime.now().year
                    local_ctx.cancel_event = cancel_event_list
                    
                    try:
                        services.enviar_ao_storage(local_ctx, confirmar_sobrescrever=perguntar_sobrescrever_lote, cancel_event=cancel_event_list)
                        sucessos += 1
                    except Exception as e:
                        print(f"Erro ao enviar {nome_pasta}: {e}")
                        erros += 1
                        
                janela_lista.after(0, lambda: lbl_status.config(text=f"Envio concluído. Sucessos: {sucessos}, Erros: {erros}."))
                finalizar_lote()
                janela_lista.after(0, atualizar_botoes_gui)
                
            threading.Thread(target=thread_run, daemon=True).start()
        
        def popular_tree():
            for nome_pasta in os.listdir(pasta_raiz):
                caminho_completo = os.path.join(pasta_raiz, nome_pasta)
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
                    janela_lista.after(0, lambda p=nome_pasta, t=tamanho_formatado: tree.insert("", tk.END, values=(p, t)))
            
            janela_lista.after(0, lambda: lbl_status.config(text="Cálculo concluído."))
        
        threading.Thread(target=popular_tree, daemon=True).start()

    def criar_diretorios():
        if not ctx.dados or not ctx.protocolo:
            messagebox.showerror("Erro", "Não há dados de protocolo para criar os diretórios.")
            return
            
        pasta_raiz = config.get('pasta_raiz')
        if not pasta_raiz or not os.path.isdir(pasta_raiz):
            messagebox.showinfo("Aviso", "Pasta raiz não configurada ou inválida.\nPor favor, selecione no explorador de arquivos.")
            pasta_selecionada = filedialog.askdirectory(title="Selecione a Pasta Raiz")
            if not pasta_selecionada:
                return
            config['pasta_raiz'] = pasta_selecionada
            utils.salvar_config(config)
            pasta_raiz = pasta_selecionada


        caminho_base = utils.obter_caminho_base(ctx.protocolo, ctx.dados, pasta_raiz)
        if not caminho_base:
            return
        
        if os.path.exists(caminho_base):
            messagebox.showinfo("Aviso", "O diretório para este protocolo já existe.")
            btn_criar_dir.pack_forget()
            return
            
        pastas_para_criar = ['Extração', 'Fotos', 'Laudo', 'Relatorios', 'Relatorios/Anexo Digital']
        
        try:
            os.makedirs(caminho_base, exist_ok=True)
            for pasta in pastas_para_criar:
                os.makedirs(os.path.join(caminho_base, pasta), exist_ok=True)
            caminho_json = os.path.join(caminho_base, 'Laudo', 'dados_protocolo.json')
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(ctx.dados, f, indent=4, ensure_ascii=False)
            if ctx.texto_resultado:
                caminho_txt = os.path.join(caminho_base, 'Laudo', 'Resumo_Laudo.txt')
                utils.salvar_resumo_txt(caminho_txt, ctx.protocolo, ctx.texto_resultado)
            messagebox.showinfo("Sucesso", f"Diretórios criados com sucesso em:\n{caminho_base}")
            ctx.caminho_zip = ""
            ctx.senha = ""
            ctx.hash_diretorio = ""
            atualizar_botoes_gui()
            os.startfile(caminho_base)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar diretórios: {e}")

    def recriar_diretorios():
        if not ctx.dados or not ctx.protocolo:
            messagebox.showerror("Erro", "Não há dados de protocolo para recriar os diretórios.")
            return
            
        pasta_raiz = config.get('pasta_raiz')
        if not pasta_raiz or not os.path.isdir(pasta_raiz):
            messagebox.showinfo("Aviso", "Pasta raiz não configurada ou inválida.\nPor favor, selecione no explorador de arquivos.")
            pasta_selecionada = filedialog.askdirectory(title="Selecione a Pasta Raiz")
            if not pasta_selecionada:
                return
            config['pasta_raiz'] = pasta_selecionada
            utils.salvar_config(config)
            pasta_raiz = pasta_selecionada

        caminho_base = utils.obter_caminho_base(ctx.protocolo, ctx.dados, pasta_raiz)
        if not caminho_base:
            return
            
        if os.path.exists(caminho_base):
            confirmacao = messagebox.askyesno(
                "Confirmar Recriação", 
                f"O diretório já existe em:\n{caminho_base}\n\nTem certeza de que deseja RECRIAR? Todos os arquivos existentes nesta pasta serão apagados permanentemente!"
            )
            if not confirmacao:
                return
            
            try:
                shutil.rmtree(caminho_base)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao apagar o diretório existente: {e}")
                return
                
        pastas_para_criar = ['Extração', 'Fotos', 'Laudo', 'Relatorios', 'Relatorios/Anexo Digital']
        
        try:
            os.makedirs(caminho_base, exist_ok=True)
            for pasta in pastas_para_criar:
                os.makedirs(os.path.join(caminho_base, pasta), exist_ok=True)
            caminho_json = os.path.join(caminho_base, 'Laudo', 'dados_protocolo.json')
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(ctx.dados, f, indent=4, ensure_ascii=False)
            if ctx.texto_resultado:
                caminho_txt = os.path.join(caminho_base, 'Laudo', 'Resumo_Laudo.txt')
                utils.salvar_resumo_txt(caminho_txt, ctx.protocolo, ctx.texto_resultado)
            messagebox.showinfo("Sucesso", f"Diretórios recriados com sucesso em:\n{caminho_base}")
            ctx.caminho_zip = ""
            ctx.senha = ""
            ctx.hash_diretorio = ""
            atualizar_botoes_gui()
            os.startfile(caminho_base)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar diretórios: {e}")

    def perguntar_sobrescrever(caminho):
        import queue
        q = queue.Queue()
        def ask():
            res = messagebox.askyesno(
                "Confirmar Sobrescrita", 
                f"O arquivo já existe no destino:\n{caminho}\n\nDeseja sobrescrevê-lo?",
                parent=janela
            )
            q.put(res)
        janela.after(0, ask)
        return q.get()

    janela = tk.Tk()
    janela.title("GAD (Gerenciador de Anexo Digital)")
    janela.geometry("900x650")
    
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
        
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
    style.configure("Process.TButton", foreground="#FFFFFF", background="#3498DB")
    style.map("Process.TButton", background=[("active", "#2980B9")])
    style.configure("Action.TButton", foreground="#FFFFFF", background="#2ECC71")
    style.map("Action.TButton", background=[("active", "#27AE60")])
    style.configure("Upload.TButton", foreground="#FFFFFF", background="#9B59B6")
    style.map("Upload.TButton", background=[("active", "#8E44AD")])
    style.configure("Danger.TButton", foreground="#FFFFFF", background="#E74C3C")
    style.map("Danger.TButton", background=[("active", "#C0392B")])
    style.configure("TLabel", font=("Segoe UI", 11))
    style.configure("TEntry", font=("Segoe UI", 11))
    style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2C3E50")
    
    menu_bar = tk.Menu(janela)
    menu_config = tk.Menu(menu_bar, tearoff=0)
    menu_config.add_command(label="Configurações...", command=abrir_configuracoes)
    menu_config.add_separator()
    menu_config.add_command(label="Processos locais...", command=listar_diretorios)
    menu_bar.add_cascade(label="Configurações", menu=menu_config)
    janela.config(menu=menu_bar)
    
    lbl_titulo = ttk.Label(janela, text="SISTEMA GAD", style="Header.TLabel")
    lbl_titulo.pack(pady=(15, 5))
    

    
    frame_top = ttk.Frame(janela)
    frame_top.pack(pady=10, padx=20, fill=tk.X)
    
    frame_botoes = ttk.Frame(janela)
    frame_botoes.pack(pady=5, padx=20, fill=tk.X)
    
    lbl_protocolo = ttk.Label(frame_top, text="Número do Protocolo:")
    lbl_protocolo.pack(side=tk.LEFT, padx=(0, 10))
    
    entry_protocolo = ttk.Entry(frame_top, width=30)
    entry_protocolo.pack(side=tk.LEFT, padx=5)
    entry_protocolo.bind("<Return>", lambda event: realizar_consulta())
    
    btn_consultar = ttk.Button(frame_top, text="Consultar Protocolo", command=realizar_consulta)
    btn_consultar.pack(side=tk.LEFT, padx=10)
    
    style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#007BFF")
    style.map("Action.TButton", background=[("active", "#0056b3")])
    
    style.configure("Process.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#28A745")
    style.map("Process.TButton", background=[("active", "#218838")])
    
    style.configure("Upload.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#6F42C1")
    style.map("Upload.TButton", background=[("active", "#5A32A3")])
    
    style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#DC3545")
    style.map("Danger.TButton", background=[("active", "#C82333")])

    btn_criar_dir = ttk.Button(frame_botoes, text="Criar Diretórios GAD", style="Action.TButton", command=criar_diretorios, state=tk.DISABLED)
    btn_recriar_dir = ttk.Button(frame_botoes, text="Recriar Diretórios", style="Danger.TButton", command=recriar_diretorios)
    
    def processar_anexos_gui():
        if not ctx.dados or not ctx.protocolo:
            return
            
        caminho_base = utils.obter_caminho_base(ctx.protocolo, ctx.dados, config.get('pasta_raiz'))
        if not caminho_base or not os.path.exists(caminho_base):
            messagebox.showerror("Erro", "O diretório do protocolo ainda não foi criado.")
            return
            
        # Verifica se há laudo criado no sistema Galileu e extrai o número e o ano
        laudo_criado = False
        num_laudo = None
        ano_laudo = None
        
        if isinstance(ctx.dados, dict):
            laudo = ctx.dados.get('laudo')
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
            messagebox.showwarning("Aviso", "Não foi encontrado nenhum laudo criado para este protocolo no Galileu.\nPor favor, primeiro crie um número de laudo no Galileu.")
            return
            
        ctx.numero_laudo = num_laudo
        if ano_laudo:
            ctx.ano = ano_laudo
        else:
            from datetime import datetime
            if isinstance(ctx.dados, dict) and 'ano' in ctx.dados:
                ctx.ano = ctx.dados['ano']
            else:
                ctx.ano = datetime.now().year
                
        # Sobrescreve o dados_protocolo.json local com os dados atualizados em memória
        caminho_json = os.path.join(caminho_base, 'Laudo', 'dados_protocolo.json')
        try:
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(ctx.dados, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao atualizar dados_protocolo.json: {e}")
            
        btn_processar.config(state=tk.DISABLED)
        btn_reprocessar.config(state=tk.DISABLED)
        progress_bar.pack(side=tk.LEFT, padx=5)
        progress_bar.config(mode='determinate', maximum=100, value=0)

        import queue
        spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        spinner_state = {"index": 0, "active": False}

        def animar_spinner():
            if not spinner_state["active"] or not txt_resultado.winfo_exists():
                return
            try:
                frame = spinner_frames[spinner_state["index"] % len(spinner_frames)]
                spinner_state["index"] += 1
                if "spinner_mark" in txt_resultado.mark_names():
                    txt_resultado.config(state=tk.NORMAL)
                    txt_resultado.delete("spinner_mark", "spinner_mark lineend")
                    txt_resultado.insert("spinner_mark", f"[{frame}]", "aviso")
                    txt_resultado.config(state=tk.DISABLED)
            except Exception:
                pass
            janela.after(100, animar_spinner)

        def finalizar_etapa_anterior(sucesso=True):
            if "spinner_mark" in txt_resultado.mark_names():
                spinner_state["active"] = False
                tag = "sucesso" if sucesso else "erro"
                status_txt = "[SUCESSO]" if sucesso else "[FALHA]"
                
                q = queue.Queue()
                def run():
                    try:
                        txt_resultado.config(state=tk.NORMAL)
                        txt_resultado.delete("spinner_mark", "spinner_mark lineend")
                        txt_resultado.insert("spinner_mark", status_txt, tag)
                        txt_resultado.mark_unset("spinner_mark")
                        txt_resultado.see(tk.END)
                        txt_resultado.config(state=tk.DISABLED)
                    except Exception:
                        pass
                    q.put(True)
                janela.after(0, run)
                q.get()

        def iniciar_etapa(etapa_str, desc):
            finalizar_etapa_anterior(sucesso=True)
            
            q = queue.Queue()
            def run():
                try:
                    txt_resultado.config(state=tk.NORMAL)
                    txt_resultado.insert(tk.END, f"-> {etapa_str}{desc} ... ")
                    txt_resultado.mark_set("spinner_mark", "insert")
                    txt_resultado.mark_gravity("spinner_mark", tk.LEFT)
                    txt_resultado.insert(tk.END, "[⠋]\n")
                    txt_resultado.see(tk.END)
                    txt_resultado.config(state=tk.DISABLED)
                except Exception:
                    pass
                q.put(True)
            janela.after(0, run)
            q.get()
            
            spinner_state["active"] = True
            janela.after(100, animar_spinner)

        def callback_progresso_gui(pct, desc):
            # Mapeia a porcentagem para a etapa correspondente
            etapa_str = ""
            if pct == 25:
                etapa_str = "[Etapa 1/4] "
            elif pct == 50:
                etapa_str = "[Etapa 2/4] "
            elif pct == 75:
                etapa_str = "[Etapa 3/4] "
            elif pct == 100:
                etapa_str = "[Etapa 4/4] "
                
            janela.after(0, lambda: progress_bar.config(value=pct))
            iniciar_etapa(etapa_str, desc)

        def thread_proc():
            try:
                # Limpa e prepara a caixa de texto
                q = queue.Queue()
                def setup_txt():
                    try:
                        txt_resultado.config(state=tk.NORMAL)
                        txt_resultado.delete("1.0", tk.END)
                        txt_resultado.insert(tk.END, "Iniciando processamento de anexos...\n")
                        txt_resultado.config(state=tk.DISABLED)
                    except Exception:
                        pass
                    q.put(True)
                janela.after(0, setup_txt)
                q.get()
                
                services.processar_anexos(ctx, callback_progresso=callback_progresso_gui)
                finalizar_etapa_anterior(sucesso=True)
                janela.after(0, atualizar_botoes_gui)
                
                if ctx.auto_enviar:
                    janela.after(0, lambda: btn_cancelar_envio.pack(side=tk.LEFT, padx=5))
                    janela.after(0, lambda: definir_estado_controles(False))
                    
                    iniciar_etapa("[Envio] ", "Copiando arquivo para a rede")
                    ctx.cancel_event.clear()
                    try:
                        destino = services.enviar_ao_storage(ctx, confirmar_sobrescrever=perguntar_sobrescrever, cancel_event=ctx.cancel_event)
                        if not (ctx.cancel_event and ctx.cancel_event.is_set()):
                            finalizar_etapa_anterior(sucesso=True)
                            janela.after(0, lambda dest=destino: (
                                txt_resultado.config(state=tk.NORMAL),
                                txt_resultado.insert(tk.END, f"\n[SUCESSO] Processamento e envio concluídos com sucesso!\nSalvo em rede: {dest}\n", "sucesso"),
                                txt_resultado.see(tk.END),
                                txt_resultado.config(state=tk.DISABLED)
                            ))
                    except services.ServiceError as env_err:
                        if not (ctx.cancel_event and ctx.cancel_event.is_set()):
                            finalizar_etapa_anterior(sucesso=False)
                            msg_err = f"\n[ERRO] Falha no envio ao Storage: {env_err}\n"
                            janela.after(0, lambda msg=msg_err: (
                                txt_resultado.config(state=tk.NORMAL),
                                txt_resultado.insert(tk.END, msg, "erro"),
                                txt_resultado.see(tk.END),
                                txt_resultado.config(state=tk.DISABLED)
                            ))
                    finally:
                        janela.after(0, lambda: btn_cancelar_envio.pack_forget())
                        janela.after(0, lambda: definir_estado_controles(True))
                else:
                    janela.after(0, lambda: (
                        txt_resultado.config(state=tk.NORMAL),
                        txt_resultado.insert(tk.END, "\n[SUCESSO] Processamento de anexos concluído localmente com sucesso!\n", "sucesso"),
                        txt_resultado.see(tk.END),
                        txt_resultado.config(state=tk.DISABLED)
                    ))
            except services.ServiceError as e:
                finalizar_etapa_anterior(sucesso=False)
                msg_erro = f"\n[ERRO] Falha no processamento: {e}\n"
                janela.after(0, lambda msg=msg_erro: (
                    txt_resultado.config(state=tk.NORMAL),
                    txt_resultado.insert(tk.END, msg, "erro"),
                    txt_resultado.see(tk.END),
                    txt_resultado.config(state=tk.DISABLED)
                ))
            finally:
                janela.after(0, lambda: btn_processar.config(state=tk.NORMAL))
                janela.after(0, lambda: btn_reprocessar.config(state=tk.NORMAL))
                janela.after(0, lambda: progress_bar.stop())
                janela.after(0, lambda: progress_bar.pack_forget())
                janela.after(0, atualizar_botoes_gui)
                
        threading.Thread(target=thread_proc, daemon=True).start()
        
    def enviar_storage_gui():
        btn_enviar.config(state=tk.DISABLED)
        progress_bar.pack(side=tk.LEFT, padx=5)
        progress_bar.start()

        def thread_envio():
            janela.after(0, lambda: btn_cancelar_envio.pack(side=tk.LEFT, padx=5))
            janela.after(0, lambda: definir_estado_controles(False))
            ctx.cancel_event.clear()
            try:
                destino = services.enviar_ao_storage(ctx, confirmar_sobrescrever=perguntar_sobrescrever, cancel_event=ctx.cancel_event)
                if not (ctx.cancel_event and ctx.cancel_event.is_set()):
                    janela.after(0, lambda: messagebox.showinfo("Upload Concluído", f"Arquivo enviado com sucesso para a rede:\n{destino}"))
            except services.ServiceError as e:
                if not (ctx.cancel_event and ctx.cancel_event.is_set()):
                    msg_erro = f"Falha ao enviar para o Storage:\n{e}"
                    janela.after(0, lambda msg=msg_erro: messagebox.showerror("Erro de Rede", msg))
            finally:
                janela.after(0, lambda: btn_cancelar_envio.pack_forget())
                janela.after(0, lambda: definir_estado_controles(True))
                janela.after(0, atualizar_botoes_gui)
                janela.after(0, lambda: progress_bar.stop())
                janela.after(0, lambda: progress_bar.pack_forget())
                
        threading.Thread(target=thread_envio, daemon=True).start()

    auto_enviar = tk.BooleanVar(value=True)
    def sync_auto(*args):
        ctx.auto_enviar = auto_enviar.get()
    auto_enviar.trace_add('write', sync_auto)
    sync_auto()

    chk_auto = ttk.Checkbutton(frame_botoes, text="Enviar automaticamente ao Storage", variable=auto_enviar)
    # chk_auto.pack is now handled after a successful query
    # Botões e barra de progresso do novo fluxo
    btn_processar = ttk.Button(frame_botoes, text="1. Processar Anexos (ZIP/Hash)", style="Process.TButton", command=processar_anexos_gui)
    btn_reprocessar = ttk.Button(frame_botoes, text="Reprocessar", style="Process.TButton", command=processar_anexos_gui)
    btn_abrir_dir = ttk.Button(frame_botoes, text="Abrir Pasta", style="Action.TButton", command=lambda: os.startfile(ctx.caminho_base) if ctx.caminho_base else None)
    btn_enviar = ttk.Button(frame_botoes, text="2. Enviar p/ Storage", style="Upload.TButton", command=enviar_storage_gui)
    btn_cancelar_envio = ttk.Button(frame_botoes, text="Cancelar Envio", style="Danger.TButton", command=lambda: cancelar_envio_gui())

    def cancelar_envio_gui():
        if messagebox.askyesno("Confirmar Cancelamento", "Deseja realmente cancelar o envio para o Storage?"):
            if ctx.cancel_event:
                ctx.cancel_event.set()
                definir_estado_controles(True)
                btn_cancelar_envio.pack_forget()
                progress_bar.stop()
                progress_bar.pack_forget()

    def definir_estado_controles(ativo):
        state = tk.NORMAL if ativo else tk.DISABLED
        entry_state = tk.NORMAL if ativo else tk.DISABLED
        menu_state = tk.NORMAL if ativo else tk.DISABLED
        
        entry_protocolo.config(state=entry_state)
        btn_consultar.config(state=state)
        btn_criar_dir.config(state=state)
        btn_recriar_dir.config(state=state)
        btn_processar.config(state=state)
        btn_reprocessar.config(state=state)
        btn_enviar.config(state=state)
        chk_auto.config(state=state)
        try:
            menu_bar.entryconfig("Configurações", state=menu_state)
        except Exception:
            pass

        for attr in ['btn_recriar_dir_list', 'btn_processar_list', 'btn_reprocessar_list', 'btn_enviar_list', 'chk_auto_list', 'btn_limpar_extracao_list', 'btn_backup_list']:
            if hasattr(janela, attr):
                try:
                    getattr(janela, attr).config(state=state)
                except Exception:
                    pass
        if hasattr(janela, 'tree_list'):
            try:
                janela.tree_list.config(selectmode="none" if not ativo else "extended")
            except Exception:
                pass

    def atualizar_botoes_gui():
        def verificar_se_ja_enviado(local_ctx):
            if not local_ctx.caminho_base or not os.path.exists(local_ctx.caminho_base):
                return False
                
            # Localize INFO.txt
            pasta_anexo = os.path.join(local_ctx.caminho_base, 'Relatorios', 'Anexo Digital')
            arquivo_info = os.path.join(pasta_anexo, 'INFO.txt')
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
            except Exception as e:
                print(f"[DEBUG] Erro ao ler {arquivo_info}: {e}")
                return False
                
            if not url_storage:
                return False
                
            chave_laudos = "/laudos/"
            if chave_laudos not in url_storage:
                return False
                
            caminho_relativo = url_storage.split(chave_laudos, 1)[1]
            partes = caminho_relativo.split('/')
            
            storage_base = config.get('destino_storage', r'\\periciadigital.ssp.to.gov.br\Web\laudos')
            destino_arquivo = os.path.join(storage_base, *partes)
            
            print(f"[DEBUG] verificar_se_ja_enviado: destino_arquivo na rede = {destino_arquivo}")
            try:
                existe = os.path.exists(destino_arquivo)
                print(f"[DEBUG] resultado de os.path.exists({destino_arquivo}) = {existe}")
                return existe
            except Exception as e:
                print(f"[DEBUG] erro ao testar os.path.exists({destino_arquivo}): {e}")
                return False

        # 1. Main window
        btn_criar_dir.pack_forget()
        btn_recriar_dir.pack_forget()
        btn_processar.pack_forget()
        btn_reprocessar.pack_forget()
        btn_abrir_dir.pack_forget()
        btn_enviar.pack_forget()
        chk_auto.pack_forget()
        
        if ctx.caminho_base:
            chk_auto.pack(side=tk.LEFT, padx=5)
            if os.path.exists(ctx.caminho_base):
                btn_recriar_dir.pack(side=tk.LEFT, padx=5)
                btn_abrir_dir.pack(side=tk.LEFT, padx=5)
                if utils.tentar_restaurar_processamento(ctx):
                    btn_reprocessar.pack(side=tk.LEFT, padx=5)
                    btn_enviar.pack(side=tk.LEFT, padx=5)
                    btn_enviar.config(state=tk.NORMAL)
                    if verificar_se_ja_enviado(ctx):
                        btn_enviar.config(text="Reenviar p/ Storage")
                    else:
                        btn_enviar.config(text="2. Enviar p/ Storage")
                else:
                    btn_processar.pack(side=tk.LEFT, padx=5)
            else:
                btn_criar_dir.pack(side=tk.LEFT, padx=5)
                btn_criar_dir.config(state=tk.NORMAL)
        
        # 2. List window
        list_attrs = ['btn_recriar_dir_list', 'btn_processar_list', 'btn_reprocessar_list', 'btn_abrir_dir_list', 'btn_enviar_list', 'chk_auto_list', 'btn_limpar_extracao_list', 'btn_backup_list']
        has_list = all(hasattr(janela, attr) for attr in list_attrs)
        if has_list:
            try:
                if janela.btn_recriar_dir_list.winfo_exists():
                    janela.btn_recriar_dir_list.pack_forget()
                    janela.btn_processar_list.pack_forget()
                    janela.btn_reprocessar_list.pack_forget()
                    janela.btn_abrir_dir_list.pack_forget()
                    janela.btn_enviar_list.pack_forget()
                    janela.chk_auto_list.pack_forget()
                    janela.btn_limpar_extracao_list.pack_forget()
                    janela.btn_backup_list.pack_forget()
                    
                    if hasattr(janela, 'tree_list') and janela.tree_list.winfo_exists():
                        selected = janela.tree_list.selection()
                        if len(selected) > 1:
                            janela.chk_auto_list.pack(side=tk.LEFT, padx=5)
                            janela.btn_recriar_dir_list.pack(side=tk.LEFT, padx=5)
                            janela.btn_processar_list.pack(side=tk.LEFT, padx=5)
                            janela.btn_reprocessar_list.pack(side=tk.LEFT, padx=5)
                            janela.btn_enviar_list.pack(side=tk.LEFT, padx=5)
                            janela.btn_enviar_list.config(state=tk.NORMAL)
                            janela.btn_enviar_list.config(text="2. Enviar p/ Storage")
                            janela.btn_limpar_extracao_list.pack(side=tk.LEFT, padx=5)
                            janela.btn_backup_list.pack(side=tk.LEFT, padx=5)
                        elif len(selected) == 1:
                            if ctx.caminho_base and os.path.exists(ctx.caminho_base):
                                janela.chk_auto_list.pack(side=tk.LEFT, padx=5)
                                janela.btn_recriar_dir_list.pack(side=tk.LEFT, padx=5)
                                janela.btn_abrir_dir_list.pack(side=tk.LEFT, padx=5)
                                janela.btn_limpar_extracao_list.pack(side=tk.LEFT, padx=5)
                                janela.btn_backup_list.pack(side=tk.LEFT, padx=5)
                                if utils.tentar_restaurar_processamento(ctx):
                                    janela.btn_reprocessar_list.pack(side=tk.LEFT, padx=5)
                                    janela.btn_enviar_list.pack(side=tk.LEFT, padx=5)
                                    janela.btn_enviar_list.config(state=tk.NORMAL)
                                    if verificar_se_ja_enviado(ctx):
                                         janela.btn_enviar_list.config(text="Reenviar p/ Storage")
                                    else:
                                         janela.btn_enviar_list.config(text="2. Enviar p/ Storage")
                                else:
                                    janela.btn_processar_list.pack(side=tk.LEFT, padx=5)
            except Exception:
                pass
    # Substituir label de progresso por Progressbar
    progress_bar = ttk.Progressbar(frame_botoes, mode='indeterminate')
    # Checkbox já existente usa auto_enviar BooleanVar; sincronizar com ctx
    def sync_auto():
        ctx.auto_enviar = auto_enviar.get()
    auto_enviar.trace_add('write', lambda *args: sync_auto())

    frame_txt = ttk.Frame(janela)
    frame_txt.pack(pady=10, padx=20, fill=tk.X)
    
    txt_resultado = ScrolledText(frame_txt, wrap=tk.WORD, font=("Courier New", 10), height=5)
    txt_resultado.pack(fill=tk.X, expand=False)
    
    # Configuração de tags para realce de texto
    txt_resultado.tag_config("sucesso", foreground="green", font=("Courier New", 11, "bold"))
    txt_resultado.tag_config("erro", foreground="red", font=("Courier New", 11, "bold"))
    txt_resultado.tag_config("aviso", foreground="#FF8C00", font=("Courier New", 10, "bold"))
    
    # Frame para exibir a tabela de resultados com Treeview (Smooth scroll)
    frame_tree = tk.Frame(janela)
    # Por padrão, a tabela fica oculta (não empacotada no início)
    
    # Treeview nativo do ttk
    tree_dados = ttk.Treeview(frame_tree, show="headings")
    
    # Scrollbars para a Treeview
    scroll_y = ttk.Scrollbar(frame_tree, orient="vertical", command=tree_dados.yview)
    scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=tree_dados.xview)
    tree_dados.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)
    
    # Pack Treeview e Scrollbars
    tree_dados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Opção para exibir ou ocultar a tabela de dados
    exibir_tabela_var = tk.BooleanVar(value=False)
    
    def toggle_tabela(*args):
        if exibir_tabela_var.get():
            frame_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        else:
            frame_tree.pack_forget()
            
    exibir_tabela_var.trace_add('write', toggle_tabela)
    
    chk_exibir_tabela = ttk.Checkbutton(frame_top, text="Exibir Tabela de Dados", variable=exibir_tabela_var)
    chk_exibir_tabela.pack(side=tk.LEFT, padx=15)
    
    entry_protocolo.focus()
    janela.mainloop()
