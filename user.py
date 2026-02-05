from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
from database import select, insert, update, delete


user = Blueprint('user', __name__)

# -------------------- USER HOME --------------------
@user.route('/user_home')
def user_home():
    lid = session['lid']
    q = "SELECT first_name FROM user WHERE login_id='%s'" % lid
    res = select(q)
    user_name = res[0]['first_name'] if res else "User"
    return render_template('user_home.html', user_name=user_name)



# -------------------- REQUEST FOR WORKER --------------------
@user.route('/user_request_worker', methods=['GET', 'POST'])
def user_request_worker():
    if 'user_id' not in session:
        return redirect(url_for('public.login'))

    uid = session['user_id']

    # Handle form submission
    if 'submit' in request.form:
        skill_id = request.form['skill_id']
        work_place = request.form['work_place']
        details = request.form['details']

        q = """INSERT INTO request_master (user_id, skill_id, work_place, request_date, details, status)
               VALUES (%s, %s, %s, CURDATE(), %s, 'pending')"""
        val = (uid, skill_id, work_place, details)
        insert(q, val)
        flash('Request sent successfully!', 'success')
        return redirect(url_for('user_request_worker'))

    # Fetch all skills for dropdown or list
    data = select("SELECT * FROM skill")
    return render_template('user_request_worker.html', data=data)



    #--------user_my_request_worker------------------
@user.route('/user_my_request_worker')
def user_my_request_worker():
    user_id = session['user_id']
    q = """
        SELECT 
            r.request_id,
            r.request_date,
            r.work_date,
            r.work_time,
            r.worker_status,
            r.user_decision,
            r.status,
            s.skill_name,
            COALESCE(p.amount, 0) AS pay_amount,
            COALESCE(p.status, 'pending') AS pay_status
        FROM request_master r
        JOIN skill s ON r.skill_id = s.skill_id
        LEFT JOIN proposals p ON p.request_master_id = r.request_id
        WHERE r.user_id='%s'
        ORDER BY r.request_id DESC
        """ % (user_id)

    data = select(q)
    # Format work_time for each row
    for row in data:
        wt = row.get('work_time')
        if wt:
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
    return render_template('user_my_request_worker.html', data=data)


@user.route('/user_view_payment/<req_id>')
def user_view_payment(req_id):
    """Show one request payment details to the user."""
    q = """
        SELECT r.request_id, r.work_date, r.work_time, r.details,
               s.skill_name,
               w.First_name AS worker_fname, w.Last_name AS worker_lname,
               p.amount, p.status
        FROM request_master r
        JOIN skill s ON r.skill_id = s.skill_id
        JOIN proposals p ON p.request_master_id = r.request_id
        JOIN worker w ON p.worker_id = w.worker_id
        WHERE r.request_id='%s'
    """ % req_id
    res = select(q)
    if not res:
        flash("Payment details not found", "danger")
        return redirect('/user_my_requests_worker')

    row = res[0]
    return render_template('user_view_payment.html', row=row)


@user.route('/user_accept_payment/<int:req_id>')
def user_accept_payment(req_id):
    """User accepts work and proceeds to payment."""
    try:
        # Update request status to accepted
        q1 = "UPDATE request_master SET user_decision='accepted' WHERE request_id='%s'" % req_id
        update(q1)
        
        # Fetch payment amount from proposals
        q = "SELECT amount FROM proposals WHERE request_master_id='%s'" % req_id
        res = select(q)
        if not res:
            flash("Payment details not found", "danger")
            return redirect(url_for('user.user_my_request_worker'))
        
        amount = int(res[0]['amount'])
        # Redirect to payment page with amount as query parameters
        return redirect(f'/pay?req_id={req_id}&amount={amount}')
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('user.user_my_request_worker'))


@user.route('/user_reject_payment/<req_id>')
def user_reject_payment(req_id):
    """User rejects work / payment."""
    q1 = "UPDATE request_master SET user_decision='rejected' WHERE request_id='%s'" % req_id
    update(q1)
    q2 = "UPDATE proposals SET status='rejected' WHERE request_master_id='%s'" % req_id
    update(q2)
    flash("Work rejected.", "info")
    return redirect('/user_my_requests_worker')
#-----------------------------------#


@user.route('/user_accept/<req_id>')
def user_accept(req_id):
    q = "UPDATE request_master SET user_decision='accepted' WHERE request_id='%s'" % req_id
    update(q)
    flash("You accepted the work", "success")
    return redirect(url_for('user.user_my_request_worker'))
@user.route('/user_reject/<req_id>')
def user_reject(req_id):
    q = "UPDATE request_master SET user_decision='rejected' WHERE request_id='%s'" % req_id
    update(q)
    flash("You rejected the work", "danger")
    return redirect(url_for('user.user_my_request_worker'))

@user.route('/user_reject_assigned/<int:req_id>')
def user_reject_assigned(req_id):
    """User rejects assigned work (with proposal)."""
    try:
        q1 = "UPDATE request_master SET user_decision='rejected' WHERE request_id='%s'" % req_id
        update(q1)
        q2 = "UPDATE proposals SET status='rejected' WHERE request_master_id='%s'" % req_id
        update(q2)
        flash("Work rejected.", "danger")
    except Exception as e:
        flash(f"Error rejecting work: {str(e)}", "danger")
    return redirect(url_for('user.user_my_request_worker'))
#---------------------------#


#___________send_request/<id>_________________

@user.route('/send_request/<int:skill_id>', methods=['GET', 'POST'])
def send_request(skill_id):
    if 'lid' not in session:
        return redirect(url_for('public.login'))

    # get user id
    q_user = "SELECT user_id FROM user WHERE login_id='%s'" % session['lid']
    user_res = select(q_user)
    user_id = user_res[0]['user_id']

    # Fetch skill details
    skill_data = select("SELECT * FROM skill WHERE skill_id='%s'" % skill_id)[0]

    if request.method == 'POST':
        details = request.form['details']

        # 🔥 Find worker who has this skill
        w = select("SELECT worker_id FROM worker_skill WHERE skill_id='%s' LIMIT 1" % skill_id)

        worker_id = w[0]['worker_id'] if w else None  # If no worker -> NULL

        # Insert request with worker_id
        q2 = """INSERT INTO request_master 
                (user_id, skill_id, request_date, details, status, worker_id)
                VALUES ('%s', '%s', CURDATE(), '%s', 'pending', '%s')""" % (
                    user_id, skill_id, details, worker_id)

        insert(q2)

        return "<script>alert('Request sent successfully!');window.location='/user_my_request_worker'</script>"

    return render_template('user_request_details.html', skill=skill_data)


@user.route('/user_add_complaint', methods=['GET', 'POST'])
def user_add_complaint():
    uid = session['user_id']

    # Dropdown selection: show worker name + skill
    q1 = """
        SELECT r.request_id, s.skill_name,
               w.first_name AS wfname, w.last_name AS wlname
        FROM request_master r
        JOIN skill s ON r.skill_id = s.skill_id
        LEFT JOIN worker w ON r.worker_id = w.worker_id
        WHERE r.user_id='%s'
    """ % uid
    works = select(q1)

    if request.method == "POST":
        req_id = request.form['request_id']
        text = request.form['complaint_text']

        # store date_time as NOW() so complaint timestamps are available for display
        q2 = "INSERT INTO complaint (request_master_id, complaint, date_time) VALUES ('%s','%s', NOW())" % (req_id, text)
        insert(q2)
        flash("Complaint submitted", "success")
        return redirect(url_for("user.user_add_complaint"))

    # Load existing complaints for user
    q3 = """
        SELECT c.complaint, c.reply,
               s.skill_name,
               w.first_name, w.last_name
        FROM complaint c
        JOIN request_master r ON c.request_master_id=r.request_id
        JOIN skill s ON r.skill_id=s.skill_id
        LEFT JOIN worker w ON r.worker_id = w.worker_id
        WHERE r.user_id='%s'
        ORDER BY c.complaint_id DESC
    """ % uid
    complaints = select(q3)

    return render_template("user_add_complaint.html", works=works, complaints=complaints)

@user.route('/user_add_review', methods=['GET', 'POST'])
def user_add_review():
    uid = session['user_id']

    # Select all worker interactions of the user
    q1 = """
        SELECT r.request_id, w.worker_id, w.first_name, w.last_name, s.skill_name
        FROM request_master r
        JOIN worker w ON r.worker_id=w.worker_id
        JOIN skill s ON r.skill_id=s.skill_id
        WHERE r.user_id='%s' AND r.worker_id IS NOT NULL
    """ % uid
    works = select(q1)

    if request.method == "POST":
        req_id = request.form['request_id']
        review_text = request.form['review_text']

        q3 = "SELECT worker_id FROM request_master WHERE request_id='%s'" % req_id
        result = select(q3)
        wid = result[0]['worker_id']

        # include date timestamp so reviews show when they were submitted
        q3 = "INSERT INTO review (user_id, worker_id, Review_des, date) VALUES ('%s','%s','%s', NOW())" % (uid, wid, review_text)
        insert(q3)

        flash("Review submitted successfully", "success")
        return redirect(url_for('user.user_add_review'))

    return render_template("user_add_review.html", works=works)

import razorpay

@user.route("/pay")
def pay():
    req_id = request.args.get('req_id')
    amount = request.args.get('amount', 200)
    
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        amount = 200
    
    KEY_ID = "rzp_test_ZMGzPbvu5L6Y8v"
    KEY_SECRET = "CcHnHJcgxJd4LE10jCrAWx5x"

    try:
        client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
        order = client.order.create({
            "amount": amount * 100,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as e:
        flash(f"Payment error: {str(e)}", "danger")
        return redirect('/user_my_request_worker')

    return render_template(
        "payment.html",
        key_id=KEY_ID,
        amount=amount,
        order_id=order['id'],
        request_id=req_id
    )

@user.route("/payment_success/<int:req_id>")
def payment_success(req_id):
    # Update request status to paid
    q1 = "UPDATE request_master SET user_decision='paid', status='paid' WHERE request_id='%s'" % req_id
    update(q1)
    # Update proposals status to paid and set Date_time to NOW()
    q2 = "UPDATE proposals SET status='paid', Date_time=NOW() WHERE request_master_id='%s'" % req_id
    update(q2)
    flash("Payment Completed Successfully!", "success")
    return redirect(url_for('user.user_my_request_worker'))



@user.route('/view_payment/<req_id>')
def view_payment(req_id):
    q = """
        SELECT 
            r.work_date,
            r.work_time,
            s.skill_name,
            p.amount
        FROM request_master r
        JOIN skill s ON r.skill_id = s.skill_id
        LEFT JOIN proposals p ON p.request_master_id = r.request_id
        WHERE r.request_id = '%s'
    """ % req_id

    res = select(q)
    if res:
        return render_template("view_payment.html", data=res[0])
    else:
        flash("No payment info found", "warning")
        return redirect(url_for('user.user_my_request_worker'))