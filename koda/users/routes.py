from flask import render_template, url_for, flash, redirect, request, Blueprint, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from koda import db, bcrypt
from koda.models import Users, Post, Photos
from koda.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   RequestResetForm, ResetPasswordForm, AddImgForm)
from koda.users.utils import save_picture, send_reset_email
import boto3
import json, os, re, uuid
from pprint import pprint
# from localConfig import bucket, aws_access_key_id, aws_secret_access_key

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Users(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():

        if form.picture.data: # if a picture is provided save picture
    
            picture_file= save_picture(form.picture.data, 'p') # saves picture and returns dict with ['filepath'] and ['filename']
                 
            BUCKET= os.environ['BUCKET'] # should send to 'koda-publicaccess/uploads' bucket in production

            s3= boto3.resource("s3", 
                        region_name = "us-east-2", # had to add "us-east-2" as incorrect region was generated
                        config= boto3.session.Config(signature_version='s3v4'), # must add this to address newer security
                        aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"],
                        aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]) # AWS Generated key pairs

            s3.Bucket(BUCKET).upload_file(picture_file['filepath'], 'uploads/'+ picture_file['filename']) #upload to s3
            
            current_user.image_file= 'uploads/'+picture_file['filename']
            print(current_user.image_file)
            os.remove(picture_file['filepath']) # remove file from tmp directory

        current_user.username = form.username.data 
        current_user.email = form.email.data
        db.session.commit() # commit changes

        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = current_user.image_file
        
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@users.route("/user/<int:id>")
def user_posts(id):
    page = request.args.get('page', 1, type=int)
    user = Users.query.filter_by(id=id).first_or_404()
    
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

# **************** GALLERY **************************************************
@login_required
@users.route("/gallery/<int:id>", methods=['GET', 'POST'])
def user_gallery(id):
    if id != current_user.id:
        abort(403)
    
    addImgForm = AddImgForm()
    if addImgForm.validate_on_submit():
        if addImgForm.images:
            for img in addImgForm.images.data:
                print(type(img))
          
                picture_file= save_picture(img, "") # saves picture and returns dict with ['filepath'] and ['filename']
                    
                BUCKET= os.environ['BUCKET'] # should send to 'koda-publicaccess/uploads' bucket in production

                s3= boto3.resource("s3", 
                            region_name = "us-east-2", # had to add "us-east-2" as incorrect region was generated
                            config= boto3.session.Config(signature_version='s3v4'), # must add this to address newer security
                            aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"],
                            aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]) # AWS Generated key pairs

                s3.Bucket(BUCKET).upload_file(picture_file['filepath'], 'uploads/'+ picture_file['filename']) #upload to s3
                
                os.remove(picture_file['filepath']) # remove file from tmp directory
        flash('Your images have been added!', 'success')
        return redirect(url_for('users.user_gallery', id=current_user.id))
    
    photos= Photos.query.filter_by(user_id=id, koda_type= "Comp")
    user = Users.query.filter_by(id=id).first_or_404()

    return render_template('users_gallery.html', user=user, photos=photos, 
                                                 title= 'Gallery', addImgForm=addImgForm)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = Users.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@users.route("/s3Request/")
@login_required
def s3UploadRequest():
    file_name = request.args.get('file-name')

    f_name, f_ext = os.path.splitext(file_name) # split into filename and ext
    clean= re.sub('[^0-9a-zA-Z]+', '_', f_name) # remove all chars execpt 0-9, a-z and _
    UUID=uuid.uuid4().hex # generate a universal unique id
    userid=current_user.id # get userid for file prefix
    newFilename= f'{userid}-{UUID}-{clean}{f_ext}' # combine all info to create a unique and uniform filename
    
    file_type = request.args.get('file-type')
    BUCKET= os.environ['BUCKET'] # should send to 'uploads' in production

    s3= boto3.client("s3", 
                region_name = "us-east-2", # had to add "us-east-2" as incorrect region was generated
                config= boto3.session.Config(signature_version='s3v4'), # must add this to address newer security
                aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]) # AWS Generated key pairs

    presigned_post = s3.generate_presigned_post(
        Bucket = BUCKET,
        Key = newFilename,
        Fields = {"Content-Type": file_type},
        Conditions = [{"Content-Type": file_type}],
        ExpiresIn = 3600)

    current_user.image_file= newFilename
    db.session.commit()
    return json.dumps({'data': presigned_post, 
                       'url': f'https://{BUCKET}.s3.amazonaws.com/{newFilename}'}) 

