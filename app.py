import os
import uuid
import json
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from db import init_db, save_certificate, get_certificate

# Initialize DB
init_db()

app = Flask(__name__)
app.secret_key = "your-secret-key"

TEMPLATE_FOLDER = "cert_templates"
GENERATED_FOLDER = "static/certificates"
POSITION_FOLDER = "positions"

os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(POSITION_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    template_name = session.get('template_name')
    template_exists = template_name is not None and os.path.exists(f"static/latest_template.png")
    return render_template('dashboard.html', template_exists=template_exists, template_name=template_name)


@app.route('/upload-template', methods=['POST'])
def upload_template():
    file = request.files.get('template')
    if not file:
        return "No file uploaded", 400

    filename = os.path.splitext(file.filename)[0]  # no .png
    unique_filename = f"{filename}_{uuid.uuid4().hex[:6]}"
    path = os.path.join(TEMPLATE_FOLDER, unique_filename + ".png")
    file.save(path)

    # Save a preview for drag UI
    file.stream.seek(0)
    with open("static/latest_template.png", "wb") as f:
        f.write(file.read())

    # Save template name in session
    session['template_name'] = unique_filename

    return redirect(url_for('dashboard'))


@app.route('/save-positions', methods=['POST'])
def save_positions():
    data = request.json
    template_name = session.get('template_name')
    if not template_name:
        return jsonify({'error': 'No template name found'}), 400

    path = os.path.join(POSITION_FOLDER, f"{template_name}.json")
    with open(path, 'w') as f:
        json.dump(data, f)
    return jsonify({'status': 'ok'})


@app.route('/generate-certificates', methods=['POST'])
def generate_certificates():
    template_name = session.get('template_name')
    if not template_name:
        return "Please upload a template first.", 400

    csv_file = request.files.get('csv')
    if not csv_file:
        return "No CSV file uploaded", 400

    df = pd.read_csv(csv_file)

    template_path = os.path.join(TEMPLATE_FOLDER, f"{template_name}.png")
    position_path = os.path.join(POSITION_FOLDER, f"{template_name}.json")

    if not os.path.exists(template_path) or not os.path.exists(position_path):
        return "Missing template or positions.", 400

    with open(position_path, "r") as f:
        positions = json.load(f)

    for _, row in df.iterrows():
        name = row['Name']
        event = row['Event']
        cert_id = str(uuid.uuid4())[:8]
        date_str = datetime.date.today().strftime("%Y-%m-%d")

        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()

        draw.text((positions['name']['x'], positions['name']['y']), name, font=font, fill="black")
        draw.text((positions['event']['x'], positions['event']['y']), event, font=font, fill="black")
        draw.text((positions['date']['x'], positions['date']['y']), date_str, font=font, fill="black")

        qr = qrcode.make(f"http://localhost:5000/verify/{cert_id}")
        qr_img = qr.resize((100, 100))
        img.paste(qr_img, (positions['qr']['x'], positions['qr']['y']))

        output_filename = f"{name}_{cert_id}.png"
        output_path = os.path.join(GENERATED_FOLDER, output_filename)
        img.save(output_path)

        save_certificate(cert_id, name, event, output_path, date_str)

    return "Certificates generated successfully!"


@app.route('/verify/<cert_id>')
def verify(cert_id):
    data = get_certificate(cert_id)
    if data:
        return render_template('verify.html', cert=data)
    else:
        return "Certificate Not Found", 404


if __name__ == '__main__':
    app.run(debug=True)
