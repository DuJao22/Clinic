from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
PASTA_UPLOADS = 'static/uploads'
app.config['UPLOAD_FOLDER'] = PASTA_UPLOADS

# Inicialização do banco de dados de usuários
def inicializar_bd_usuarios():
    with sqlite3.connect('usuarios.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cpf TEXT UNIQUE,
                            nome TEXT,
                            cargo TEXT,
                            usuario TEXT UNIQUE,
                            senha TEXT)''')
        
        # Inserir usuário administrador pré-cadastrado
        cursor.execute('''INSERT OR IGNORE INTO usuarios (cpf, nome, cargo, usuario, senha) 
                          VALUES ('00000000000', 'Dr Marcelo Henrique ADM', 'administrador', 'admin', 'MARCELO_H')''')
        conn.commit()

# Inicialização do banco de dados de pacientes
def inicializar_bd_pacientes():
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cpf TEXT UNIQUE,
                            nome TEXT,
                            convenio TEXT,
                            cep TEXT,
                            endereco TEXT,
                            numero TEXT,
                            complemento TEXT,
                            telefone TEXT,
                            data_nascimento TEXT,
                            sexo TEXT,
                            prontuario TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS consultas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_paciente INTEGER,
                            data TEXT,
                            hora TEXT,
                            chegada INTEGER DEFAULT 0,
                            concluida INTEGER DEFAULT 0,
                            FOREIGN KEY(id_paciente) REFERENCES pacientes(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS uploads (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_paciente INTEGER,
                            nome_arquivo TEXT,
                            enviado_pelo_medico INTEGER DEFAULT 0,
                            FOREIGN KEY(id_paciente) REFERENCES pacientes(id))''')
        conn.commit()

inicializar_bd_usuarios()
inicializar_bd_pacientes()

# Login de usuário
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario, senha))
            usuario = cursor.fetchone()
            if usuario:
                session['id_usuario'] = usuario[0]
                session['cargo'] = usuario[3]
                if usuario[3] == 'administrador':
                    return redirect(url_for('painel'))
                elif usuario[3] == 'recepcionista':
                    return redirect(url_for('recepcionista'))
                elif usuario[3] == 'medico':
                    return redirect(url_for('medico'))
            return 'Credenciais inválidas'
    return render_template('login.html')

# Logout de usuário
@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    session.pop('cargo', None)
    return redirect(url_for('login'))

# Painel de controle (apenas administrador)
@app.route('/painel')
def painel():
    if 'id_usuario' not in session or session['cargo'] != 'administrador':
        return redirect(url_for('login'))
    return render_template('painel.html', cargo=session['cargo'])

# Cadastro de novo paciente
@app.route('/cadastrar_paciente', methods=['GET', 'POST'])
def cadastrar_paciente():
    if 'id_usuario' not in session or session['cargo'] != 'recepcionista':
        return redirect(url_for('login'))
    if request.method == 'POST':
        cpf = request.form['cpf']
        nome = request.form['nome']
        convenio = request.form['convenio']
        cep = request.form['cep']
        endereco = request.form['endereco']
        numero = request.form['numero']
        complemento = request.form['complemento']
        telefone = request.form['telefone']
        data_nascimento = request.form['data_nascimento']
        sexo = request.form['sexo']
        
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pacientes (cpf, nome, convenio, cep, endereco, numero, complemento, telefone, data_nascimento, sexo) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cpf, nome, convenio, cep, endereco, numero, complemento, telefone, data_nascimento, sexo))
            conn.commit()
        
    return render_template('cadastrar_paciente.html')


# Cadastro de novo funcionário (apenas administrador)
@app.route('/cadastrar_funcionario', methods=['GET', 'POST'])
def cadastrar_funcionario():
    if 'id_usuario' not in session or session['cargo'] != 'administrador':
        return redirect(url_for('login'))
    if request.method == 'POST':
        cpf = request.form['cpf']
        nome = request.form['nome']
        cargo = request.form['cargo']
        usuario = request.form['usuario']
        senha = request.form['senha']
        print("ok")
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (cpf, nome, cargo, usuario, senha) VALUES (?, ?, ?, ?, ?)', (cpf, nome, cargo, usuario, senha))
            conn.commit()
        
    return render_template('cadastrar_funcionario.html')

# Agendamento de consulta
@app.route('/agendar_consulta', methods=['GET', 'POST'])
def agendar_consulta():
    if 'id_usuario' not in session or session['cargo'] != 'recepcionista':
        return redirect(url_for('login'))
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        data = request.form['data']
        hora = request.form['hora']
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO consultas (id_paciente, data, hora) VALUES (?, ?, ?)', (id_paciente, data, hora))
            conn.commit()
        
    return render_template('agendar_consulta.html')

# Registro de chegada do paciente
@app.route('/registrar_chegada', methods=['GET', 'POST'])
def registrar_chegada():
    if 'id_usuario' not in session or session['cargo'] != 'recepcionista':
        return redirect(url_for('login'))
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE consultas SET chegada = 1 WHERE id_paciente = ?', (id_paciente,))
            conn.commit()
        return redirect(url_for("recepcionista"))
    # Listar pacientes em espera
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT c.id, p.nome, c.data, c.hora 
                          FROM consultas c 
                          JOIN pacientes p ON c.id_paciente = p.id 
                          WHERE c.chegada = 0 
                          ORDER BY c.data, c.hora''')
        pacientes_em_espera = cursor.fetchall()
    return render_template('registrar_chegada.html', pacientes=pacientes_em_espera)

# Busca de pacientes para registrar chegada e agendar consulta
@app.route('/buscar_pacientes', methods=['GET'])
def buscar_pacientes():
    if 'id_usuario' not in session or session['cargo'] not in ['recepcionista', 'medico']:
        return redirect(url_for('login'))
    termo = request.args.get('termo', '')
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome FROM pacientes WHERE nome LIKE ?', ('%' + termo + '%',))
        pacientes = cursor.fetchall()
    return jsonify(pacientes)

# Visualização do prontuário do paciente
@app.route('/prontuario/<int:id_paciente>', methods=['GET'])
def prontuario(id_paciente):
    if 'id_usuario' not in session or session['cargo'] != 'medico':
        return redirect(url_for('login'))
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome, prontuario FROM pacientes WHERE id = ?', (id_paciente,))
        paciente = cursor.fetchone()
    return render_template('prontuario.html', paciente=paciente)

# Upload de documentos médicos (login paciente)
@app.route('/login_paciente', methods=['GET', 'POST'])
def login_paciente():
    if request.method == 'POST':
        cpf = request.form['cpf']
        
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pacientes WHERE cpf = ?', (cpf,))
            paciente = cursor.fetchone()
            print(paciente)
            if paciente:
                session['id_usuario'] = paciente[0]
                session['cargo'] = 'paciente'
                return redirect(url_for('upload_documento'))
            return 'Credenciais inválidas'
    return render_template('login_paciente.html')

# Upload de documentos médicos
@app.route('/upload_documento', methods=['GET', 'POST'])
def upload_documento():
    if 'id_usuario' not in session or session['cargo'] != 'paciente':
        return redirect(url_for('login_paciente'))
    
    id_paciente = session['id_usuario']
    
    if request.method == 'POST':
        arquivo = request.files['arquivo']
        nome_arquivo = arquivo.filename
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO uploads (id_paciente, nome_arquivo) VALUES (?, ?)', (id_paciente, nome_arquivo))
            conn.commit()
        return 'Documento enviado com sucesso'
    
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome, cpf, convenio, cep, endereco, numero, complemento, telefone, data_nascimento, sexo, prontuario FROM pacientes WHERE id = ?', (id_paciente,))
        paciente = cursor.fetchone()
        cursor.execute('SELECT nome_arquivo FROM uploads WHERE id_paciente = ? AND enviado_pelo_medico = 1', (id_paciente,))
        documentos = cursor.fetchall()
    
    return render_template('upload_documento.html', paciente=paciente, documentos=documentos)

# Visualização de documentos médicos
@app.route('/visualizar_documentos')
def visualizar_documentos():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    id_paciente = session['id_usuario']
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome_arquivo FROM uploads WHERE id_paciente = ? AND enviado_pelo_medico = 0', (id_paciente,))
        documentos = cursor.fetchall()
    return render_template('visualizar_documentos.html', documentos=documentos)

# Visualização e edição de prontuário (apenas médico)
@app.route('/editar_prontuario', methods=['GET', 'POST'])
def editar_prontuario():
    if 'id_usuario' not in session or session['cargo'] != 'medico':
        return redirect(url_for('login'))
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        prontuario = request.form['prontuario']
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE pacientes SET prontuario = ? WHERE id = ?', (prontuario, id_paciente))
            conn.commit()
        return 'Prontuário atualizado com sucesso'
    return render_template('editar_prontuario.html')

# Página do médico para ver a lista de pacientes em espera e buscar prontuários
@app.route('/medico', methods=['GET', 'POST'])
def medico():
    if 'id_usuario' not in session or session['cargo'] != 'medico':
        return redirect(url_for('login'))
    
    id_usuario = session['id_usuario']
    with sqlite3.connect('usuarios.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome FROM usuarios WHERE id = ?', (id_usuario,))
        medico_nome = cursor.fetchone()[0]
    
    if request.method == 'POST':
        termo = request.form['termo']
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT c.id, p.nome, c.data, c.hora 
                              FROM consultas c 
                              JOIN pacientes p ON c.id_paciente = p.id 
                              WHERE c.chegada = 1 AND c.concluida = 0 AND (p.nome LIKE ? OR p.prontuario LIKE ?) 
                              ORDER BY c.data, c.hora''', ('%' + termo + '%', '%' + termo + '%'))
            consultas = cursor.fetchall()
    else:
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT c.id, p.nome, c.data, c.hora 
                              FROM consultas c 
                              JOIN pacientes p ON c.id_paciente = p.id 
                              WHERE c.chegada = 1 AND c.concluida = 0 
                              ORDER BY c.data, c.hora''')
            consultas = cursor.fetchall()
    
    return render_template('medico.html', consultas=consultas, medico_nome=medico_nome)



def calcular_idade(data_nascimento):
    hoje = datetime.today()
    nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d')
    anos = hoje.year - nascimento.year
    meses = hoje.month - nascimento.month
    dias = hoje.day - nascimento.day

    if dias < 0:
        meses -= 1
        dias += 30  # Aproximação para meses de 30 dias

    if meses < 0:
        anos -= 1
        meses += 12

    return anos, meses, dias

# Página para visualizar informações do paciente
@app.route('/paciente/<int:id_consulta>', methods=['GET', 'POST'])
def paciente_info(id_consulta):
    if 'id_usuario' not in session or session['cargo'] != 'medico':
        return redirect(url_for('login'))
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT p.id, p.nome, p.cpf, p.convenio, p.cep, p.endereco, p.numero, p.complemento, p.telefone, p.data_nascimento, p.sexo, p.prontuario 
                          FROM pacientes p 
                          JOIN consultas c ON p.id = c.id_paciente 
                          WHERE c.id = ?''', (id_consulta,))
        paciente = cursor.fetchone()
        cursor.execute('SELECT nome_arquivo FROM uploads WHERE id_paciente = ? AND enviado_pelo_medico = 1', (paciente[0],))
        documentos_medico = cursor.fetchall()
        cursor.execute('SELECT nome_arquivo FROM uploads WHERE id_paciente = ? AND enviado_pelo_medico = 0', (paciente[0],))
        documentos_paciente = cursor.fetchall()

    idade_anos, idade_meses, idade_dias = calcular_idade(paciente[9])

    if request.method == 'POST':
        novo_prontuario = request.form.get('novo_prontuario', '')
        if novo_prontuario:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            prontuario_atualizado = (paciente[11] or '') + f"\n-------------\n{timestamp}\n{novo_prontuario}-------"
            cursor.execute('UPDATE pacientes SET prontuario = ? WHERE id = ?', (prontuario_atualizado, paciente[0]))
            conn.commit()
        cursor.execute('UPDATE consultas SET concluida = 1 WHERE id = ?', (id_consulta,))
        conn.commit()
        return redirect(url_for('medico'))
    return render_template('paciente_info.html', paciente=paciente, documentos_medico=documentos_medico, documentos_paciente=documentos_paciente, idade_anos=idade_anos, idade_meses=idade_meses, idade_dias=idade_dias)

# Upload de documentos médicos pelo médico para o paciente
@app.route('/enviar_documento/<int:id_paciente>', methods=['POST'])
def enviar_documento(id_paciente):
    if 'id_usuario' not in session or session['cargo'] != 'medico':
        return redirect(url_for('login'))
    if request.method == 'POST':
        arquivo = request.files['arquivo']
        nome_arquivo = arquivo.filename
        # Certifique-se de que a pasta de uploads existe
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
        arquivo.save(caminho_arquivo)
        with sqlite3.connect('pacientes.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO uploads (id_paciente, nome_arquivo, enviado_pelo_medico) VALUES (?, ?, 1)', (id_paciente, nome_arquivo))
            conn.commit()
        return redirect(url_for('paciente_info', id_consulta=id_paciente))

# Página do paciente para visualizar documentos enviados pelo médico
@app.route('/documentos_medico')
def documentos_medico():
    if 'id_usuario' not in session or session['cargo'] != 'paciente':
        return redirect(url_for('login'))
    id_paciente = session['id_usuario']
    with sqlite3.connect('pacientes.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome_arquivo FROM uploads WHERE id_paciente = ? AND enviado_pelo_medico = 1', (id_paciente,))
        documentos = cursor.fetchall()
    return render_template('documentos_medico.html', documentos=documentos)

# Página da recepcionista
@app.route('/recepcionista')
def recepcionista():
    if 'id_usuario' not in session or session['cargo'] != 'recepcionista':
        return redirect(url_for('login'))
    return render_template('recepcionista.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port='5000')
