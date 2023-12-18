from app.models import TokenUsuario, FuncionarioRH, Servidor
import app.functions.email as _email
from app.functions import empty
from app.functions.validate import *
from app.functions import custom_render_template as render_template
from flask import session
from werkzeug.security import generate_password_hash

def save(nome, email, telefone, cpf, senha):
    try:
        funcionario = FuncionarioRH(nome=nome.strip(), email=email.strip(),telefone=get_clean_number(telefone), cpf=get_clean_number(cpf), senha=senha.strip())
        valoresRepetidos = funcionario.getRepetido()
        if not empty(valoresRepetidos):
            if len(valoresRepetidos) == 1:
                msg = f"{valoresRepetidos[0]} já cadastrado, por favor, verifique"
            else:
                msg = "Usuário já cadastrado, por favor, verifique"
            return {'success': False, 'msg': msg}
        if funcionario.nome.count(" ") == 0:
            return {'success': False, 'msg': 'Por favor, digite seu nome completo'}
        if not name_validate(funcionario.nome):
            return {'success': False, 'msg': 'Por favor, digite um nome válido com apenas letras e espaços'}
        if not cpf_validate(funcionario.cpf):
            return {'success': False, 'msg': 'Por favor, digite um CPF válido'}
        if not validate_phone(funcionario.telefone):
            return {'success': False, 'msg': 'Por favor, digite um telefone válido'}

        save = funcionario.save()
        if not save:
            return {'success': False, 'msg': save}
        return {'success': True, 'msg': 'Cadastrado com sucesso'}
    except Exception as e:
        print(e)
        return {'success': False, 'msg': e}

def login(email, senha, remember):
    funcionario = (FuncionarioRH(login_padrao=email, senha_padrao=senha)).exists()
    if funcionario:
        session.permanent = False
        if remember == 'true':
            session.permanent = True
        session['user_id'] = funcionario.id
        return {'success': True, 'msg': '', 'confirmarEmail': False}
    else:
        servidor = (Servidor(email=email, cpf=senha)).exists()
        if servidor:
            if servidor.email_confirmado == 1:
                session.permanent = False
                if remember == 'true':
                    session.permanent = True
                session['user_id'] = funcionario.id
                return {'success': True, 'msg': '', 'confirmarEmail': False}
            else:
                return {'success': True, 'msg': '', 'confirmarEmail': True}
        else:
            return {'success': False, 'msg': 'Usuário e/ou senha incorretos'}

def makeEmailConfirmation(email):
    try:
        token = TokenUsuario.createTokenUsuario(email, 'tokenUser')
        _email.send(email, 'Código de Confirmação',
                    f"Clique para confirmar seu e-mail: http://127.0.0.1:5000/confirmation/{token}")
        return {'success': True, 'msg': 'Enviado com sucesso'}
    except Exception as e:
        return {'success': False, 'msg': str(e)}

def makePasswordRecovery(email):
    try:
        token = TokenUsuario.createTokenUsuario(email, 'passwordRecovery')
        _email.send(email, 'Link de Recuperação',
                    f"Clique para recuperar sua senha: http://127.0.0.1:5000/recovery/{token}")
        return {'success': True, 'msg': 'Enviado com sucesso'}
    except Exception as e:
        return {'success': False, 'msg': e}

def confirmEmail(token):
    type = "email"
    tokenUser = TokenUsuario.getFuncionarioToken(token, 'tokenUser')
    if len(tokenUser) == 0: # inválido
        return render_template("return_token.html", type=type, response="invalid")
    else:
        if tokenUser[0]['expirado'] == 1: # expirado
            return render_template("confirmation.html", token="expirado")
        elif tokenUser[0]['email_confirmado'] == 1: # em uso
            return render_template("return_token.html", type=type, response="used")
        elif tokenUser[0]['email_confirmado'] == 0: # sucesso
            funcionario = FuncionarioRH(id=tokenUser[0]['id'], email_confirmado=True)
            funcionario.save()
            funcionario.deleteConfirmations()
            return render_template("return_token.html", type=type, response="success")
        else:
            print("Ocorreu algum erro")
            return render_template("return_token.html", type=type, response="invalid")

def recoveryPassoword(token):
    type = "password"
    tokenUser = TokenUsuario.getFuncionarioToken(token, 'passwordRecovery')
    if len(tokenUser) == 0: # inválido
        return render_template("return_token.html", type=type, response="invalid")
    else:
        if tokenUser[0]['expirado'] == 1: # expirado
            return render_template("recovery.html", token="expirado")
        else: # sucesso
            return render_template("new_password.html", token=token)

def saveNewPassword(token, password):
    tokenUser = TokenUsuario.query.filter_by(token=token).first()
    funcionario = FuncionarioRH.query.filter_by(id=tokenUser.user_id).first()
    funcionario.senha = generate_password_hash(password);
    funcionario.email_confirmado = True
    funcionario.save()
    funcionario.deleteConfirmations()
    funcionario.deleteRecoveries()
    return render_template("return_token.html", type="password", response="success")
def corrigirEmail(oldEmail, newEmail):
    funcionario = FuncionarioRH.query.filter_by(email=oldEmail).first()
    funcionario.email = newEmail
    funcionario.save()
    funcionario.deleteConfirmations()

def checkEmailExists(email):
    funcionario = FuncionarioRH(email=email)
    return {'exists':funcionario.emailExists()}