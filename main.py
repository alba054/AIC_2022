from flask import Flask, request
import json

from utils_api import get_database
from detect import load_image_and_detect


app = Flask(__name__)
clientDB = get_database()

# @app.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"

@app.route("/animals/<ids>")
def getAnimalById(ids):
  id_list = ids.split("-")
  id_list = set(id_list)
  animalCollection = clientDB["animals"]
  response = []
  for id in id_list:  
    animal = animalCollection.find({"id" : id})
    animal = list(animal)[0]
    del animal["_id"]
    response.append(animal)

  return response

@app.route("/detect", methods=['POST'])
def detect():
  body = json.loads(request.data)
  base64Image = body['image']
  filters = body['filters']


  return load_image_and_detect(base64Image, filters)

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)
  
