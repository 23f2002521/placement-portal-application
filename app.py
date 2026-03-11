from flask import Flask
from backend.models import db,Admin,Student,Company,PlacementDrive,Application
from flask_login import LoginManager

def create_app():
    app=Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Placement.db"
    db.init_app(app)
    app.config["SECRET_KEY"]="thisgoodday"
    login_manager=LoginManager(app)
    @login_manager.user_loader
    def load_user(email):
        return (db.session.query(Admin).filter_by(email=email).first() or \
        db.session.query(Student).filter_by(email=email).first() or \
        db.session.query(Company).filter_by(email=email).first())
    app.app_context().push()
    db.create_all()
    return app
app=create_app()

from backend.routes import *

from backend.initial_db import *

if __name__=="__main__":
    app.run(debug=True)
