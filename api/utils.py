from pkgutil import get_data
from pymongo import MongoClient
import pymongo

import csv

from conf import DB_CONNECTION

CSV_FILE = '../data/animal_detail.csv'

def get_database():
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(DB_CONNECTION)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['animals']
