import uuid
from flask import Flask, request, make_response
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import decode_token

import json
import bcrypt
import base64
import uuid
import os
import datetime

from utils_api import get_database, upload_blob
'''
for production
'''
from detect import load_image_and_detect


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
  name = payload["name"]
  # print(password)
  password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

  userCollection = clientDB["users"]
  user = userCollection.find_one({"email" : email})
  if user:
    return make_response({
      "result" : {
        "message" : "user is defined"
      }
    }, 400)
  
  try:
    newUser = userCollection.insert_one({
      "email" : email,
      "password" : password,
      "name" : name
    })

    return make_response({
      "result" : {
        "message" : "success",
      }
    }, 201)
  except Exception as e:
    print(e)
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
  locationCollection = clientDB["locations"]
  location = None
  name = None
  user = userCollection.find_one({ "email" : username})
  print(user.keys())
  if "location" in user.keys():
    print(user["location"])
    location = locationCollection.find_one({"id" : int(user["location"])})
  if "name" in user.keys():
      name = user["name"]
  
  isPasswordCorrect = bcrypt.checkpw(password.encode(), user["password"])
    # print(isPasswordCorrect)
  print(user)
  if isPasswordCorrect:
      accessToken = create_access_token(identity={"username" : username, "role" : "user", "name":name})
      return {"result" : {
        "access_token" : accessToken
      }}

@app.route("/animals/<ids>")
def getAnimalById(ids):
  id_list = ids.split("-")
  id_list = set(id_list)
  animalCollection = clientDB["animals"]
  response = []
  try:
    for id in id_list:
        animal = animalCollection.find({"id" : id})
        animal = list(animal)[0]
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

@app.route("/update-location", methods=["POST"])
@jwt_required()
def update_location():
  auth = request.headers["Authorization"]
  access_token = auth.split(" ")[1]
  decoded = decode_token(access_token)
  body = json.loads(request.data)
  location = body["location_id"]

  userCollection = clientDB["users"]
  userCollection.update_one({"email" : decoded["sub"]["username"]}, {"$set" : {"location" : location}})

  return make_response({"result" : {"message" : "ok"}}, 200)

'''
for production
'''
@app.route("/detect", methods=['POST'])
@jwt_required(optional=True)
def detect():
  auth = None
  if "Authorization" in request.headers.keys():
    auth = request.headers["Authorization"]
  filters = None
  body = json.loads(request.data)
  base64Image = body['image']
  try:
    filters = body['filters']
  except:
    pass

  access_token = None
  result = load_image_and_detect(base64Image, filters)
  if auth:
    access_token = auth.split(" ")[1]
    decoded = decode_token(access_token)
    historiesCollection = clientDB["histories"]
    current_time = datetime.datetime.now()
    current_time = f"{current_time.year}-{current_time.month}-{current_time.day}"
    historiesCollection.insert_one({
      "username" : decoded["sub"]["username"],
      "image" : base64Image,
      "detected_at" : current_time,
      "location" : decoded["sub"]["location"],
      "name" : decoded["sub"]["name"],
      "detection_result" : result
    })

  
  return result

@app.route("/histories")
@jwt_required()
def getDetectionHistory():
  auth = request.headers["Authorization"]
  access_token = auth.split(" ")[1]
  decoded = decode_token(access_token)
  historiesCollection = clientDB["histories"]
  histories = historiesCollection.find({"username" : decoded["sub"]["username"]})
  histories = list(histories)
  results = []
  for hist in histories:
      results.append({"username" : hist["username"], "image" : hist["image"], "detected_at" : hist["detected_at"], "location" : hist["location"], "name" : hist["name"], "detection_result" : json.loads(hist["detection_result"])})
  return make_response({"result":{"histories" : results}}, 200)



@app.route("/user")
@jwt_required()
def getUserProfile():
  auth = request.headers["Authorization"]
  access_token = auth.split(" ")[1]
  decoded = decode_token(access_token)

  location = None
  name = None
  user = clientDB["users"].find_one({"email" : decoded["sub"]["username"]})
  if "location" in user.keys():
    location = user["location"]
  if "name" in user.keys():
    name = user["name"]
  
  return make_response({
    "result" : {
      "username" : decoded["sub"]["username"],
      "location" : location,
      "name" : name
    }
  })

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
  
  if os.path.exists(filename):
      os.remove(filename)
  else:
      print(f"{filename}'s not found")
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
  
