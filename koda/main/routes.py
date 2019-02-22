from flask import render_template, request, Blueprint,redirect, send_from_directory
from koda.models import Post
# from localConfig import aws_access_key_id, aws_secret_access_key, bucket
# import boto3
from botocore.client import Config
import requests, json, os
from urllib.parse import urljoin


main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@main.route("/about")
def about():
    return render_template('about.html', title='About')

# Custom static for CDN
@main.route('/cdn/<path:filename>')
def custom_static(filename):
    return redirect(urljoin(os.environ['CLOUDFRONT_CDN_MAIN'], filename))
    


