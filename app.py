from flask import Flask
from backend.models import db,Admin,Student,Company,PlacementDrive,Application
def create_app():
    app=Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Placement.db"
    db.init_app(app)
    app.app_context().push()
    db.create_all()
    return app
app=create_app()

from backend.routes import *

from backend.initial_db import *

if __name__=="__main__":
    app.run(debug=True)
