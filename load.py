import csv
import json
import sys

from utils_api import get_database

clientDB = get_database()

def load_csv_to_database():
  CSV_PATH = '../data/animal_detail.csv'
  animals = []
  with open(CSV_PATH) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      animals.append(row)
  
  animalCollection = clientDB["animals"]
  animalCollection.insert_many(animals)

def insert_document(path_to_document):
  with open(path_to_document) as jsonfile:
    zones = json.load(jsonfile)
  
  locationsCollection = clientDB["locations"]
  locationsCollection.insert_many(zones)

def update_document(path_to_document):
  with open(path_to_document) as jsonfile:
    updates = json.load(jsonfile)
  
  animalsCollection = clientDB["animals"]
  for update in updates:
    animalsCollection.update_one(update['data'], update['updated'])

if __name__ == "__main__":
  if sys.argv[1] == "insert":
    if len(sys.argv) < 3:
      print("provide path")
    else:
      insert_document(sys.argv[2])
  elif sys.argv[1] == "update":
    if len(sys.argv) < 3:
      print("provide path")
    else:
      update_document(sys.argv[2])


  # print(sys.argv)
  # insert_document("data/locations.json")