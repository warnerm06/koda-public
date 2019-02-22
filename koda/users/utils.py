
import os, re, uuid
import secrets
# from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from flask_login import current_user
from koda import mail

def save_picture(form_picture, code): # saves picture and renames it
    print(form_picture.filename)
    f_name, f_ext = os.path.splitext(form_picture.filename) # splits filename
    clean= re.sub('[^0-9a-zA-Z]+', '_', f_name) # removes all chars except 0-9, a-z, A-Z, and _
    clean = (clean[-50:]) if len(clean) > 50 else clean # truncate to 50 chars or less
    userid= current_user.id
    UUID=uuid.uuid4().hex
    newFilename= f'{code}-{userid}-{UUID}-{clean}{f_ext}' # new unique filename

    picture_path = os.path.join(current_app.root_path, 'tmp', newFilename)
    form_picture.save(picture_path) # save picture to tmp directory
   
    pic_info={}
    pic_info['filename']=newFilename
    pic_info['filepath']=picture_path

    return pic_info

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)











