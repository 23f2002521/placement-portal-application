from app import app
from flask import render_template,request,redirect,flash,url_for,session
from .models import *
from flask_login import login_user,login_required,current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, cast, String
import os
import uuid

def save_resume_file(resume_file):
    if not resume_file or resume_file.filename == "":
        return None
    filename = secure_filename(resume_file.filename)
    if filename == "":
        return None
    file_ext = os.path.splitext(filename)[1]
    saved_name = f"{uuid.uuid4().hex}{file_ext}"
    resume_folder = os.path.join(app.static_folder, "resumes")
    os.makedirs(resume_folder, exist_ok=True)
    resume_file.save(os.path.join(resume_folder, saved_name))
    return f"resumes/{saved_name}"

@app.route('/')
def home_v():
    return render_template("home.html")

@app.route('/login', methods=["GET","POST"])
def login_page():
    if request.method=="GET":       
        return render_template("login.html")
    elif request.method=="POST":
        email=request.form.get("email")
        password=request.form.get("password")
        u=db.session.query(Admin).filter_by(email=email).first() or \
        db.session.query(Company).filter_by(email=email).first() or \
        db.session.query(Student).filter_by(email=email).first()
        if u:
            if u.password==password:
                if isinstance(u,Admin):
                    login_user(u)
                    return redirect(f"/admin/dash")
                elif isinstance(u,Company):
                    login_user(u)
                    return redirect(f"/company/dash")
                elif isinstance(u,Student):
                    login_user(u)
                    return redirect(f"/students/dash")
            else:
                flash("incorrect password")
                return redirect("/login")
        else:
            flash("incorrect email")
            return redirect("/login")
             
@app.route("/register" , methods=["GET","POST"])
def register():
    if request.method=="GET":
        if request.args.get("u_type")=="company":
            comp=db.session.query(Company).all()
            return render_template("/company/register.html",companies=comp)
        elif request.args.get("u_type")=="student":
            return render_template("/students/register.html")
        else:
            return "Invalid user type"
    elif request.method=="POST":
        if request.args.get("u_type")=="company":
            c_name=request.form.get("comp_name")
            c_email=request.form.get("comp_email")
            c_password=request.form.get("comp_password")
            c_industry=request.form.get("industry")
            c_hr=request.form.get("hr_contact")
            c_web=request.form.get("website")
            com=db.session.query(Company).filter_by(email=c_email).first()
            if not com:
                com=Company(name=c_name,email=c_email,password=c_password,industry=c_industry,hr_contact=c_hr,website=c_web,approval_status="Pending")
                db.session.add(com)
                db.session.commit()
                return redirect("/login")
            else:
                flash("email already exist")
                return redirect("/register?u_type=company")

        elif request.args.get("u_type") == "student":
            s_name=request.form.get("stud_name")
            s_email=request.form.get("stud_email")
            s_password=request.form.get("stud_password")
            s_resume=save_resume_file(request.files.get("resume"))
            student=db.session.query(Student).filter_by(email=s_email).first()
            if not student:
                student=Student(name=s_name,email=s_email,password=s_password,resume=s_resume)
                db.session.add(student)
                db.session.commit()
                return redirect("/login")
            else:
                flash("email already exist")
                return redirect("/register?u_type=student")


    return "error"

@app.route("/admin/dash", methods=["GET","POST"])
@login_required
def ad_dash():
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    student_search = request.args.get("student_search", "").strip()
    company_search = request.args.get("company_search", "").strip()
    comp_query = db.session.query(Company)
    if company_search:
        comp_query = comp_query.filter(
            or_(
                Company.name.ilike(f"%{company_search}%"),
                Company.industry.ilike(f"%{company_search}%")
            )
        )
    comp = comp_query.order_by(Company.name.asc()).all()
    stu_query = db.session.query(Student)
    if student_search:
        stu_query = stu_query.filter(
            or_(
                Student.name.ilike(f"%{student_search}%"),
                cast(Student.stud_id, String).ilike(f"%{student_search}%"),
                Student.email.ilike(f"%{student_search}%")
            )
        )
    stu = stu_query.order_by(Student.name.asc()).all()
    requested_prof = db.session.query(Company).filter_by(approval_status="Pending").order_by(Company.name.asc()).all()
    requested_drives = db.session.query(PlacementDrive).filter_by(status="Waiting").order_by(PlacementDrive.placemnt_id.desc()).all()
    ongoing_drives = (db.session.query(PlacementDrive).filter_by(status="Pending").order_by(PlacementDrive.application_deadline.asc()).all())
    student_applications = (db.session.query(Application).order_by(Application.application_date.desc()).all())
    total_students = db.session.query(Student).count()
    total_companies = db.session.query(Company).count()
    total_applications = db.session.query(Application).count()
    total_drives = db.session.query(PlacementDrive).count()
    return render_template("admin/dash.html",
                           current_ad=current_user,
                           all_comp=comp,
                           all_stu=stu,
                           requested_prof=requested_prof,
                           requested_drives=requested_drives,
                           ongoing_drives=ongoing_drives,
                           student_applications=student_applications,
                           student_search=student_search,
                           company_search=company_search,
                           total_students=total_students,
                           total_companies=total_companies,
                           total_applications=total_applications,
                           total_drives=total_drives)
@app.route("/company/dash", methods=["GET","POST"])
@login_required
def cm_dash():
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status.lower() != "active":
        return "wait for admin's approval"
    rq_drives = PlacementDrive.query.filter_by(company_id=current_user.cmp_id, status="Waiting").all()
    up_drives = PlacementDrive.query.filter_by(company_id=current_user.cmp_id, status="Pending").all()
    cl_drives   = PlacementDrive.query.filter_by(company_id=current_user.cmp_id, status="completed").all()
    rj_drives = PlacementDrive.query.filter_by(company_id=current_user.cmp_id, status="Rejected").all()
    return render_template("company/dash.html",current_comp=current_user,rq_drives=rq_drives,up_drives=up_drives,cl_drives=cl_drives,rj_drives=rj_drives)

@app.route("/students/dash", methods=["GET","POST"])
@login_required
def st_dash():
    if not isinstance(current_user, Student):
        return "Unauthorized"
    search = request.args.get("search", "").strip()
    comp_query = Company.query.filter_by(approval_status="active")
    if search:
        comp_query = comp_query.join(PlacementDrive).filter(
            PlacementDrive.status == "Pending",
            or_(
                Company.name.ilike(f"%{search}%"),
                PlacementDrive.drive_name.ilike(f"%{search}%"),
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.eligibility_criteria.ilike(f"%{search}%"),
                PlacementDrive.skills.ilike(f"%{search}%"),
                PlacementDrive.job_description.ilike(f"%{search}%"))).distinct()
    all_comp = comp_query.all()
    applied_drives = Application.query.filter_by(student_id=current_user.stud_id).order_by(Application.application_date.desc()).all()
    notify_statuses = {
        "Shortlisted": "shortlisted",
        "Rejected": "rejected",
        "Selected": "accepted"
    }
    seen = session.get("app_status_seen")
    if seen is None:
        seen = {}
        for appln in applied_drives:
            if appln.status in notify_statuses:
                seen[str(appln.appln_id)] = appln.status
        session["app_status_seen"] = seen
    else:
        for appln in applied_drives:
            if appln.status in notify_statuses:
                prev = seen.get(str(appln.appln_id))
                if prev != appln.status:
                    flash(f"Your application for {appln.drive.drive_name} at {appln.drive.company.name} was {notify_statuses[appln.status]}.")
                    seen[str(appln.appln_id)] = appln.status
        session["app_status_seen"] = seen
    return render_template("students/dash.html",current_stu=current_user,all_comp=all_comp,applied_drives=applied_drives,search=search)

@app.route("/students/history", methods=["GET"])
@login_required
def student_history():
    if not isinstance(current_user, Student):
        return "Unauthorized"
    applied_drives = (Application.query.filter_by(student_id=current_user.stud_id).order_by(Application.application_date.desc()).all())
    return render_template("students/history.html", current_stu=current_user, applied_drives=applied_drives)

@app.route("/students/profile", methods=["GET","POST"])
@login_required
def student_profile():
    if not isinstance(current_user, Student):
        return "Unauthorized"
    if request.method=="POST":
        current_user.name=request.form.get("stud_name")
        current_user.skills=request.form.get("skills")
        current_user.education=request.form.get("education")
        current_user.department=request.form.get("department")
        resume_path=save_resume_file(request.files.get("resume"))
        if resume_path:
            current_user.resume=resume_path
        db.session.commit()
        flash("profile updated")
        return redirect(url_for("student_profile"))
    return render_template("students/profile.html", current_stu=current_user)
       
@app.route("/company",methods=["POST"])
@login_required
def cmp_approve():
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    if request.args.get("task")=="approve":
        cmp_id=request.args.get("cmp_id")
        cmp=db.session.query(Company).filter_by(cmp_id=cmp_id).first()
        if cmp:
            cmp.approval_status="active"
            db.session.commit()
            flash(f"{cmp.name} is approved" )
            return redirect("/admin/dash")
        else:
            return "unable to approve"

@app.route("/admin/company/<int:cmp_id>/blacklist", methods=["POST"])
@login_required
def admin_blacklist_company(cmp_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    cmp = Company.query.get_or_404(cmp_id)
    cmp.approval_status = "blacklisted"
    active_drives = PlacementDrive.query.filter(PlacementDrive.company_id == cmp_id,PlacementDrive.status != "completed",PlacementDrive.status != "cancelled").all()
    for drive in active_drives:
        drive.status = "cancelled"
    db.session.commit()
    flash(f"{cmp.name} is blacklisted and active drives are cancelled")
    return redirect("/admin/dash")

@app.route("/admin/company/<int:cmp_id>/unblacklist", methods=["POST"])
@login_required
def admin_unblacklist_company(cmp_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    cmp = Company.query.get_or_404(cmp_id)
    if cmp.approval_status.lower() != "blacklisted":
        flash(f"{cmp.name} is not blacklisted")
        return redirect("/admin/dash")
    cmp.approval_status = "active"
    now = datetime.now()
    cancelled_drives = PlacementDrive.query.filter(
        PlacementDrive.company_id == cmp_id,
        PlacementDrive.status == "cancelled",
        PlacementDrive.application_deadline > now
    ).all()
    for drive in cancelled_drives:
        drive.status = "Pending"
    db.session.commit()
    if cancelled_drives:
        flash(f"{cmp.name} is unblacklisted. Restored {len(cancelled_drives)} active drive(s).")
    else:
        flash(f"{cmp.name} is unblacklisted")
    return redirect("/admin/dash")

@app.route("/admin/student/<int:stud_id>/blacklist", methods=["POST"])
@login_required
def admin_blacklist_student(stud_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    stu = Student.query.get_or_404(stud_id)
    stu.status = "blacklisted"
    db.session.commit()
    flash(f"{stu.name} is blacklisted")
    return redirect("/admin/dash")

@app.route("/admin/student/<int:stud_id>/unblacklist", methods=["POST"])
@login_required
def admin_unblacklist_student(stud_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    stu = Student.query.get_or_404(stud_id)
    if stu.status.lower() != "blacklisted":
        flash(f"{stu.name} is not blacklisted")
        return redirect("/admin/dash")
    stu.status = "Active"
    db.session.commit()
    flash(f"{stu.name} is unblacklisted")
    return redirect("/admin/dash")

@app.route("/admin/drive/<int:drive_id>/approve", methods=["POST"])
@login_required
def admin_approve_drive(drive_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Pending"
    db.session.commit()
    flash(f"{drive.drive_name} is approved")
    return redirect("/admin/dash")

@app.route("/admin/drive/<int:drive_id>/reject", methods=["POST"])
@login_required
def admin_reject_drive(drive_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Rejected"
    db.session.commit()
    flash(f"{drive.drive_name} is rejected")
    return redirect("/admin/dash")

@app.route("/admin/drive/<int:drive_id>", methods=["GET"])
@login_required
def admin_drive_details(drive_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    drive = PlacementDrive.query.get_or_404(drive_id)
    return render_template("admin/drive_details.html", drive=drive)

@app.route("/admin/drive/<int:drive_id>/complete", methods=["POST"])
@login_required
def admin_mark_drive_complete(drive_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "completed"
    db.session.commit()
    flash(f"{drive.drive_name} marked as complete")
    return redirect("/admin/dash")

@app.route("/admin/application/<int:appln_id>", methods=["GET"])
@login_required
def admin_application_details(appln_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized"
    appln = Application.query.get_or_404(appln_id)
    return render_template("admin/application_details.html", appln=appln)

@app.route("/logout")
def log_out():
    return redirect("/login")

@app.route("/drive", methods=["GET","POST"])
@login_required
def create_drive():
    if not isinstance(current_user,Company):
        return "unauthorized"
    if current_user.approval_status.lower() != "active":
        return "wait for admin's approval"
    if request.method=="POST":
            name=request.form.get("name")
            if name:
                name = name.strip()
            existing = PlacementDrive.query.filter_by(drive_name=name).first()
            if existing:
                flash("Drive name already exists")
                return redirect("/drive")
            job_title=request.form.get("job_title")
            job_description=request.form.get("job_description")
            elig_cri=request.form.get("eligibility_criteria")
            salary=request.form.get("salary")
            skills=request.form.get("skills")
            exp=request.form.get("exp")
            application_deadline = datetime.fromisoformat(request.form['application_deadline'])
    
            new_drive = PlacementDrive(
                drive_name = name,
                company_id = current_user.cmp_id,
                job_title = job_title,
                job_description = job_description,
                eligibility_criteria = elig_cri,
                skills=skills,
                exp=exp,
                application_deadline = application_deadline,
                salary=salary,
                status = "Waiting"
            )
            db.session.add(new_drive)
            db.session.commit()
            flash("drive created and waiting for admin approval")
            return redirect("/company/dash")
    return render_template("/company/drive.html")
            

@app.route("/mark_complete",methods=["POST"])
def mark_comp():
    if request.args.get("task")=="completed":
        pl=request.args.get("placemnt_id")
        plm=db.session.query(PlacementDrive).filter_by(placemnt_id=pl).first()
        if plm:
            plm.status="completed"
            flash(f"{plm.drive_name} marked as completed ")
            db.session.commit()
            return redirect("/company/dash")
        else:
            return "unable to mark as completed"
    
@app.route("/close_drive/<int:drive_id>", methods=["POST"])
@login_required
def close_drive(drive_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status.lower() != "active":
        return "Wait for admin's approval"
    drive = PlacementDrive.query.filter_by(placemnt_id=drive_id, company_id=current_user.cmp_id).first()
    if not drive:
        return "Drive not found or not authorized"
    drive.status = "completed"
    db.session.commit()
    flash(f"{drive.drive_name} marked as closed")
    return redirect("/company/dash")

@app.route("/update_drive/<int:drive_id>",methods=["POST"])
@login_required
def update_drive(drive_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status!="active":
        return "wait for admin approval"
    drive=PlacementDrive.query.filter_by(placemnt_id=drive_id, company_id=current_user.cmp_id).first()
    if not drive: 
        return "drive not found"
    if drive.status.lower()=="completed":
        drive.status="Pending"
        flash(f"{drive.drive_name} moved  on upcomming drives")
    else:
        drive.status="completed"
        drive.status="completed"
        flash(f"{drive.drive_name} mark as closed")
    db.session.commit()
    return redirect("/company/dash")
        
@app.route("/view_drive/<int:cmp_id>",methods=["GET"])
@login_required
def view_compd(cmp_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status!="active":
        return "wait for admin approval"
    company=Company.query.filter_by( company_id=current_user.cmp_id).first()
    if not company:
        return "company not found"
    drives = PlacementDrive.query.filter_by(company_id=cmp_id).all()
    return render_template("/company/comp_details.html",company=company,current_user=current_user)

@app.route("/drive_v/<int:drive_id>", methods=["GET"])
@login_required
def view_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if isinstance(current_user, Student):
        if drive.status.lower() != "pending" or drive.company.approval_status.lower() != "active":
            return "Drive not available"
    return render_template("drive_details.html", drive=drive)

@app.route("/company/<int:cmp_id>/drives", methods=["GET"])
@login_required
def company_drives(cmp_id):
    company = Company.query.get_or_404(cmp_id)
    if isinstance(current_user, Student):
        if company.approval_status.lower() != "active":
            return "Unauthorized"
    drives = PlacementDrive.query.filter_by(company_id=cmp_id,status="Pending").all()
    # student_id=Application.query.filter_by(student_id=student_id)
    return render_template("company/that_cdrive.html",company=company,drives=drives,status="Pending")
@app.route("/students/apply_drive/<int:drive_id>", methods=["GET"])
@login_required
def student_apply_drive(drive_id):
    if not isinstance(current_user, Student):
        return "Unauthorized"
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status.lower() != "pending" or drive.company.approval_status.lower() != "active":
        return "Cannot apply to this drive"
    return render_template("students/apply_drive.html", drive=drive)

@app.route("/students/apply_job/<int:drive_id>", methods=["POST"])
@login_required
def apply_button(drive_id):
    if not isinstance(current_user, Student):
        return "Unauthorized", 403
    existing = Application.query.filter_by(student_id=current_user.stud_id,drive_id=drive_id).first()
    if existing:
        flash("You already applied for this drive.")
    else:
        appln = Application(student_id=current_user.stud_id, drive_id=drive_id, status="Applied")
        db.session.add(appln)
        db.session.commit()
        flash("Successfully applied!")

    return redirect(url_for("student_apply_drive", drive_id=drive_id))

@app.route("/company/drive/<int:drive_id>/appln",methods=["GET"])
@login_required
def revw_drive_appln(drive_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status.lower()!="active":
        return "wait for admin's approval"
    drive = PlacementDrive.query.filter_by(placemnt_id=drive_id,company_id=current_user.cmp_id ).first_or_404()
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template("company/stu_appln.html", drive=drive, applications=applications)

@app.route("/company/application/<int:appln_id>/status", methods=["POST"])
@login_required
def update_appln_status(appln_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    appln = Application.query.get_or_404(appln_id)
    drive = PlacementDrive.query.filter_by(placemnt_id=appln.drive_id,company_id=current_user.cmp_id).first()
    if not drive:
        return "Unauthorized"
    new_status = request.form.get("status")
    allowed = ["Rejected", "Shortlisted", "Selected", "Waitlisted","Interview"]
    if new_status not in allowed:
        flash("Invalid status")
        return redirect(url_for("revw_drive_appln", drive_id=appln.drive_id))
    appln.status = new_status
    db.session.commit()
    flash("Application status updated")
    return redirect(url_for("revw_drive_appln", drive_id=appln.drive_id))

@app.route("/company/application/<int:appln_id>/review", methods=["GET", "POST"])
@login_required
def review_one_appln(appln_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status.lower()!="active":
        return "wait for admin's approval"
    appln = Application.query.get_or_404(appln_id)
    drive = PlacementDrive.query.filter_by(placemnt_id=appln.drive_id, company_id=current_user.cmp_id).first()
    if not drive:
        return "Unauthorized"
    if request.method == "POST":
        new_status = request.form.get("status")
        allowed = ["Shortlisted", "Rejected", "Waitlisted"]
        if new_status not in allowed:
            flash("Invalid status")
            return redirect(url_for("review_one_appln", appln_id=appln_id))
        appln.status = new_status
        db.session.commit()
        flash("status updated")
        return redirect(url_for("review_one_appln", appln_id=appln_id))

    return render_template("company/review_one_appln.html", appln=appln, drive=drive)

@app.route("/company/drive/<int:drive_id>/shortlisted", methods=["GET"])
@login_required
def view_shortls_stu(drive_id):
    if not isinstance(current_user, Company):
        return "Unauthorized"
    if current_user.approval_status.lower() != "active":
        return "wait for admin's approval"
    drive = PlacementDrive.query.filter_by(placemnt_id=drive_id, company_id=current_user.cmp_id).first_or_404()
    shortlisted_apps = Application.query.filter_by(drive_id=drive_id, status="Shortlisted").all()
    return render_template("company/shortlisted_students.html", drive=drive, shortlisted_apps=shortlisted_apps)

@app.route("/admin/company/<int:cmp_id>/reject", methods=["POST"])
@login_required
def reject_comp(cmp_id):
    if not isinstance(current_user,Admin):
        return "unauthorized"
    cmp=Company.query.get_or_404(cmp_id)
    cmp.approval_status="rejected"
    db.session.commit()
    flash(f"{cmp.name} rejected")
    return redirect("/admin/dash")





