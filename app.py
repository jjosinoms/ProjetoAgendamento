from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
import json, os, io, csv

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

ARQUIVO = 'agendamentos.json'

@app.template_filter('datetime_format')
def datetime_format(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M')
        except ValueError:
            return value
    return value.strftime('%d/%m/%Y %H:%M')

def carregar_agendamentos():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, 'r') as f:
            return json.load(f)
    return []

def salvar_agendamentos(agendamentos):
    with open(ARQUIVO, 'w') as f:
        json.dump(agendamentos, f, indent=4)

@app.route('/')
def index():
    agendamentos = sorted(carregar_agendamentos(), key=lambda x: x['data_hora'])
    for i, ag in enumerate(agendamentos):
        ag['id'] = i + 1
    return render_template('index.html', agendamentos=agendamentos)

@app.route('/agendar', methods=['POST'])
def agendar():
    nome = request.form['nome']
    data_hora = request.form['data_hora']
    cpf = request.form['cpf']
    email = request.form['email']
    endereco = request.form['endereco']
    observacao = request.form.get('observacao', '')
    status = request.form.get('status', 'Pendente')

    try:
        dt = datetime.strptime(data_hora, '%Y-%m-%dT%H:%M')
        data_formatada = dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        flash('Data/hora inválida.', 'error')
        return redirect(url_for('index'))

    agendamentos = carregar_agendamentos()

    for ag in agendamentos:
        if ag['data_hora'] == data_formatada:
            flash('Horário já agendado. Escolha outro horário.', 'error')
            return redirect(url_for('index'))

    agendamentos.append({
        'id': len(agendamentos) + 1,
        'nome': nome,
        'data_hora': data_formatada,
        'cpf': cpf,
        'email': email,
        'endereco': endereco,
        'observacao': observacao,
        'status': status,
        'historico': [f'Criado em {datetime.now().strftime("%d/%m/%Y %H:%M")}' ]
    })
    salvar_agendamentos(agendamentos)
    flash('Agendamento feito com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    agendamentos = carregar_agendamentos()
    agendamento = agendamentos[id-1]

    if request.method == 'POST':
        agendamento['nome'] = request.form['nome']
        data_hora = request.form['data_hora']

        try:
            dt = datetime.strptime(data_hora, '%Y-%m-%dT%H:%M')
            agendamento['data_hora'] = dt.strftime('%Y-%m-%d %H:%M')
        except ValueError:
            flash('Data/hora inválida.', 'error')
            return redirect(url_for('index'))

        agendamento['cpf'] = request.form['cpf']
        agendamento['email'] = request.form['email']
        agendamento['endereco'] = request.form['endereco']
        agendamento['observacao'] = request.form.get('observacao', '')
        agendamento['status'] = request.form.get('status', 'Pendente')
        agendamento.setdefault('historico', []).append(f'Editado em {datetime.now().strftime("%d/%m/%Y %H:%M")}')

        salvar_agendamentos(agendamentos)
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('editar.html', agendamento=agendamento)

@app.route('/excluir/<int:id>', methods=['GET'])
def excluir(id):
    agendamentos = carregar_agendamentos()
    agendamentos.pop(id-1)
    salvar_agendamentos(agendamentos)
    flash('Agendamento excluído com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/exportar')
def exportar():
    agendamentos = carregar_agendamentos()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'Data/Hora', 'CPF', 'Email', 'Endereço', 'Observação', 'Status'])
    for ag in agendamentos:
        writer.writerow([
            ag['nome'], ag['data_hora'], ag['cpf'], ag['email'],
            ag['endereco'], ag['observacao'], ag.get('status', 'Pendente')
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.read().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='agendamentos.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
