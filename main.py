import sys
import api

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ["-h", "--help"]:
        # Modo CLI
        protocolo = sys.argv[1]
        sucesso, resultado, dados, chaves, tabela = api.consultar_protocolo(protocolo)
        print(resultado)
    else:
        # Modo GUI (Interface amigável)
        import ui
        ui.iniciar_interface()

