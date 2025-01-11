import os
from flask import Flask, flash, request, redirect, url_for, render_template, jsonify
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/home/jesusaldanamartin/TFM/tests/'
ALLOWED_EXTENSIONS = {'tif', 'tiff', 'shp', 'png'}

app = Flask(__name__, static_folder='static')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(f"Uploaded file: {file.filename}")
            print(f"Saved file: {os.path.join(app.config['UPLOAD_FOLDER'], filename)}")

            # Return the file name to the front end
            return jsonify({"filename": filename}), 200
        else:
            return jsonify({"error": "File type not allowed"}), 400

    return render_template('home.html')


# @app.route("/upload", methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return "No file part in the request", 400
#     file = request.files['file']
#     if file.filename == '':
#         return "No file selected", 400
#     return "File uploaded successfully", 200

if __name__ == "__main__":
    app.run(debug=True)
