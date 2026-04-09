import subprocess as s
import os
import re
import math
import sys

# Constante de Extensoes
EXT = [".txt", ".env", ".json", ".log", ".py", ".sql", ".yaml", ".xml"]

# PADRÕES DE BUSCA - REGEX
# OS valores podem tanto estar entre aspas " " ou sem.
PADROES = {
    "Chave API": r"(?i)(api|key|token|secret|access[_-]?key)\s*[:=]\s*['\"]?[a-zA-Z0-9/+=_-]{3,100}['\"]?",
    "Senha/Password" : r"(?i)(password|passwd|senha|pwd|pass)\s*[:=]\s*['\"]?.+['\"]?",
    "String de Conexão" : r"(mongodb\+srv:\/\/|postgres:\/\/|mysql:\/\/|jdbc:)"
}

# CÁLCULO DE ENTROPIA - Shannon Entropy
def entropia(content):
    if not content: return 0
    prob = [float(content.count(c)) / len(content) for c in dict.fromkeys(list(content))]
    # formula entropia de SHannon
    entropia = - sum([ p * math.log(p,2) for p in prob])
    return entropia

if __name__ == '__main__':
    print("\nGit Pre-Commit Secret Finder v 1.0")

    # 1- Identificar arquivos para Commit
    # cuidado na execução pois ele utiliza o caminho root do repositório, é preciso executar o script de lá "cd ..".
    try: 
        # git diff --cached --name-only
        arquivos = s.check_output(["git", "diff", "--cached", "--name-only"], text=True)
        listaArquivos = arquivos.splitlines()
    except s.CalledProcessError:
        print("Erro ao acessar Git.")
        sys.exit(1)

    extensoes = EXT 

    threats = False

    for file in listaArquivos:
        if not os.path.exists(file): continue
        # Pula caso o arquivo for deletado

        relatorio = {}

        with open(file, 'r', errors='ignore') as f:
            for i, linha in enumerate(f, 1):
                # Busca de regex
                for tipo, padrao in PADROES.items():
                    if re.search(padrao, linha):
                        if i not in relatorio:
                            relatorio[i] = []
                        relatorio[i].append(f"{tipo} detectado")
                        threats = True

                # Busca por entropia
                palavras = linha.split()
                for palavra in palavras:
                    if len(palavra) > 16 and entropia(palavra) > 4.5: 
                        # Entropia acima de 4.5 é considerado Chaves, Hashes ou Base64
                        if i not in relatorio:
                            relatorio[i] = []
                            # Adiciona apenas se o Regex já não tiver classificado essa linha para evitar mensagens duplicadas na mesma linha

                        if "Possivel Segredo Ofuscado (Alta Entropia)" not in relatorio[i]:
                            relatorio[i].append("Possivel Segredo Ofuscado (Alta Entropia)")
                            threats = True
            
        # Só imprime se o dicionário do arquivo não estiver vazio
        if relatorio:
            print(f"\n" + f"="*50)
            print(f"Arquivo: {file}")
            
            # Ordena as linhas para o print ficar organizado
            for num_linha in sorted(relatorio.keys()):
                # Junta as mensagens (caso uma linha tenha pego em dois tipos de regex, por exemplo)
                mensagens = " e ".join(relatorio[num_linha])
                print(f"[!] {file} - Linha {num_linha} - {mensagens}")
    
    if threats:
        print("\n\n\n[ATENCAO] Vulnerabilidades encontradas. Corrija-as antes de realizar o commit.")
        print("Referência: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html\n")
        sys.exit(1)

    else:
        print("\n[SUCESSO] Nenhum segredo detectado.\n")
        sys.exit(0)