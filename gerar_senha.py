# gerar_senha.py
import streamlit_authenticator as stauth
import sys

if len(sys.argv) > 1:
    senha_para_criptografar = [sys.argv[1]]
    hashed_password = stauth.Hasher(senha_para_criptografar).generate()
    print("Senha criptografada (copie a linha que começa com '$2b$...' ):")
    print(hashed_password[0])
else:
    print("Por favor, forneça a senha como um argumento. Exemplo: python gerar_senha.py 'SuaSenhaAqui'")