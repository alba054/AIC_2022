import uuid
from flask import Flask, request, make_response
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

import json
import bcrypt
import base64
import uuid

from utils_api import get_database, upload_blob
'''
for production
'''
# from detect import load_image_and_detect


app = Flask(__name__)
clientDB = get_database()
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)

BUCKET_NAME = "wicoversity_bucket"


@app.route("/register", methods=["POST"])
def registerHandler():
  payload = json.loads(request.data)
  email = payload["email"]
  password = payload["password"]
  # print(password)
  password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

  userCollection = clientDB["users"]
  
  
  try:
    newUser = userCollection.insert_one({
      "email" : email,
      "password" : password
    })

    return make_response({
      "result" : {
        "message" : "success",
      }
    }, 201)
  except:
    return make_response({
      "result" : {
        "message" : "failed"
      }
    }, 500)

@app.route("/login", methods=["POST"])
def loginHandler():
  username = request.headers["username"]
  password = request.headers["password"]
  userCollection = clientDB["users"]

  try:
    user = userCollection.find_one({ "email" : username})
    isPasswordCorrect = bcrypt.checkpw(password.encode(), user["password"])
    # print(isPasswordCorrect)

    if isPasswordCorrect:
      accessToken = create_access_token(identity={"username" : username, "role" : "user"})
      return {"result" : {
        "access_token" : accessToken
      }}
  except:
    return make_response({"result" : {
      "message" : "user's not found"
    }}, 404)

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

# '''
# for production
# '''
# @app.route("/detect", methods=['POST'])
# def detect():
#   filters = None
#   body = json.loads(request.data)
#   base64Image = body['image']
#   try:
#     filters = body['filters']
#   except:
#     pass

#   return load_image_and_detect(base64Image, filters)

@app.route("/upload-file", methods=["POST"])
@jwt_required()
def uploadImageHandler():
  payload = json.loads(request.data)
  img = payload["uploaded_image"]
  title = str(uuid.uuid4())
  filename = f"img/{title}.png"
  
  # try:
  with open(filename, "wb") as imgFile:
    img = base64.b64decode(img)
    imgFile.write(img)
  
  upload_blob(BUCKET_NAME, filename, title)
  
  return make_response({
    "result" : {
      "message" : "successfully uploaded image"
    }
  }, 201)
  # except:
  #   return make_response({
  #     "result" : {
  #       "message" : "failed"
  #     }
  #   }, 500)
  
  # upload_blob(BUCKET_NAME, )


if __name__ == "__main__":
  app.run("0.0.0.0", 8000, debug=True)
  
