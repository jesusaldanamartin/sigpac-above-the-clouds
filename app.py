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
import pandas as pd
from PIL import Image
from rasterio.enums import ColorInterp
import boto3 
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

S3_BUCKET = "sigpac-above-the-cloud"
S3_REGION = "us-east-1"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=S3_REGION,
)

COLORMAP_SIGPAC = {    
    0: (0, 0, 0, 0),          # Transparent
    1: (0, 50, 200 ),         # Red
    2: (250, 0, 0 ),          # Green
    3: (240, 150, 255 ),      # Blue
    4: (240, 150, 255 ),      # Yellow
    5: (240, 150, 255 ),      # Orange
    6: (240, 150, 255 ),      # Purple
    7: (250, 0, 0 ),          # Cyan
    8: (255, 187, 34 ),       # Pink
    9: (240, 150, 255 ),      # Gray
    10: (240, 150, 255 ),     # Teal
    11: (100, 140, 0 ),       # Chocolate
    12: (240, 150, 255 ),     # Indigo
    13: (240, 150, 255 ),     # Green Yellow
    14: (240, 150, 255 ),     # Khaki
    15: (250, 0, 0 ),         # Medium Slate Blue
    16: (255, 69, 0, 255),    # Orange Red
    17: (240, 150, 255 ),     # Sea Green
    18: (240, 150, 255 ),     # Light Sea Green
    19: (240, 150, 255 ),     # Tomato
    20: (255, 187, 34 ),      # Crimson
    21: (255, 187, 34 ),      # Navajo White
    22: (255, 255, 76 ),      # Lawn Green
    23: (240, 150, 255 ),     # Lemon Chiffon
    24: (240, 150, 255 ),     # Lime Green
    25: (240, 150, 255 ),     # Blue Violet
    26: (240, 150, 255 ),     # Gold
    27: (240, 150, 255 ),     # Dark Slate Blue
    28: (250, 0, 0 ),         # Medium Violet Red
    29: (250, 0, 0 )          # Orchid
}

COLORMAP_RED_GREEN = {
    0: (0, 0, 0, 0),      # Transparent
    1: (185, 56, 0 ),     # Red
    2: (3, 165, 0 ),      # Green
}

COLORMAP_CONF_MATRIX = {
    0: (0, 0, 0, 0),      # Transparent
    1: (2, 138, 0 ),      # Green
    2: (117, 117, 117),   # Gray
    3: (145, 44, 0 ),     # Red
    4: (42, 61, 188 )     # Blue

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
    try:
        raster_file = None
        shapefile = None

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

        metrics_path = os.path.join(output_folder, "metrics.csv")
        print(metrics_path)
        filtered_metrics = process_metrics_csv(metrics_path)
        print(filtered_metrics)
        # Apply custom styles and convert TIFs to PNGs
        styled_files = {}
        for tif_name in ["sigpac_file.tif", "red_green.tif", "conf_matrix.tif"]:
            input_tif = os.path.join(output_folder, tif_name)
            styled_tif = os.path.join(output_folder, f"styled_{tif_name}")
            output_png = os.path.join(output_folder, f"styled_{tif_name.replace('.tif', '.png')}")
            
            if "sigpac_file" in tif_name:
                apply_colormap(input_tif, styled_tif, COLORMAP_SIGPAC)
            elif "red_green" in tif_name:
                apply_colormap(input_tif, styled_tif, COLORMAP_RED_GREEN)
            elif "conf" in tif_name:
                apply_colormap(input_tif, styled_tif, COLORMAP_CONF_MATRIX)

            convert_tiff_to_png(styled_tif, output_png)
            styled_files[tif_name.replace('.tif', '')] = output_png

        print(f"Styled PNG files: {styled_files}")

        response_data = {
            "default_map": f"/output/{os.path.basename(styled_files['sigpac_file'])}",
            "true_false_map": f"/output/{os.path.basename(styled_files['red_green'])}",
            "conf_matrix_map": f"/output/{os.path.basename(styled_files['conf_matrix'])}",
            "metrics_table": filtered_metrics
        }

        print("Response Data:", response_data)

        return jsonify(response_data), 200
    except Exception as e:
        app.logger.error("Error during execution: %s", e)
    return jsonify({"error": str(e)}), 500

@app.route('/output-2/<filename>')
def get_processed_file(filename):
    processed_key = f"processed/{filename}"

    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=processed_key)
        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{processed_key}"
        return jsonify({"processed_file_url": file_url}), 200
    except:
        return jsonify({"error": "Processed file not found"}), 404

@app.route('/upload-2', methods=['POST'])
def upload_file_2():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        s3_client.upload_fileobj(file, S3_BUCKET, f"uploads/{filename}")

        return jsonify({"message": "File uploaded to S3", "filename": filename}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400

def satelite_images_sigpac(raster_path, shapefile_path, output_name, output_folder):

    mask_shp(shapefile_path, raster_path, output_folder + "masked_file.tif")
    save_output_file(shapefile_path, output_folder + "masked_file.tif", output_folder +"sigpac_file.tif")

    rows, cols, metadata, style, msk_band, sgc_band = read_needed_files(
        "../satelite_images_sigpac/json/crop_style_sheet.json", output_folder + "masked_file.tif", output_folder +"sigpac_file.tif")

    print("Binario")
    raster_comparison(rows, cols, metadata, output_folder + "red_green.tif", style, msk_band, sgc_band)
    print("CONF AMTRIX")
    raster_comparison_confmatrix(
        rows, cols, metadata, output_folder + "conf_matrix.tif", style, msk_band, sgc_band)

    print("start csv")
    create_dataframe_and_graphs(msk_band, sgc_band, output_folder + "metrics.csv")
    print("finish csv")
    # print(f"Processing {raster_path} and {shapefile_path} and {output_name} and {output_folder}")

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

def process_metrics_csv(csv_path):

    df = pd.read_csv(csv_path)

    df_filtered = df[(df.iloc[:, 1:] != 0).any(axis=1)]

    return df_filtered.to_dict(orient='records')

if __name__ == "__main__":
    app.run(debug=True)
