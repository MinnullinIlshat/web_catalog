import requests
from collections import deque
from io import BytesIO
from flask import current_app, render_template, redirect
from flask import request, flash
from http import HTTPStatus
from zipfile import ZipFile
from utils import csvfile_processing
from time import sleep
from fpdf import FPDF




NEWS = deque(maxlen=50)

def get_logs():
    '''возвращает последние n строк логов'''
    with open('logfile.log') as file:
        n = current_app.config.get('LINE_OF_LOGS')
        logs = file.readlines()
        return logs[-n:] if n < len(logs) else logs
    
def index():
    data = dict(requests.get('http://localhost:5000/links').json())
    
    if data['links'].get('first'):
        data['links']['first'] = data['links']['first'][-1]
    if data['links'].get('prev'):
        data['links']['prev'] = data['links']['prev'][-1]
    if data['links'].get('next'):
        data['links']['next'] = data['links']['next'][-1]
    data['links']['first'] = data['links']['first'][-1]
    data['links']['last'] = data['links']['last'][-1]
    
    pages = [i for i in range(1, data['pages'] + 1)]
    
    return render_template('table.html', pagination=data, page=1, order='desc', sort='id', pages=pages)

def table(sort='id', order='desc', page=1):
    order = 'asc' if order == 'desc' else 'desc'
    url = f'http://localhost:5000/links?sort={sort}&order={order}&page={page}'
    data = dict(requests.get(url).json())
    
    if data['links'].get('first'):
        data['links']['first'] = data['links']['first'][-1]
    if data['links'].get('prev'):
        data['links']['prev'] = data['links']['prev'][-1]
    if data['links'].get('next'):
        data['links']['next'] = data['links']['next'][-1]
    data['links']['first'] = data['links']['first'][-1]
    data['links']['last'] = data['links']['last'][-1]
    
    pages = [i for i in range(1, data['pages'] + 1)]
    
    return render_template('table.html', pagination=data, page=page, order=order, sort=sort, pages=pages)

def upload():
    if request.method == 'POST':
        link = request.form['link']
        jsn = {"link": link}
        
        response = requests.post('http://localhost:5000/links', json=jsn).json()
        return render_template('after_link_up.html', data=response)
    return render_template('upload.html')
    
def file_upload():
    file = request.files['file']
    
    if file.filename.rsplit('.', 1)[-1] != 'zip':
        flash("Файл должен иметь расширение'.zip'")
        return render_template('upload.html')
        
    file_io = BytesIO()
    file.save(file_io)
    
    with ZipFile(file_io) as zip_file: 
        # в архиве должен быть только один файл
        if len(zip_file.infolist()) != 1:
            flash('В zip архиве должен быть только один файл формата csv')
            return render_template('upload.html'), HTTPStatus.BAD_REQUEST
        
        csv_filename = zip_file.infolist()[0].filename
        if csv_filename.rsplit('.', 1)[-1] != 'csv':
            flash('Архив должен содержать один csv файл')
            return render_template('upload.html'), HTTPStatus.BAD_REQUEST
        
        with zip_file.open(csv_filename) as csv_file:
            links_count, errors, links_to_save = csvfile_processing(csv_file)
            
        data = {
            "total": links_count,
            "errors": errors,
            "success": links_to_save,
        }
        
        return render_template('file_upload_success.html', data=data)
    
def logs_page():
    return render_template('logging.html')

def news():
    with open('news.txt', 'r') as file:
        data = file.readlines()
    return render_template('news.html', data=data)
    
def stream():
    def generate():
        with open('logfile.log') as f:
            while True:
                lines = f.readlines()
                yield ''.join(lines[-20:])
                sleep(1)
    
    return current_app.response_class(generate(), mimetype="text/plain")


def pdf_download():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    with open('logfile.log') as file: 
        for line in file: 
            pdf.cell(200, 10, txt=line, ln=1, align='C')
    pdf.output('static/images/assets/logs.pdf')
    return redirect(f"/static/images/assets/logs.pdf")

def get_link(uuid):
    data = dict(requests.get(f'http://localhost:5000/links/{uuid}').json())
    
    if data.get('message'):
        flash('Ссылки с таким uuid не существует')
        return render_template('index.html')
    
    return render_template('link_page.html', data=data)