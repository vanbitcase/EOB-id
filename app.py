import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import json
import webbrowser

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['SECRET_KEY'] = 'supersecretkey'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

data_file = 'data.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_data():
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        eob_id = request.form['eob_id']
        applicant_names = request.form.get('applicant_name', '').split(',')  # Default to empty list if not provided
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_id + '.pdf')
            file.save(save_path)

            # Get the file's modification date
            file_date = datetime.fromtimestamp(os.path.getmtime(save_path)).strftime('%Y-%m-%d')

            data = load_data()
            data[unique_id] = {
                'unique_id': unique_id,
                'date': file_date,  # Use file modification date
                'eob_id': eob_id,
                'filename': filename,
                'path': save_path,
                'applicant_names': [name.strip() for name in applicant_names]  # Ensure it's always a list
            }
            save_data(data)

            flash(f'File uploaded successfully with unique ID: {unique_id}')
            return redirect(url_for('upload_file'))

    return render_template('index.html')



@app.route('/search', methods=['GET', 'POST'])
def search_file():
    if request.method == 'POST':
        search_date = request.form.get('date')
        search_eob_id = request.form.get('eob_id')
        search_applicant_name = request.form.get('applicant_name', '').strip()

        data = load_data()
        results = []

        for unique_id, entry in data.items():
            # Ensure 'applicant_names' exists in the entry
            applicant_names = entry.get('applicant_names', [])

            # Check for matches
            name_match = any(search_applicant_name.lower() in name.lower() for name in applicant_names)
            if (search_eob_id and entry.get('eob_id') == search_eob_id) or \
               (search_date and entry.get('date') == search_date) or \
               (search_applicant_name and name_match):
                results.append({**entry, 'unique_id': unique_id})

        return render_template('search.html', results=results)

    return render_template('search.html', results=None)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/view_pdf/<unique_id>')
def view_pdf(unique_id):
    data = load_data()
    entry = data.get(unique_id)
    if entry:
        file_url = f'file://{os.path.abspath(entry["path"])}'
        chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
        webbrowser.get(chrome_path).open(file_url)
        return f'Opening PDF: {entry["filename"]}'
    else:
        return 'File not found', 404

if __name__ == '__main__':
    app.run(debug=True)
