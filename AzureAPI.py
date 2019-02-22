# from localConfig import AWS_access_key_id, AWS_secret_access_key, AWS_DB_URI
import sqlalchemy
from sqlalchemy import create_engine, dialects
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, VARCHAR
import datetime
from sqlalchemy.orm import sessionmaker
import json
import urllib
import time 
import requests
import operator
import os
import random

import urllib
from pprint import pprint


engine= create_engine(os.environ['AWS_DB_URI'])
Session= sessionmaker()
Session.configure(bind=engine)
session=Session()

Base= declarative_base()

class Photos(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    file_name= Column(String(100),nullable = False, unique=True)
    user_id=Column(Integer, nullable=False, default = 0)
    koda_type= Column(String(20),nullable=False, default='error')
    file_type=Column(String(10), nullable = False, default="error")
    file_size=Column(Integer, nullable=False, default = 0)
    date_posted = Column(DateTime, nullable=False, default= datetime.datetime.now())
    bucket= Column(String(50), nullable=False)
    azure_api=Column(dialects.postgresql.JSONB())



# Variables
_region = 'westus' #Here you enter the region of your subscription
_url = 'https://{}.api.cognitive.microsoft.com/vision/v2.0/analyze'.format(_region)
_key = os.environ["AZURE_API_KEY"]
_maxNumRetries = 10

def processRequest( json, data, headers, params ):

    retries = 0
    result = None

    while True:
        response = requests.request( 'post', _url, json = json, data = data, headers = headers, params = params )
        if response.status_code == 429: 
            print( "Message: %s" % ( response.json() ) )
            if retries <= _maxNumRetries: 
                time.sleep(1) 
                retries += 1
                continue
            else: 
                print( 'Error: failed after retrying!' )
                break
        elif response.status_code == 200 or response.status_code == 201:
            if 'content-length' in response.headers and int(response.headers['content-length']) == 0: 
                result = None 
            elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str): 
                if 'application/json' in response.headers['content-type'].lower(): 
                    result = response.json() if response.content else None 
                elif 'image' in response.headers['content-type'].lower(): 
                    result = response.content
        else:
            print( "Error code: %d" % ( response.status_code ) )
            print( "Message: %s" % ( response.json() ) )
        break
            return result
    
# Load raw image file into memory
pathToFileInDisk = r'C:\Users\warne\Desktop\BC Homework\Final_Project_Img_Analysis\static\uploads\IMG_6525.jpg'
with open( pathToFileInDisk, 'rb' ) as f:
    data = f.read()
    
# Computer Vision parameters
params = { 'visualFeatures' : 'Color,Categories,Tags,Description,Faces,ImageType,Adult', 'details': 'Celebrities,Landmarks'}
headers = dict()
headers['Ocp-Apim-Subscription-Key'] = _key
headers['Content-Type'] = 'application/octet-stream'

json = None
result = processRequest( json, data, headers, params )

if result is not None:
    pprint(result)
    print(type(result))
    photo= Photos(file_name=random.randint(0,10000), user_id=00, koda_type='Test',file_type= 'jpg', file_size=00, bucket='koda-publicaccess', azure_api=result)
    

    session.add(photo)
    session.commit()