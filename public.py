from flask import *
from database import *
import uuid
import os
from werkzeug.utils import secure_filename

public = Blueprint('public', __name__)

# -----------------------------
# HOME PAGE
# -----------------------------
@public.route('/')
def home():
    return render_template('home.html')


# -----------------------------
# LOGIN PAGE
# -----------------------------
@public.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        psw = request.form['password']

        # Use only the correct column name for login
        q = "SELECT * FROM login WHERE user_name='%s' AND password='%s'" % (uname, psw)
        res = select(q)

        if res:
            row = res[0]
            # detect login id key (login_id, Login_id, id, ID)
            lid_key = None
            for k in row.keys():
                if k.lower() == 'login_id' or k.lower() == 'loginid' or k.lower() == 'id':
                    lid_key = k
                    break
            if not lid_key:
                # fallback to first key that contains 'login' or endswith 'id'
                for k in row.keys():
                    if 'login' in k.lower() or k.lower().endswith('id'):
                        lid_key = k
                        break
            session['lid'] = row[lid_key] if lid_key else list(row.values())[0]

            # detect user type key
            type_key = None
            for k in row.keys():
                if k.lower() in ('user_type', 'usertype', 'userrole', 'type'):
                    type_key = k
                    break
            session['type'] = row[type_key] if type_key and type_key in row else row.get('user_type') if 'user_type' in row else None

            # ---------- ADMIN ----------
            if session['type'] == 'admin':
                return redirect('/admin_home')

            # ---------- USER ----------
            elif session['type'] == 'user':
                q1 = "SELECT * FROM user WHERE Login_id='%s'" % (session['lid'])
                user = select(q1)
                if user:
                    # ✅ Use the exact case from your DB: User_id
                    session['user_id'] = user[0]['User_id']
                    return redirect('/user_home')
                else:
                    return "<script>alert('User record not found.');window.location='/login'</script>"

            # ---------- WORKER ----------
            elif session['type'] == 'worker':
                q2 = "SELECT worker_id, status FROM worker WHERE login_id='%s'" % (session['lid'])
                worker_status = select(q2)

                if worker_status:
                    status = worker_status[0]['status'].lower()
                    session['worker_id'] = worker_status[0]['worker_id']  # ✅ store worker ID

                    if status == 'approved':
                        return redirect('/worker_home')
                    elif status == 'rejected':
                        return "<script>alert('Your account was rejected by the admin.');window.location='/login'</script>"
                    else:
                        return "<script>alert('Your account is pending approval.');window.location='/login'</script>"
                else:
                    return "<script>alert('Worker account not found.');window.location='/login'</script>"

        # If login invalid
        return "<script>alert('Invalid username or password');window.location='/login'</script>"

    return render_template('login.html')


# -----------------------------
# USER REGISTRATION
# -----------------------------
@public.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form['phone']
        hname = request.form['hname']
        city = request.form['city']
        po = request.form['po']
        district = request.form['district']
        uname = request.form['uname']
        psw = request.form['password']

        # Insert into login first
        q1 = "INSERT INTO login VALUES (NULL, '%s', '%s', 'user')" % (uname, psw)
        loginid = insert(q1)

        # Insert into user table
        q2 = """INSERT INTO user VALUES (
            NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
        )""" % (loginid, fname, lname, gender, email, phone, hname, city, po, district)
        insert(q2)

        return "<script>alert('Registration successful!');window.location='/login'</script>"

    return render_template('user_registration.html')


# -----------------------------
# -----------------------------
# WORKER REGISTRATION
# -----------------------------
@public.route('/workerreg', methods=['GET', 'POST'])
def workerreg():
    if request.method == 'POST':
        First_name = request.form.get('fname', '')
        Last_name = request.form.get('lname', '')
        gender = request.form.get('gender', '')
        email = request.form.get('email', '')
        Phone_no = request.form.get('phone', '')
        House_name = request.form.get('hname', '')
        city = request.form.get('city', '')
        Post_office = request.form.get('po', '')
        district = request.form.get('district', '')
        password = request.form.get('password', '')
        username = request.form.get('uname', email)

        # Prepare uploads dir
        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        # Handle profile photo
        profile_filename = ''
        photo = request.files.get('photo')
        if photo and photo.filename:
            profile_filename = str(uuid.uuid4()) + "_" + secure_filename(photo.filename)
            photo.save(os.path.join(upload_folder, profile_filename))

        # Handle licence/id proof upload
        licence_filename = ''
        licence = request.files.get('license_photo')
        if licence and licence.filename:
            licence_filename = str(uuid.uuid4()) + "_" + secure_filename(licence.filename)
            licence.save(os.path.join(upload_folder, licence_filename))

        # Insert into login table (use provided username)
        q1 = "INSERT INTO login (user_name, password, user_type) VALUES ('%s', '%s', 'worker')" % (username, password)
        loginid = insert(q1)

        # Insert into worker table — ensure column names match DB (Profile_photo, licence_photo)
        q2 = """INSERT INTO worker (
                    Login_id, First_name, Last_name, gender, email, Phone_no, House_name, city, Post_office, district, Profile_photo, licence_photo, status
                ) VALUES (
                    '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', 'pending'
                )""" % (
                   loginid, First_name, Last_name, gender, email, Phone_no, House_name, city, Post_office, district, profile_filename, licence_filename)
        insert(q2)

        return "<script>alert('Worker registered successfully! Wait for admin approval.');window.location='/login'</script>"

    return render_template('worker_registration.html')

# -----------------------------
# LOGOUT
# -----------------------------
@public.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
