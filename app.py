import os
import sys

from flask import Flask, flash, request, redirect, url_for, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

sys.path.append("..")
from satelite_images_sigpac.src.utils import mask_shp ,reproject_raster, save_output_file
from satelite_images_sigpac.src.validation import read_needed_files, raster_comparison, raster_comparison_confmatrix, create_dataframe_and_graphs

import rasterio
import fiona
import logging
from PIL import Image
from rasterio.enums import ColorInterp

logger = logging.getLogger(__name__)

COLORMAP = {
    0: (0, 0, 0, 0),       # Transparent
    1: (255, 0, 0, 255),   # Red
    2: (0, 255, 0, 255),   # Green
    3: (0, 0, 255, 255),   # Blue
    4: (255, 255, 0, 255), # Yellow
    5: (255, 165, 0, 255), # Orange
    6: (128, 0, 128, 255), # Purple
    7: (0, 255, 255, 255), # Cyan
    8: (255, 192, 203, 255), # Pink
    9: (128, 128, 128, 255), # Gray
    10: (0, 128, 128, 255),  # Teal
    11: (210, 105, 30, 255), # Chocolate
    12: (75, 0, 130, 255),   # Indigo
    13: (173, 255, 47, 255), # Green Yellow
    14: (240, 230, 140, 255), # Khaki
    15: (123, 104, 238, 255), # Medium Slate Blue
    16: (255, 69, 0, 255),    # Orange Red
    17: (46, 139, 87, 255),   # Sea Green
    18: (32, 178, 170, 255),  # Light Sea Green
    19: (255, 99, 71, 255),   # Tomato
    20: (220, 20, 60, 255),   # Crimson
    21: (255, 222, 173, 255), # Navajo White
    22: (124, 252, 0, 255),   # Lawn Green
    23: (255, 250, 205, 255), # Lemon Chiffon
    24: (50, 205, 50, 255),   # Lime Green
    25: (138, 43, 226, 255),  # Blue Violet
    26: (255, 215, 0, 255),   # Gold
    27: (72, 61, 139, 255),   # Dark Slate Blue
    28: (199, 21, 133, 255),  # Medium Violet Red
    29: (218, 112, 214, 255)  # Orchid
}

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
   
@app.route('/execution', methods=['POST'])
def execute_process():
    raster_file = None
    shapefile = None

    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.tif') or filename.endswith('.tiff'):
                raster_file = filename
            elif filename.endswith('.shp'):
                shapefile = filename

        if not raster_file or not shapefile:
            return jsonify({"error": "Both raster and shapefile must be uploaded"}), 400

        raster_path = os.path.join(app.config['UPLOAD_FOLDER'], raster_file)
        shapefile_path = os.path.join(app.config['UPLOAD_FOLDER'], shapefile)
        output_folder = os.path.join(app.config['UPLOAD_FOLDER'], "output/")
        os.makedirs(output_folder, exist_ok=True)

        satelite_images_sigpac(
            raster_path=raster_path,
            shapefile_path=shapefile_path,
            output_name="above_the_clouds_sigpac",
            output_folder=output_folder
        )
        
        # Convert the processed file to PNG for rendering
        output_tif = os.path.join(output_folder, "sigpac_file.tif")
        styled_tif = os.path.join("/home/jesusaldanamartin/TFM/tests/output", "styled_sigpac_file.tif")
        apply_colormap(output_tif, styled_tif, COLORMAP)

        # Convert the styled TIFF to PNG
        output_png = os.path.join("/home/jesusaldanamartin/TFM/tests/output", "styled_sigpac_file.png")
        convert_tiff_to_png(styled_tif, output_png)
        
        output_png = os.path.join(output_folder, styled_tif)
        with rasterio.open(output_tif) as src:
            data = src.read(1)
            img = Image.fromarray(data)
            img.save(output_png)

        return jsonify({"png_url": f"/output/styled_sigpac_file.png"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def satelite_images_sigpac(raster_path, shapefile_path, output_name, output_folder):

    # print(shapefile_path)
    # print(raster_path)
    # print(output_folder + "masked_file.tif")

    mask_shp(shapefile_path, raster_path, output_folder + "masked_file.tif")
    save_output_file(shapefile_path, output_folder + "masked_file.tif", output_folder +"sigpac_file.tif")

    print(f"Processing {raster_path} and {shapefile_path} and {output_name} and {output_folder}")

    return {"raster": raster_path, "shapefile": shapefile_path}

@app.route('/output/<filename>')
def get_output_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], "output"), filename)

def apply_colormap(input_tif, output_tif, colormap):
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        meta = src.meta.copy()

        meta.update({
            "dtype": "uint8",
            "count": 1
        })

        with rasterio.open(output_tif, "w", **meta) as dst:
            dst.write(data.astype("uint8"), 1)
            dst.write_colormap(1, colormap)  # Apply the colormap
            dst.colorinterp = [ColorInterp.palette]

def convert_tiff_to_png(tif_path, png_path):
    with rasterio.open(tif_path) as src:
        data = src.read(1)
        colormap = src.colormap(1)

        # Convert the colormap to a PIL-compatible palette
        palette = []
        for key in sorted(colormap.keys()):
            palette.extend(colormap[key][:3])

        img = Image.fromarray(data.astype("uint8"), mode="P")
        img.putpalette(palette)
        img.save(png_path)

if __name__ == "__main__":
    app.run(debug=True)
