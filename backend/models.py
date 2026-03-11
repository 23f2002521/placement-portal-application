from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone
from flask_login import UserMixin
db=SQLAlchemy()


class Admin(db.Model,UserMixin):
    __tablename__ = 'admin'
    a_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,  nullable=False)
    email= db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    def get_id(self):
        return (self.email)
    
class Company(db.Model,UserMixin):
    __tablename__ = 'companies'
    cmp_id = db.Column(db.Integer, primary_key=True , autoincrement=True)
    name = db.Column(db.String,unique=True, nullable=False)
    industry = db.Column(db.String)
    hr_contact = db.Column(db.String, nullable=False)
    website = db.Column(db.String)
    approval_status = db.Column(db.String, default="Pending")  
    password= db.Column(db.String, nullable=False)
    drives = db.relationship('PlacementDrive', backref='company', lazy=True)
    email= db.Column(db.String, unique=True, nullable=False)
    
    def get_id(self):
        return (self.email)
class Student(db.Model,UserMixin):
    __tablename__ = 'students'
    stud_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    skills = db.Column(db.Text)
    education = db.Column(db.Text)
    department=db.Column(db.String)
    resume = db.Column(db.String)  
    status = db.Column(db.String, default="Active") 
    applications = db.relationship('Application', backref='student', lazy=True)
    def get_id(self):
        return (self.email)
class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    placemnt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drive_name=db.Column(db.String, nullable=False,unique=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.cmp_id'), nullable=False)
    job_title = db.Column(db.String, nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=False)
    application_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, default="Pending")  
    salary=db.Column(db.Integer,nullable="False")
    skills=db.Column(db.String, nullable=False)
    exp=db.Column(db.String, nullable=False)
    applications = db.relationship('Application', backref='drive', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    appln_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.stud_id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.placemnt_id'), nullable=False)
    application_date = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))
    status = db.Column(db.String , default="not_applied")  

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),
    )
