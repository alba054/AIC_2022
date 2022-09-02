import csv
import json

from utils import get_database

clientDB = get_database()
CSV_PATH = '../data/animal_detail.csv'

if __name__ == "__main__":
  animals = []
  with open(CSV_PATH) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      animals.append(row)
  
  animalCollection = clientDB["animals"]
  animalCollection.insert_many(animals)