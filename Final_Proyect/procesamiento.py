from flask import Flask, request, jsonify
import base64
from io import BytesIO
from PIL import Image
import numpy as np

app = Flask(__name__)

@app.route('/process_frame', methods=['POST'])
def process_frame():

    data = request.get_json()
    print("Frame recibido!")  # Mensaje de depuración
    image_data = data['image'].split(',')[1]
    print(f"Imagen base64: {image_data[:50]}...")  # Muestra parte del frame en la terminal

    image = Image.open(BytesIO(base64.b64decode(image_data)))
    
    # Simular el procesamiento del modelo
    resultado = {"emocion": "felicidad"}

    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True)
