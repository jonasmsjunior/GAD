import main

if __name__ == "__main__":
    # O sistema foi refatorado. Agora o ponto de entrada principal é o main.py.
    # Este arquivo (consulta_galileu.py) foi mantido para compatibilidade.
    # Ele simplesmente redireciona a execução para o novo arquivo main.py
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] not in ["-h", "--help"]:
        sucesso, resultado, dados = main.api.consultar_protocolo(sys.argv[1])
        print(resultado)
    else:
        main.ui.iniciar_interface()
