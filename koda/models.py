from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from koda import db, login_manager
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB






@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(100), nullable=False, default='default_profile_pic.png')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)


    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Photos(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    file_name= db.Column(db.String(100),nullable = False, unique=True)
    user_id=db.Column(db.Integer, nullable=False, default = 0)
    koda_type= db.Column(db.String(20),nullable=False, default='error')
    file_type=db.Column(db.String(10), nullable = False, default="error")
    file_size=db.Column(db.Integer, nullable=False, default = 0)
    date_posted = db.Column(db.DateTime, nullable=False, default= datetime.utcnow())
    bucket= db.Column(db.String(50), nullable=False)
    azure_api=db.Column(JSONB) # Idk why this works but it does. 

    def __repr__(self):
        return f"Photos('{self.user_id}', '{self.file_type}')"