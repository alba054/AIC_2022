from pkgutil import get_data
from flask import Flask

from utils import get_database

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
  response = {}
  for id in id_list:  
    animal = animalCollection.find({"id" : id})
    animal = list(animal)[0]
    del animal["_id"]
    response[id] = animal

  return response

if __name__ == "__main__":
  app.run(debug=True)