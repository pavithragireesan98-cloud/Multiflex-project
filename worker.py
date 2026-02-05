from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import *

worker = Blueprint('worker', __name__)

# ---------------------------------------------------------
# Worker Home
# ---------------------------------------------------------
@worker.route('/worker_home')
def worker_home():
    lid = session['lid']
    q = "SELECT First_name FROM worker WHERE Login_id='%s'" % lid
    res = select(q)
    worker_name = res[0]['First_name'] if res else "Worker"
    return render_template("worker_home.html", worker_name=worker_name)



# ---------------------------------------------------------
# Add Worker Skill
# ---------------------------------------------------------
@worker.route('/worker_add_skills', methods=['GET', 'POST'])
def worker_add_skills():
    wid = session.get('worker_id')
    if not wid:
        flash("Worker not logged in", "danger")
        return redirect(url_for('public.login'))

    skills = select("SELECT * FROM skill")

    q2 = """
        SELECT s.skill_name 
        FROM worker_skill ws 
        JOIN skill s ON ws.skill_id = s.skill_id 
        WHERE ws.worker_id = '%s'
    """ % wid
    current_skills = select(q2)

    if request.method == 'POST':
        skill_id = request.form['skill_id']
        check = select("SELECT * FROM worker_skill WHERE worker_id='%s' AND skill_id='%s'" % (wid, skill_id))

        if check:
            flash("Skill already exists!", "warning")
        else:
            insert("INSERT INTO worker_skill (worker_id, skill_id) VALUES ('%s', '%s')" % (wid, skill_id))
            flash("Skill added successfully!", "success")

        return redirect(url_for('worker.worker_add_skills'))

    return render_template('worker_add_skills.html', skills=skills, current_skills=current_skills)



# ---------------------------------------------------------
# Worker Accept Request
# ---------------------------------------------------------
@worker.route('/accept_request/<req_id>')
def accept_request(req_id):
    wid = session.get('worker_id')
    q = "UPDATE request_master SET worker_status='assigned', worker_id='%s' WHERE request_id='%s'" % (wid, req_id)
    update(q)
    flash("Request assigned — Now set date & time!", "success")
    return redirect(url_for('worker.worker_view_requests'))



# ---------------------------------------------------------
# Worker Reject Request
# ---------------------------------------------------------
@worker.route('/reject_request/<req_id>')
def reject_request(req_id):
    wid = session.get('worker_id')
    q = "UPDATE request_master SET worker_status='rejected', worker_id='%s' WHERE request_id='%s'" % (wid, req_id)
    update(q)
    flash("Request rejected!", "danger")
    return redirect(url_for('worker.worker_view_requests'))



# ---------------------------------------------------------
# Worker set Date/Time for Work (SAVE proposal amount)
# ---------------------------------------------------------
@worker.route('/confirm_time/<request_id>', methods=['GET', 'POST'])
def confirm_time(request_id):
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        amount = request.form['amount']

        update("UPDATE request_master SET work_date='%s', work_time='%s', worker_status='assigned', status='worker_confirmed' WHERE request_id='%s'" % (date, time, request_id))

        wid = session.get('worker_id')

        q3 = """
            INSERT INTO proposals (request_master_id, worker_id, amount, status)
            VALUES ('%s','%s','%s','pending')
            ON DUPLICATE KEY UPDATE amount='%s', status='pending'
        """ % (request_id, wid, amount, amount)
        update(q3)

        flash("✔ Time & amount saved!", "success")
        return redirect(url_for('worker.worker_view_requests'))

    return render_template('worker_confirm_time.html', request_id=request_id)



# ---------------------------------------------------------
# Worker View Assigned Requests
# ---------------------------------------------------------
@worker.route('/worker_view_requests')
def worker_view_requests():
    worker_id = session.get('worker_id')
    # Get all skill IDs for this worker
    skill_rows = select("SELECT skill_id FROM worker_skill WHERE worker_id='%s'" % worker_id)
    skill_ids = [str(row['skill_id']) for row in skill_rows]
    skill_ids_str = ','.join(skill_ids) if skill_ids else '0'

    # Requests assigned to this worker
    q1 = """
        SELECT 
            r.request_id, r.request_date, r.details, r.worker_status,
            r.user_decision, r.status,
            u.first_name, u.last_name, u.phone_no, u.post_office, u.district,
            s.skill_name
        FROM request_master r
        JOIN user u ON r.user_id = u.user_id
        JOIN skill s ON r.skill_id = s.skill_id
        WHERE r.worker_id='%s'
    """ % worker_id

    # Requests matching worker's skills and not yet assigned
    q2 = """
        SELECT 
            r.request_id, r.request_date, r.details, r.worker_status,
            r.user_decision, r.status,
            u.first_name, u.last_name, u.phone_no, u.post_office, u.district,
            s.skill_name
        FROM request_master r
        JOIN user u ON r.user_id = u.user_id
        JOIN skill s ON r.skill_id = s.skill_id
        WHERE (r.worker_id IS NULL OR r.worker_id = '' OR r.worker_id = 0)
        AND r.skill_id IN (%s)
    """ % skill_ids_str

    data1 = list(select(q1))
    data2 = list(select(q2))
    data = data1 + data2
    # Remove duplicates if any (by request_id)
    seen = set()
    unique_data = []
    for row in data:
        if row['request_id'] not in seen:
            unique_data.append(row)
            seen.add(row['request_id'])
    return render_template('worker_view_requests.html', data=unique_data)



# ---------------------------------------------------------
# Worker Confirm Works (user accepted)
# ---------------------------------------------------------
@worker.route('/worker_confirm_works')
def worker_confirm_works():
    worker_id = session.get('worker_id')

    q = """
        SELECT 
            r.request_id, r.details, r.work_date, r.work_time,
            r.user_decision, r.status,
            u.first_name, u.last_name, u.phone_no,
            s.skill_name,
            p.amount, p.status AS pstatus
        FROM request_master r
        JOIN user u ON r.user_id = u.user_id
        JOIN skill s ON r.skill_id = s.skill_id
        LEFT JOIN proposals p ON p.request_master_id = r.request_id
        WHERE r.worker_id='%s'
    """ % worker_id

    data = select(q)
    return render_template("worker_confirm_works.html", data=data)



# ---------------------------------------------------------
# Worker Mark Work Finished
# ---------------------------------------------------------
@worker.route('/worker_mark_work_finished/<int:req_id>')
def worker_mark_work_finished(req_id):
    update("UPDATE request_master SET status='completed' WHERE request_id='%s'" % req_id)
    flash("✔ Work marked finished — waiting for user payment", "success")
    return redirect(url_for('worker.worker_confirm_works'))



# ---------------------------------------------------------
# Worker Request Payment — NO request_payment column used
# ---------------------------------------------------------
@worker.route('/request_payment/<req_id>', methods=['GET', 'POST'])
def worker_request_payment(req_id):
    wid = session.get('worker_id')
    if request.method == 'POST':
        amount = request.form.get('amount')
        if amount:
            # Update proposals table with new amount and set status to pending
            update("UPDATE proposals SET amount='%s', status='pending' WHERE request_master_id='%s' AND worker_id='%s'" % (amount, req_id, wid))
            flash("💰 Payment request sent to user", "success")
            return redirect(url_for('worker.worker_confirm_works'))
        else:
            flash("Amount is required", "danger")
            return redirect(url_for('worker.worker_request_payment', req_id=req_id))
    # GET: Show form with current proposal amount
    proposal = select("SELECT amount FROM proposals WHERE request_master_id='%s' AND worker_id='%s'" % (req_id, wid))
    work_time = select("SELECT work_time FROM request_master WHERE request_id='%s'" % req_id)
    return render_template('worker_request_payment.html', req_id=req_id, proposal=proposal[0] if proposal else None, work_time=work_time[0]['work_time'] if work_time else None)



# ---------------------------------------------------------
# Worker Profile
# ---------------------------------------------------------
@worker.route('/worker_profile')
@worker.route('/admin_view_worker/<int:wid>')
def worker_profile(wid=None):

    if wid is None:
        wid = session.get('worker_id')

    q = "SELECT * FROM worker WHERE worker_id='%s'" % wid
    res = select(q)

    return render_template("worker_profile.html", worker=res[0] if res else None)




@worker.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('public.login'))



@worker.route('/worker_view_review')
def worker_view_review():
    wid = session['worker_id']

    q = """
        SELECT r.*, u.first_name, u.last_name
        FROM review r 
        JOIN user u ON r.user_id=u.user_id
        WHERE r.worker_id='%s'
        ORDER BY r.review_id DESC
    """ % wid

    data = select(q)
    return render_template("worker_view_reviews.html", reviews=data)