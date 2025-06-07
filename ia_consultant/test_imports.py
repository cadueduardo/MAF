print("Iniciando teste de importação...")

try:
    print("Tentando importar 'Agent' de 'agent.py'...")
    from agent import Agent
    print("Importação de 'Agent' bem-sucedida.")

    print("\nTentando inicializar o Agente (isso pode levar um momento)...")
    maf_agent = Agent()
    print("Inicialização do Agente bem-sucedida!")

    print("\nTeste concluído com sucesso! O problema pode ser outro.")

except Exception as e:
    print("\n--- ERRO ENCONTRADO ---")
    print(f"Ocorreu um erro durante a inicialização:")
    # Imprime o traceback completo para depuração
    import traceback
    traceback.print_exc()
    print("\nPor favor, envie esta mensagem de erro completa.") 