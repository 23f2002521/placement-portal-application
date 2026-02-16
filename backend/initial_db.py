from backend.models import db, Admin, Company,Student,PlacementDrive,Application
from datetime import datetime

if db.session.query(Admin).count()==0:
    admin=Admin(name="admin",email="admin@hospital.com",password="pass")
    db.session.add(admin)
    db.session.commit()

comp=Company(name="googl", hr_contact="1234",website="www.googl.com",approval_status="pending",password="123")
db.session.add(comp)
db.session.commit()

stud=Student(name="safa",email="safa@gmail.com",password="123",resume="this is my resume",status="active")
db.session.add(stud)
db.session.commit()

placemnt=PlacementDrive(company_id=1,job_title="sde",job_description="hhh",eligibility_criteria="jjskhd",application_deadline=datetime(2026, 3, 15, 23, 59), status="pending")
db.session.add(placemnt)
db.session.commit()

appln=Application(student_id=1,drive_id=2,status="applied")
db.session.add(appln)
db.session.commit()
