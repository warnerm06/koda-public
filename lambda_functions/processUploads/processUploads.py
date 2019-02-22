# Improvements:
# Remove global variables
# change filename to '13/13-asdfadsaf-123.jpg

import boto3
import tinify
import os, requests, time, datetime, json, urllib, shutil

import sqlalchemy
from sqlalchemy import create_engine, dialects, Column, Integer, String, DateTime, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ************ TINIFY API ************************
tinify.key = os.environ['TINIFY_KEY']

# ************* AWS s3 API ***********************
s3 = boto3.resource("s3")

# ************** SQLAlchemy Connection and Models ***********
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

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    image_file = Column(String(100), nullable=False, default='default.jpg')

# ******************** AZURE API ***********************

def azureRequest(file): # get azure Cognitive Services info form local file
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
    pathToFileInDisk = '/tmp/' + file
    with open( pathToFileInDisk, 'rb' ) as f:
        data = f.read()
        
    # Computer Vision parameters
    params = { 'visualFeatures' : 'Color,Categories,Tags,Description,Faces,ImageType,Adult', 'details': 'Celebrities,Landmarks'}
    headers = dict()
    headers['Ocp-Apim-Subscription-Key'] = _key
    headers['Content-Type'] = 'application/octet-stream'

    json = None
    result = processRequest( json, data, headers, params )
    return result # returns json object to store in database

# *************** Create Object from Event *************************************
class LambdaObject(): # create an object to store information about the event that was passed to Lambda
    def __init__(self, event):
        self.key= str(event['Records'][0]['s3']['object']['key']) # exact filename in s3 Bucket
        self.raw_filename= self.key.split('/')[1] # removes 'uploads/' from filename
        self.keySplit = self.raw_filename.split('-') 
        self.action= self.keySplit[0] # get action code
        self.user_id = self.keySplit[1] # get user_id
        # self.user_filename = self.keySplit[2] # get user uploaded filename
        self.file_type= self.key.split('.')[1] # get filetype example'jpg'.... without period
        self.azureResults = None # initially set to none but will be added 
        self.orig_size = int(event['Records'][0]['s3']['object']['size']) # original file size in s3


# ************** Rename File ***********************
def renameFile(orig, arg): # takes filename and inserts arg into 2nd position.  'p-6-x098swdf-123.jpg' becomes 'p-6-x098swdf-arg-123.jpg'
    newName = orig.split('-')
    newName.pop(0)
    newName.insert(2, arg)
    newName= "-".join(newName)
    return newName

# download the file from s3 to local copy
def downloadFile(key): # download based on filname

    s3.Bucket('koda-publicaccess').download_file(key, '/tmp/'+ obj.raw_filename) # download using filename and save to tmp directory

def compress(file):
  
    source = tinify.from_file('/tmp/'+file) # use tinify api to compress file

    compName=renameFile(file, 'Comp') # rename file with 'Comp'
    
    source.to_file('/tmp/'+ compName) # save file
    return compName # return Compress filename

# upload compressed file to s3
def uploadComp(file):
    
    # get size of file in bytes
    comp_size=os.path.getsize('/tmp/'+ file)

    # need to change to variable content type
    s3.Bucket('koda-publicaccess').upload_file('/tmp/'+file,  obj.user_id+'/'+ file,
                                                ExtraArgs={'ContentType': "image/jpeg", "ACL":"public-read"})

    photo= Photos(file_name=obj.user_id+'/'+ file, user_id=obj.user_id, koda_type='Comp',file_type= obj.file_type, file_size=comp_size, bucket='koda-publicaccess', azure_api= obj.azureResults)

    if obj.action == 'p': # if action is 'p' then set profile pic s3 name
        session.query(Users).filter(Users.id==obj.user_id).update({Users.image_file:f'{obj.user_id}/{file}'}, synchronize_session=False)      

    session.add(photo)

def uploadOrig(file):

    orig_name= renameFile(file, 'Orig') # rename file with 'orig'
    
    # note: useing orignal name to get obj but renaming when uploading
    s3.Bucket('koda-publicaccess').upload_file('/tmp/'+file,  obj.user_id +'/'+ orig_name)

    photo= Photos(file_name= obj.user_id + '/' + orig_name, user_id=obj.user_id, koda_type='Orig',file_type= obj.file_type, file_size=obj.orig_size, bucket='koda-publicaccess', azure_api=obj.azureResults)
    
    session.add(photo)

def deleteUserUpload(file, compressed):
    # deletes user file from s3 uploads bucket
    s3.Object('koda-publicaccess', 'uploads/' +file).delete()
    
    try:
        os.remove('/tmp/' + file)
        os.remove('/tmp/' + compressed)

        # shutil.rmtree('/tmp') # remove all files in tmp folder
    except Exception as e :
        print("Error: Failed to remove file from tmp!")
        raise e

    if os.listdir('/tmp') == []:
        print('tmp directory is empty!')
    else:
        print('Files remain in tmp: ' +os.listdir('/tmp'))
# ************* CODE STARTS HERE ************************
obj= None # global object for event information
tmp_files= []

# Lambda event handleer. Called when triggered. 
def lambda_handler(event, context):
    global obj
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    # bucket = event['Records'][0]['s3']['bucket']['name']

    try:
        obj=LambdaObject(event) # create object with all needed properties

        downloadFile(obj.key) # download file
        obj.azureResults=azureRequest(obj.raw_filename) # get azure api results
        compressed=compress(obj.raw_filename) # compress file using tinify
        uploadComp(compressed) # upload Compressed file to s3
        uploadOrig(obj.raw_filename) # upload original file to s3

        session.commit() # commit to db
        session.close() 

        deleteUserUpload(obj.raw_filename, compressed) # delete temporary files from lambda to reduce space
        print("Lambda Function Total Success!")
    except Exception as e:
        print('Error processing file from koda-publicaccess.')
        session.rollback()
        session.close()
        raise e
