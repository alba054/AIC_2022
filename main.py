from flask import Flask, request
import json

from utils_api import get_database
'''
for production
'''
from detect import load_image_and_detect


app = Flask(__name__)
clientDB = get_database()

@app.route("/animals/<ids>")
def getAnimalById(ids):
  id_list = ids.split("-")
  id_list = set(id_list)
  animalCollection = clientDB["animals"]
  response = []
  try:
    for id in id_list:
        animal = animalCollection.find({"id" : id})
        animal = list(animal)
        del animal["_id"]
        response.append(animal)
  except:
    return { "results" : [] }

  return { "results" : response }

@app.route("/locations/<id>")
def getLocationByID(id):
  locationCollection = clientDB["locations"]
  animalsCollection = clientDB["animals"]
  try:
    location = locationCollection.find({"id" : int(id)})
    location = list(location)[0]
    del location["_id"]
    
    filtered_animals = animalsCollection.find({"zones" : {"$in" : [int(id)] } })
    animals = []

    for animal in filtered_animals:
      animals.append(animal['id'])

    return { "result" : {
      "destination" : location,
      "animals" : animals
      } 
    }
  except:
    return { "result" : {} }

'''
for production
'''
@app.route("/detect", methods=['POST'])
def detect():
  filters = None
  body = json.loads(request.data)
  base64Image = body['image']
  try:
    filters = body['filters']
  except:
    pass

  return load_image_and_detect(base64Image, filters)

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)
  
