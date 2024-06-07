import json
import os
from flask import Flask, jsonify, request, send_from_directory
from scripts.find_way import find_way
from scripts.edit_json import update_caption, create_mask
from flask_cors import CORS
from scripts.predict import plot_predictions
from scripts.mask_to_json import (
    mask_to_json,
    size_convert,
    remove_colored_pixels,
    to_mask,
)

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}}, supports_credentials=True)


@app.route("/editstore/<buildingname>", methods=["POST"])
def edit_store(buildingname):
    # my_res = Flask.Response("차단되지롱")
    # my_res.headers["Access-Control-Allow-Origin"] = "*"
    data = request.json
    update_caption(data, buildingname)
    create_mask(buildingname)
    return "json, mask update 완료"


@app.route("/findway", methods=["POST"])
def run_way():
    data = request.json
    find_way(
        data["building_name"],
        data["startFloor"],
        data["startId"],
        data["endFloor"],
        data["endId"],
        data["elev"],
    )
    return "길 탐색(find_way) 완료!!"


@app.route("/mask/<filename>")
def get_mask(filename):
    img_path = f"result/{filename[:-3]}/mask"
    fname = f"{filename}.png"
    if os.path.exists(os.path.join(img_path, fname)):
        return send_from_directory(img_path, fname)
    else:
        return send_from_directory("sources", "404err.png")


@app.route("/healthcheck")
def healthcheck():
    return "ok"


@app.route("/way/<filename>")
def get_way(filename):
    img_path = f"result/{filename[:-3]}/way"
    fname = f"{filename}.png"
    if os.path.exists(os.path.join(img_path, fname)):
        return send_from_directory(img_path, fname)
    else:
        return send_from_directory("sources", "404err.png")


@app.route("/source/<filename>")
def get_source(filename):
    img_path = f"sources/{filename[:-3]}/images"
    fname = f"{filename}.png"
    if os.path.exists(os.path.join(img_path, fname)):
        return send_from_directory(img_path, fname)
    else:
        return send_from_directory("sources", "404err.png")


@app.route("/loading")
def loading():
    img_path = "sources"
    fname = "loading.png"
    return send_from_directory(img_path, fname)


@app.route("/json/<filename>")
def filtered_json(filename):
    img_path = f"result/{filename[:-3]}/data"
    fname = f"{filename}.json"
    if not os.path.exists(os.path.join(img_path, fname)):
        return jsonify(
            [{"id": 404, "caption": "404Err", "move_up": 404, "move_down": 404}]
        )
    with open(os.path.join(img_path, fname), "r") as file:
        data = json.load(file)
    filtered_data = []
    for item in data:
        filtered_data.append(
            {
                "id": item["id"],
                "caption": item["caption"],
                "move_up": item["move_up"],
                "move_down": item["move_down"],
            }
        )
    return jsonify(filtered_data)


@app.route("/dir/<buildingname>")
def list_directory(buildingname):
    directory_path = f"result/{buildingname}/data"
    try:
        file_list = os.listdir(directory_path)
        for i in range(len(file_list)):
            file_list[i] = file_list[i][-7:-5]
        return jsonify(file_list)
    except FileNotFoundError:
        return jsonify({"error": "Directory not found"}), 404


@app.route("/dirimg/<buildingname>")
def get_filelist(buildingname):
    directory_path = f"sources/{buildingname}/images"
    try:
        file_list = os.listdir(directory_path)
        for i in range(len(file_list)):
            file_list[i] = file_list[i][-6:-4]
        return jsonify(file_list)
    except FileNotFoundError:
        return jsonify({"error": "Directory not found"}), 404


@app.route("/buildinglist")
def building_list():
    directory_path = "result"
    try:
        file_list = os.listdir(directory_path)
        return jsonify(file_list)
    except FileNotFoundError:
        return jsonify({"error": "Directory not found"}), 404


@app.route("/upload/<filename>", methods=["POST"])
def upload_file(filename):
    UPLOAD_FOLDER = f"./sources/{filename[:-3]}/images"
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    if file:
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], f"{filename}.png"))
        remove_colored_pixels(filename)
        print("remove_colored_pixels complete")
        plot_predictions(filename)
        print("plot_predictions complete")
        size_convert(filename)
        print("size_convert complete")
        mask_to_json(filename)
        print("mask_to_json complete")
        to_mask(filename)
        print("create mask complete")
        return "File successfully uploaded"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
