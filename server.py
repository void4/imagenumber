import os
from math import log
from glob import glob
from time import time
from copy import deepcopy

import numpy as np
from PIL import Image
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

paths = glob(f"targets/**/target.png")

targets = [{"name": os.path.split(os.path.split(path)[-2])[-1], "shape": np.array(Image.open(path)).shape} for path in paths]

def compare(path, target):

	if target not in paths:
		return {"status": "error", "errortext": f"Invalid target"}

	target_img = Image.open(target)
	original = np.array(target_img)

	img = Image.open(path)
	reconstructed = np.array(img)

	if original.shape != reconstructed.shape:
		return {"status": "error", "errortext": f"Invalid image shape (need {original.shape})"}

	diff = np.sum(abs(reconstructed-original))/np.prod(original.shape)
	print("error per pixel:", diff)
	return {"status":"ok", "diff": diff}

@app.route("/", methods=["GET"])
def r_index_get():

	fulltargets = deepcopy(targets)

	for target in fulltargets:
		target["scoreboard"] = []
		for userpath in glob(f"targets/{target['name']}/attempts/*"):
			for run in glob(userpath+"/*/"):
				userattempts = glob(os.path.join(run, "*.png"))
				if len(userattempts):
					latest_file = max(userattempts, key=os.path.getctime)
					latestdiff = compare(latest_file, f"targets/{target['name']}/target.png")["diff"]
					#score = latestdiff*log(2+len(userattempts)+len(userattempts))
					# "score": score,
					target["scoreboard"].append({"name": os.path.split(userpath)[-1], "run": run.split("/")[-2], "latestdiff": latestdiff, "attempts": len(userattempts)})

		print(target)
		target["scoreboard"] = list(sorted(target["scoreboard"], key=lambda sc: sc["latestdiff"]))#score

	return jsonify({"status": "ok", "targets": fulltargets})

@app.route("/", methods=["POST"])
def r_index_post():
	if "image" not in request.files:
		return jsonify({"status": "error", "errortext": "Missing file 'image'"})
	if len(request.files) > 1:
		return jsonify({"status": "error", "errortext": "Too many images (just upload one)"})

	f = request.files["image"]

	if not f.filename.endswith(".png"):
		return jsonify({"status": "error", "errortext": "Invalid filetype, not .png"})

	target = secure_filename(str(request.values.get("target", "1")))
	print(request.values.get("target"))

	if target not in [t["name"] for t in targets]:
		return jsonify({"status": "error", "errortext": "Invalid target, must be one of", "targets": targets})

	name = secure_filename(request.values.get("name", "anon"))
	namepath = os.path.join("targets", target, "attempts", name)

	os.makedirs(namepath, exist_ok=True)

	if name != "anon":

		password = request.values.get("password")
		passwordpath = os.path.join(namepath, "password")

		if os.path.exists(passwordpath):
			with open(passwordpath) as pwfile:
				if pwfile.read() != password:
					return jsonify({"status": "error", "errortext": "Invalid password"})

		elif password is not None:
			with open(passwordpath, "w+") as pwfile:
				pwfile.write(password)

	runname = secure_filename(request.values.get("run", "test"))

	runpath = os.path.join(namepath, runname)
	os.makedirs(runpath, exist_ok=True)

	attemptpath = os.path.join(runpath, str(int(time()*1000))+".png")

	f.save(attemptpath)
	#print(f, dir(f))

	return jsonify(compare(attemptpath, os.path.join("targets", target, "target.png")))

HOST = "0.0.0.0"
PORT = 1236
DEBUG = os.getcwd().startswith("/home/zero")

app.run(HOST, PORT, debug=DEBUG)
