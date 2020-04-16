from flask import Flask, render_template      
from flask import request
import sys
import threading
import cv2
import boto3
import requests
import base64
import numpy as np

app = Flask(__name__, static_url_path='', static_folder='static/picojs')

@app.route('/')
def main_page():
    return render_template("index.html")

person = 'None'
@app.route('/person', methods=['POST'])
def process_person():
    global person
    person = request.data.decode("utf-8")
    # sys.stderr.write(person + '\n\n')
    return person

@app.route('/person', methods=['GET'])
def return_person():
    return person

rekognition = boto3.client("rekognition", "us-west-2")
processing = False

def process_image(data):
    global person
    global processing
    encoded_data = data[22:]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    output = ""
    response = rekognition.search_faces_by_image(
        Image={
            "Bytes": bytearray(cv2.imencode('.png', img)[1])
        },
        CollectionId="arc-face-rec-test",
        FaceMatchThreshold=80,
    )

    for face in response['FaceMatches']:
        face = response['FaceMatches'][0]['Face']
        output += "Face Detected: " + face['ExternalImageId'] + ", Confidence: " + str(face['Confidence']) + '<br>'
    person = output
    # sys.stderr.write(output + '\n\n')
    processing = False
    return output

@app.route('/detect', methods=['POST'])
def detect_faces():
    global processing
    if not processing:
        processing=True
        # print("Starting recognizeFace thread")
        th = threading.Thread(target=process_image, args=[request.get_data()])
        th.start()
    return "Success"

if __name__ == '__main__':
    app.run(debug=True, threaded=False, host="0.0.0.0")