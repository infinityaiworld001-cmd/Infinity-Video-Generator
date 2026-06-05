from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageEnhance
import cv2
import numpy as np
import os
import time
import random
import math

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
VIDEO_FOLDER = "static/videos"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

history = []


def prepare_image(image_path, size=(1920, 1080)):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail(size, Image.LANCZOS)

    bg = Image.new("RGB", size, (5, 8, 22))
    x = (size[0] - img.width) // 2
    y = (size[1] - img.height) // 2
    bg.paste(img, (x, y))

    bg = ImageEnhance.Contrast(bg).enhance(1.12)
    bg = ImageEnhance.Sharpness(bg).enhance(1.30)
    bg = ImageEnhance.Color(bg).enhance(1.12)

    return np.array(bg)


def detect_effect(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (300, 300))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    red1 = cv2.inRange(hsv, (0, 60, 60), (10, 255, 255))
    red2 = cv2.inRange(hsv, (170, 60, 60), (180, 255, 255))
    orange = cv2.inRange(hsv, (10, 80, 80), (25, 255, 255))
    yellow = cv2.inRange(hsv, (25, 70, 70), (35, 255, 255))
    green = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
    blue = cv2.inRange(hsv, (90, 60, 50), (130, 255, 255))
    cyan = cv2.inRange(hsv, (80, 50, 50), (95, 255, 255))
    purple = cv2.inRange(hsv, (130, 50, 50), (165, 255, 255))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dark_score = np.sum(gray < 60)

    scores = {
        "fire": np.sum(red1) + np.sum(red2) + np.sum(orange),
        "lightning": np.sum(yellow),
        "wind": np.sum(green),
        "water": np.sum(blue),
        "ice": np.sum(cyan),
        "dark": np.sum(purple) + dark_score,
        "cinematic": 1
    }

    effect = max(scores, key=scores.get)

    return effect


def cinematic_bars(frame):
    h, w, _ = frame.shape
    bar = int(h * 0.075)
    frame[:bar, :] = 0
    frame[h - bar:, :] = 0
    return frame


def vignette(frame):
    h, w = frame.shape[:2]
    x_kernel = cv2.getGaussianKernel(w, w / 2)
    y_kernel = cv2.getGaussianKernel(h, h / 2)
    kernel = y_kernel * x_kernel.T
    mask = kernel / kernel.max()
    mask = np.dstack([mask] * 3)
    return np.uint8(frame * (0.50 + 0.50 * mask))


def glow(frame):
    blur = cv2.GaussianBlur(frame, (0, 0), 24)
    return cv2.addWeighted(frame, 0.86, blur, 0.30, 0)


def color_overlay(frame, color, strength):
    overlay = np.zeros_like(frame)
    overlay[:, :] = color
    return cv2.addWeighted(frame, 1 - strength, overlay, strength, 0)


def add_particles(frame, effect, progress):
    h, w, _ = frame.shape
    layer = np.zeros_like(frame)

    if effect == "fire":
        color = (255, 95, 0)
        for _ in range(160):
            x = random.randint(0, w)
            y = random.randint(int(h * 0.45), h)
            r = random.randint(2, 7)
            cv2.circle(layer, (x, y), r, color, -1)

    elif effect == "water":
        color = (0, 170, 255)
        for _ in range(130):
            x = random.randint(0, w)
            y = random.randint(0, h)
            cv2.line(layer, (x, y), (x + 12, y + 30), color, 1)

    elif effect == "ice":
        color = (170, 235, 255)
        for _ in range(130):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(1, 4)
            cv2.circle(layer, (x, y), r, color, -1)

    elif effect == "wind":
        color = (140, 255, 190)
        for _ in range(120):
            x = random.randint(0, w)
            y = random.randint(0, h)
            cv2.line(layer, (x, y), (x + 55, y - 10), color, 1)

    elif effect == "lightning":
        color = (255, 230, 40)
        for _ in range(60):
            x = random.randint(0, w)
            y = random.randint(0, h)
            x2 = x + random.randint(-25, 25)
            y2 = y + random.randint(25, 70)
            cv2.line(layer, (x, y), (x2, y2), color, 2)

    elif effect == "dark":
        color = (120, 0, 180)
        for _ in range(140):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(2, 6)
            cv2.circle(layer, (x, y), r, color, -1)

    else:
        color = (80, 160, 255)
        for _ in range(100):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(1, 4)
            cv2.circle(layer, (x, y), r, color, -1)

    return cv2.addWeighted(frame, 1, layer, 0.45, 0)


def apply_effect(frame, effect, progress):
    pulse = 0.09 + 0.04 * math.sin(progress * math.pi * 8)

    if effect == "fire":
        frame = color_overlay(frame, (255, 80, 0), pulse)
    elif effect == "water":
        frame = color_overlay(frame, (0, 150, 255), pulse)
    elif effect == "ice":
        frame = color_overlay(frame, (170, 235, 255), pulse)
    elif effect == "wind":
        frame = color_overlay(frame, (120, 255, 190), pulse)
    elif effect == "lightning":
        frame = color_overlay(frame, (255, 230, 40), pulse)
    elif effect == "dark":
        frame = color_overlay(frame, (100, 0, 150), pulse)
    else:
        frame = color_overlay(frame, (80, 160, 255), 0.06)

    frame = add_particles(frame, effect, progress)
    return frame


def create_video(image_path, output_path, duration=12, fps=30):
    detected_effect = detect_effect(image_path)

    base = prepare_image(image_path, (1920, 1080))
    h, w, _ = base.shape

    total_frames = duration * fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    for i in range(total_frames):
        progress = i / total_frames

        zoom = 1.0 + progress * 0.16
        new_w = int(w / zoom)
        new_h = int(h / zoom)

        pan_x = int(math.sin(progress * math.pi * 2) * 45)
        pan_y = int(math.cos(progress * math.pi * 2) * 25)

        x = int((w - new_w) / 2 + pan_x)
        y = int((h - new_h) / 2 + pan_y)

        x = max(0, min(x, w - new_w))
        y = max(0, min(y, h - new_h))

        cropped = base[y:y + new_h, x:x + new_w]
        frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_CUBIC)

        frame = glow(frame)
        frame = apply_effect(frame, detected_effect, progress)
        frame = vignette(frame)
        frame = cinematic_bars(frame)

        if progress < 0.06:
            alpha = progress / 0.06
            frame = np.uint8(frame * alpha)

        if progress > 0.94:
            alpha = (1 - progress) / 0.06
            frame = np.uint8(frame * alpha)

        video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    video.release()

    return detected_effect


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    image = request.files.get("image")
    prompt = request.form.get("prompt", "")

    if not image:
        return jsonify({"error": "Please upload image"}), 400

    filename = secure_filename(image.filename)
    unique = str(int(time.time()))

    image_path = os.path.join(UPLOAD_FOLDER, unique + "_" + filename)
    image.save(image_path)

    video_name = unique + "_infinity_auto_video.mp4"
    video_path = os.path.join(VIDEO_FOLDER, video_name)

    detected_effect = create_video(image_path, video_path)

    video_url = "/" + video_path

    item = {
        "prompt": prompt if prompt else "Auto detected cinematic anime animation",
        "effect": detected_effect,
        "video": video_url
    }

    history.insert(0, item)

    return jsonify({
        "video_url": video_url,
        "effect": detected_effect,
        "history": history
    })


if __name__ == "__main__":
    app.run()