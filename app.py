from flask import Flask, render_template
from flask import request, session
import sys
import threading
import cv2
import boto3
import requests
import base64
import numpy as np
import os

app = Flask(__name__, static_url_path='', static_folder='static/picojs')
app.secret_key = str(os.urandom(16))
rekognition = boto3.client("rekognition", "us-west-2")


@app.route('/')
def main_page():
    session["is_processing"] = False
    return render_template("index.html")


@app.route('/people_detected', methods=['POST'])
def process_people_detected():
    people_detected = request.data.decode("utf-8")
    session['people_detected'] = people_detected
    # sys.stderr.write(people_detected + '\n\n')
    return people_detected


@app.route('/people_detected', methods=['GET'])
def return_people_detected():
    return session.get('people_detected', "None")


@app.route('/detect', methods=['POST'])
def detect_faces():
    # Get raw request data, remove header, and convert to image
    encoded_data = request.get_data()[22:]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Send image to AWS Rekognition and process result
    output = ""
    try:
        response = rekognition.search_faces_by_image(
            Image={
                "Bytes": bytearray(cv2.imencode('.png', img)[1])
            },
            CollectionId="arc-face-rec-test",
            FaceMatchThreshold=80,
        )

        for resp in response['FaceMatches']:
            face = resp['Face']
            output += "Face Detected: " + \
                face['ExternalImageId'] + ", Confidence: " + \
                str(face['Confidence']) + '<br>'
    except rekognition.exceptions.InvalidParameterException:
        output = "None"

    # sys.stderr.write(output + '\n\n')
    session['people_detected'] = output
    return output


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host="0.0.0.0")
