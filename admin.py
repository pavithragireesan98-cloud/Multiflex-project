from flask import Blueprint, render_template, request, redirect, url_for
from database import select, insert, update, delete
from datetime import datetime

admin = Blueprint('admin', __name__)

# -------------------- ADMIN HOME --------------------
@admin.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')


# -------------------- ADD SKILL --------------------
@admin.route('/admin_manage_skills', methods=['GET', 'POST'])
def admin_manage_skills():
    if 'submit' in request.form:
        skill_name = request.form['skill_name']
        q = "INSERT INTO skill (skill_name) VALUES ('%s')" % (skill_name)
        insert(q)
        return "<script>alert('Skill added successfully!');window.location='/admin_manage_skills'</script>"

    # Fetch all skills
    q = "SELECT * FROM skill"
    data = select(q)
    return render_template('admin_add_skill.html', data=data)



@admin.route('/delete_skill/<int:id>')
def delete_skill(id):
    delete("DELETE FROM skill WHERE skill_id='%s'" % (id))
    res = select("SELECT COUNT(*) AS count FROM skill")
    if res and res[0]['count'] == 0:
        update("ALTER TABLE skill AUTO_INCREMENT = 1")
    return redirect(url_for('admin.admin_manage_skills'))


# -------------------- APPROVE WORKERS --------------------
@admin.route('/approve_workers')
def approve_workers():
    # Fetch pending workers
    q1 = "SELECT worker_id, first_name, last_name, email, status FROM worker WHERE status='pending'"
    pending = select(q1)

    # Fetch rejected workers
    q2 = "SELECT worker_id, first_name, last_name, email, status FROM worker WHERE status='rejected'"
    rejected = select(q2)

    # Fetch approved workers
    q3 = "SELECT worker_id, first_name, last_name, email, status FROM worker WHERE status='approved'"
    approved = select(q3)

    return render_template('admin_approve_workers.html', pending=pending, rejected=rejected, approved=approved)


# -------------------- VIEW USERS --------------------
@admin.route('/view_users')
def view_users():
    q = "SELECT * FROM user"
    users = select(q)
    return render_template('admin_view_users.html', users=users)


    # -------------------- VIEW REQUESTS --------------------
@admin.route('/view_requests')
def view_requests():
    q = """
        SELECT 
            r.request_id,
            r.user_id,
            -- If work_place is '0' use the user's House_name, otherwise show work_place
            CASE WHEN r.work_place = '0' OR r.work_place = 0 THEN u.House_name ELSE r.work_place END AS work_place_display,
            u.first_name AS user_first_name,
            u.last_name  AS user_last_name,
            s.skill_name AS skill_name,
            r.details,
            r.request_date,
            r.work_date,
            r.work_time,
            w.first_name AS worker_first_name,
            r.user_decision,
            r.worker_status
        FROM request_master r
        JOIN user  u ON u.user_id  = r.user_id
        JOIN skill s ON s.skill_id = r.skill_id
        LEFT JOIN worker w ON w.worker_id = r.worker_id
        ORDER BY r.request_id DESC
    """
    data = select(q)
    # Compute a display value for work_place by falling back to user fields if work_place is '0' or empty
    for row in data:
        wp = row.get('work_place') if 'work_place' in row else None
        if wp in (None, '', 0, '0'):
            # fetch user record to find a sensible place field (be resilient to differing column names)
            uid = row.get('user_id') or row.get('User_id')
            user_row = None
            if uid:
                ures = select("SELECT * FROM user WHERE user_id='%s'" % uid)
                if ures:
                    user_row = ures[0]
            # prefer these keys in order
            place = None
            if user_row:
                # prefer the user's registered city first (registration stores city)
                for key in ('city','City','House_name','house_name','House','house','address','place','location'):
                    if key in user_row and user_row[key]:
                        place = user_row[key]
                        break
            row['work_place_display'] = place or '-' 
        else:
            row['work_place_display'] = wp
    # Format work_time for each row
    for row in data:
        wt = row.get('work_time')
        if wt and wt not in ('None', None):
            # If it's a timedelta, convert to string
            if hasattr(wt, 'seconds'):
                total_seconds = wt.seconds
                hour = total_seconds // 3600
                minute = (total_seconds % 3600) // 60
            else:
                # If it's a string like '07:00:00'
                parts = str(wt).split(':')
                hour = int(parts[0])
                minute = int(parts[1])
            ampm = 'AM' if hour < 12 else 'PM'
            hour12 = hour if 1 <= hour <= 12 else (hour - 12 if hour > 12 else 12)
            row['work_time'] = f"{hour12:02d}:{minute:02d} {ampm}"
        else:
            row['work_time'] = '-'
    return render_template("admin_view_requests.html",data=data)


# -------------------- APPROVE A WORKER --------------------
@admin.route('/approve_worker/<int:worker_id>')
def approve_worker(worker_id):
    # Approve the worker (no login insert required — login is created at registration)
    q = "UPDATE worker SET status='approved' WHERE worker_id='%s'" % (worker_id)
    update(q)
    return redirect(url_for('admin.approve_workers'))


# -------------------- REMOVE/DEACTIVATE A WORKER --------------------
@admin.route('/remove_worker/<int:worker_id>')
def remove_worker(worker_id):
    # Mark worker as removed/deactivated
    q = "UPDATE worker SET status='removed' WHERE worker_id='%s'" % (worker_id)
    update(q)
    return redirect(url_for('admin.approve_workers'))


# -------------------- REJECT A WORKER --------------------
@admin.route('/reject_worker/<int:worker_id>')
def reject_worker(worker_id):
    # Mark worker as rejected
    q = "UPDATE worker SET status='rejected' WHERE worker_id='%s'" % (worker_id)
    update(q)
    return redirect(url_for('admin.approve_workers'))



# -------------------- VIEW COMPLAINTS --------------------
@admin.route('/view_complaints')
def view_complaints():
    q = """
        SELECT 
            complaint.complaint_id,
            complaint.complaint,
            complaint.date_time,
            -- Show user house name if request_master.work_place is '0'
            request_master.user_id,
            CASE WHEN request_master.work_place = '0' OR request_master.work_place = 0 THEN u.House_name ELSE request_master.work_place END AS work_place_display,
            u.first_name AS user_name,
            w.first_name AS worker_name,
            request_master.work_date,
            request_master.work_time,
            request_master.details,
            skill.skill_name
        FROM complaint
        JOIN request_master ON request_master.request_id = complaint.request_master_id
        JOIN user u ON u.user_id = request_master.user_id
        JOIN worker w ON w.worker_id = request_master.worker_id
        JOIN skill ON skill.skill_id = request_master.skill_id
    """
    data = select(q)
    from datetime import datetime
    for row in data:
        # Format work place
        wp = row.get('work_place') if 'work_place' in row else None
        if wp in (None, '', 0, '0'):
            uid = row.get('user_id') or row.get('User_id')
            user_row = None
            if uid:
                ures = select("SELECT * FROM user WHERE user_id='%s'" % uid)
                if ures:
                    user_row = ures[0]
            place = None
            if user_row:
                for key in ('city','City','House_name','house_name','House','house','address','place','location'):
                    if key in user_row and user_row[key]:
                        place = user_row[key]
                        break
            row['work_place_display'] = place or '-' 
        else:
            row['work_place_display'] = wp
        # Format complaint date_time
        dt = row.get('date_time')
        if dt and dt not in ('None', None):
            try:
                if isinstance(dt, str):
                    parsed = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                else:
                    parsed = dt
                row['date_time'] = parsed.strftime('%Y-%m-%d %I:%M:%S %p')
            except Exception:
                row['date_time'] = str(dt)
    return render_template("admin_view_complaints.html", data=data)



@admin.route('/admin_reply_complaint/<cid>', methods=['GET','POST'])
def admin_reply_complaint(cid):

    if request.method == 'POST':
        reply = request.form['reply']
        q = "UPDATE complaint SET reply='%s' WHERE complaint_id='%s'" % (reply, cid)
        update(q)
        return redirect(url_for('admin.view_complaints'))

    # GET — Show page with original complaint and timestamp
    q = "SELECT complaint, date_time FROM complaint WHERE complaint_id='%s'" % cid
    res = select(q)
    complaint_text = res[0]['complaint'] if res else ''
    complaint_dt = None
    if res and 'date_time' in res[0] and res[0]['date_time']:
        raw_dt = res[0]['date_time']
        # raw_dt may already be a datetime object from the DB driver, or a string
        if isinstance(raw_dt, datetime):
            complaint_dt = raw_dt.strftime('%d-%m-%Y %I:%M %p')
        else:
            # try common string patterns
            parsed = None
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                try:
                    parsed = datetime.strptime(str(raw_dt), fmt)
                    break
                except Exception:
                    parsed = None
            if parsed:
                complaint_dt = parsed.strftime('%d-%m-%Y %I:%M %p')
            else:
                # fallback: pass raw value
                complaint_dt = str(raw_dt)

    return render_template("admin_reply_complaint.html", complaint_text=complaint_text, complaint_date_time=complaint_dt)



# -------------------- VIEW REVIEWS --------------------
@admin.route('/admin_view_review')
def admin_view_review():

    q = """
        SELECT 
            r.review_des,
            r.date AS review_date,
            u.first_name AS user_fname,
            u.last_name AS user_lname,
            w.first_name AS worker_fname,
            w.last_name AS worker_lname
        FROM review r
        JOIN user u ON r.user_id = u.user_id
        JOIN worker w ON r.worker_id = w.worker_id
    """
    data = select(q)
    # Format review_date for display
    for row in data:
        rd = row.get('review_date')
        display = None
        if rd:
            if isinstance(rd, datetime):
                display = rd.strftime('%d-%m-%Y')
            else:
                try:
                    parsed = datetime.strptime(str(rd), '%Y-%m-%d %H:%M:%S')
                    display = parsed.strftime('%d-%m-%Y')
                except Exception:
                    try:
                        parsed = datetime.strptime(str(rd), '%Y-%m-%d')
                        display = parsed.strftime('%d-%m-%Y')
                    except Exception:
                        display = str(rd)
        row['review_date_display'] = display
    return render_template("admin_view_review.html", data=data)

@admin.route('/admin_view_payments')
def admin_view_payments():

    q = """
        SELECT 
            p.payment_id,
            p.Date_time AS proposal_date_time,
            r.user_id,
            CASE WHEN r.work_place = '0' OR r.work_place = 0 THEN u.House_name ELSE r.work_place END AS work_place_display,
            r.request_date,
            r.work_date,
            r.work_time,
            p.amount,
            p.status,

            u.First_name AS user_fname,
            u.Last_name AS user_lname,

            w.First_name AS worker_fname,
            w.Last_name AS worker_lname,

            s.skill_name

        FROM proposals p
        JOIN request_master r ON p.Request_master_id = r.request_id
        JOIN user u ON r.user_id = u.user_id
        JOIN worker w ON p.Worker_id = w.worker_id
        JOIN skill s ON r.skill_id = s.skill_id
        ORDER BY p.payment_id DESC
    """
    data = select(q)
    from datetime import datetime
    for row in data:
        wp = row.get('work_place') if 'work_place' in row else None
        if wp in (None, '', 0, '0'):
            uid = row.get('user_id') or row.get('User_id')
            user_row = None
            if uid:
                ures = select("SELECT * FROM user WHERE user_id='%s'" % uid)
                if ures:
                    user_row = ures[0]
            place = None
            if user_row:
                for key in ('city','City','House_name','house_name','House','house','address','place','location'):
                    if key in user_row and user_row[key]:
                        place = user_row[key]
                        break
            row['work_place_display'] = place or '-' 
        else:
            row['work_place_display'] = wp
        # Format payment date/time
        dt = row.get('proposal_date_time')
        if dt and dt not in ('None', None):
            try:
                if isinstance(dt, str):
                    parsed = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                else:
                    parsed = dt
                row['proposal_date_time'] = parsed.strftime('%Y-%m-%d %I:%M:%S %p')
            except Exception:
                row['proposal_date_time'] = str(dt)
    return render_template('admin_view_payments.html', data=data)