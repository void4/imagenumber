from time import sleep
import requests

import numpy as np
from PIL import Image

NAME = "anon"

HOST = "randomcorrelations.com"
URL = f"https://{HOST}/"

targets = requests.get(URL).json()["targets"]

target = targets[0]
print("target:", target)

def send(arr):
	img = Image.fromarray(arr)
	img.save("image.png")

	data = {"name": NAME, "target": target["name"]}
	files = {"image": open("image.png", "rb")}

	response = requests.post(URL, data=data, files=files)
	j = response.json()
	if j["status"] == "ok":
		return j["diff"]
	else:
		print(j)
		raise Exception(str(j))

# Initialize black image
arr = np.zeros(target["shape"], dtype=np.uint8)

h,w,c = target["shape"]

x = 0
y = 0

while True:

	# modify arr here

	# Example: change every pixel to black or white individually
	# very slow, requires many attempts, and will therefore yield a bad score

	arr[y][x] = [0,0,0]
	blackdiff = send(arr)

	arr[y][x] = [255,255,255]
	whitediff = send(arr)
	print(whitediff, blackdiff)

	if whitediff < blackdiff:
		arr[y][x] = [255,255,255]
		diff = whitediff
	else:
		arr[y][x] = [0,0,0]
		diff = blackdiff

	if x == w-1:
		x = 0
		y += 1
	else:
		x += 1

	if y == h-1:
		break

	print(x, y, "average difference per pixel:", diff)

	# not too fast please
	sleep(0.01)
