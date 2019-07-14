from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import mysql.connector
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug import secure_filename
import os

UPLOAD_FOLDER = 'static/path/to/the/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'jsbcfsbfjefebw237u3gdbdc'

config = {
    'user': 'root',
    'password': 'root',
    'unix_socket': '/Applications/MAMP/tmp/mysql/mysql.sock',
    'database': 'myflaskapp',
    'raise_on_warnings': True,
}

db = mysql.connector.connect(**config)


@app.route('/')
def index():
   if 'nik' in session:
      nik_session = session['nik']
      if session['level'] == 1:
         cur = db.cursor(buffered=True)
         cur.execute("SELECT * FROM users WHERE nik=%s",
                     [nik_session])
         rows = cur.fetchall()
         return redirect(url_for('dashboard_dosbim'))
      elif session['level'] == 2:
         cur = db.cursor(buffered=True)
         cur.execute("SELECT * FROM users WHERE nik=%s",
                     [nik_session])
         rows = cur.fetchall()
         return render_template('dashboard.html')
      elif session['level'] == 3:
         cur = db.cursor(buffered=True)
         cur.execute("SELECT * FROM users WHERE nik=%s",
                     [nik_session])
         rows = cur.fetchall()
         return render_template('dashboard_admin.html')
      else:
         return render_template("eror.html")
   else:
      return render_template('login.html')


def is_logged_in(f):
   @wraps(f)
   def wrap(*args, **kwargs):
      if 'logged_in' in session:
         return f(*args, **kwargs)
      else:
         flash('Login Tidak Sah, Silahkan Login dengar benar', 'danger')
         return redirect(url_for('login'))
   return wrap


@app.route('/dashboard')
@is_logged_in
def dashboard():
   return render_template('dashboard.html')


def allowed_file(filename):
   return '.' in filename and \
          filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_pengajuan', methods=['GET', 'POST'])
@is_logged_in
def add_pengajuan():
   cur = db.cursor(buffered=True)

   # get article
   result = cur.execute("SELECT * FROM dosen")
   data = cur.fetchall()

   if request.method == 'POST':
      judul = request.form['judul']
      dosbim = request.form['dosbim']
      file = request.files['file']
      sinopsis = request.form['sinopsis']

      if file and allowed_file(file.filename):
         filename = secure_filename(file.filename)
         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      # create cursor
      cur = db.cursor(buffered=True)
      # execute query

      cur.execute("INSERT INTO pengajuan (nik,judul,dosbim,file,sinopsis,status) VALUES (%s,%s, %s, %s, %s, %s)",
                  (session['nik'], judul, dosbim, filename, sinopsis, 'Menunggu Konfirmasi Dosen'))

      db.commit()

      cur.close()

      flash(' Pengajuan berhasil, Cek status pengajuan', 'success')

      return redirect(url_for('status'))
   return render_template('add_pengajuan.html', data=data)


@app.route('/status')
@is_logged_in
def status():
   # yang bermasalah koneksi databasenya
   cur = db.cursor(buffered=True)
   nik = session['nik']
   result = cur.execute("SELECT * FROM pengajuan WHERE nik=%s", [nik])
   data = cur.fetchall()

   if data > 0:
      return render_template('status.html', data=data)
   else:
      msg = 'Tidak ada Pengajuan'
      return render_template('status.html', msg=msg)
   # Close Connectio
   cur.close()


@app.route('/edit_pengajuan/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_pengajuan(id):
   # create cursor
   cur = db.cursor(buffered=True)

   # get article by id
   result = cur.execute("SELECT * FROM pengajuan WHERE id = %s", [id])
   data = cur.fetchall()

   if request.method == 'POST':
      judul = request.form['judul']
      dosbim = request.form['dosbim']
      sinopsis = request.form['sinopsis']

      # create cursor
      cur = db.cursor(buffered=True)

      # execute
      cur.execute(
          "UPDATE pengajuan SET judul=%s, dosbim=%s, sinopsis=%s WHERE id = %s", (judul, dosbim, sinopsis, id))

      # commit to DB
      db.commit()

      # close connection
      cur.close()

      flash('Update Berhasil', 'success')

      return redirect(url_for('status'))
   return render_template('edit.html', data=data)


@app.route('/delete_pengajuan/<string:id>', methods=['POST'])
def delete_pengajuan(id):
   # create cursor
   cur = db.cursor(buffered=True)

   # execute
   cur.execute("DELETE FROM pengajuan WHERE id = %s", [id])

   # commit DB
   db.commit()

   # close connection
   cur.close()

   flash('Pengajuan di Hapus', 'success')

   return redirect(url_for('status'))


@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      # Get Form Field
      nik = request.form['nik']
      password_candidate = request.form['password']
      # Create Cursor
      cur = db.cursor(buffered=True)

      # Get user by username
      sSql = ''' SELECT nik, password, level FROM users WHERE nik = '{0}' '''.format(
          nik,)
      result = cur.execute(sSql)
      data = cur.fetchone()

      if data:
         # Get stored hash
         qNik = data[0]
         qPassword = data[1]
         qLvel = data[2]
         # Compare Passwords

         if sha256_crypt.verify(password_candidate, qPassword):
            # Passed
            session['logged_in'] = True
            session['nik'] = qNik
            session['level'] = qLvel

            flash('you are now logged', 'success')
            return redirect(url_for('index'))
         else:
            error = 'Invalid Password'
            return render_template('login.html', error=error)

         # close connection
         cur.close()
      else:
         error = 'Username not found'

         return render_template('login.html', error=error)
   return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
   # form = RegisterForm(request.form)
   if request.method == 'POST':
      name = request.form['name']
      nik = request.form['nik']
      username = request.form['name']
      password = sha256_crypt.encrypt(str(request.form['password']))

      # create cursor
      cur = db.cursor(buffered=True)

      # execute query
      cur.execute("INSERT INTO users (name, NIK, username, password, level) VALUES (%s, %s, %s, %s, %s)",
                  (name, nik, username, password, 2))

      # commit to DB
      db.commit()

      # close connection
      cur.close()

      flash(' you are registed and you can Log in', 'success')

      return redirect(url_for('login'))
   return render_template('login.html')

# dosbim area
@app.route('/dashboard_dosbim')
@is_logged_in
def dashboard_dosbim():
   # yang bermasalah koneksi databasenya
   cur = db.cursor(buffered=True)
   # dosbim = session['dosbim']
   result = cur.execute("SELECT * FROM pengajuan")
   data = cur.fetchall()

   if data > 0:
      return render_template('dashboard_dosbim.html', data=data)
   else:
      msg = 'Tidak ada Pengajuan'
      return render_template('dashboard_dosbim.html', msg=msg)
   # Close Connectio
   cur.close()

# admin area
@app.route('/dashboard_admin')
def dashboard_admin():

    cur = db.cursor(buffered=True)

    result = cur.execute("SELECT * FROM dosen")
    data = cur.fetchall()

    if data > 0:
       return render_template('dashboard_admin.html', data=data)
    else:
       msg = 'Tidak ada Pengajuan'
       return render_template('dashboard_admin.html', msg=msg)
    # Close Connectio
    cur.close()


@app.route('/add_data_dosen', methods=['GET', 'POST'])
def add_data_dosen():
   if request.method == 'POST':
      nik_dosen = request.form['nik_dosen']
      dosbim = request.form['dosbim']
      alamat = request.form['alamat']
      telp = request.form['telp']
      fakultas = request.form['fakultas']
      email_dosbim = request.form['email_dosbim']
      pend_terakhir = request.form['pend_terakhir']
      prodi = request.form['prodi']
      bid_ilmu = request.form['bid_ilmu']
      spesialisasi = request.form['spesialisasi']
      bhs_program = request.form['bhs_program']

      # create cursor
      cur = db.cursor(buffered=True)

      cur.execute("INSERT INTO dosen (nik_dosen,dosbim,alamat,telp,fakultas,email_dosbim,pend_terakhir,prodi,bid_ilmu,spesialisasi,bhs_program) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )",
                  (nik_dosen,dosbim,alamat,telp,fakultas,email_dosbim,pend_terakhir,prodi,bid_ilmu,spesialisasi,bhs_program))
      # commit to DB
      db.commit()

      # close connection
      cur.close()

      flash(' Data Dosen Berhasil di Tambahkan', 'success')

      return redirect(url_for('dashboard_admin'))
   return render_template('add_data_dosen.html')

# tanya-jawab


@app.route('/tanya/<string:id>', methods=['GET', 'POST'])
def tanya(id):
   # create cursor
   cur = db.cursor(buffered=True)

   # get article by id
   result = cur.execute("SELECT * FROM pengajuan WHERE id = %s", [id])
   data = cur.fetchall()

   if request.method == 'POST':
      judul = request.form['judul']
      dosbim = request.form['dosbim']
      chat = request.form['chat']

      # create cursor
      cur = db.cursor(buffered=True)

      # execute
      cur.execute("INSERT INTO chat (judul, nik, dosbim, chat) VALUES (%s, %s, %s, %s)",
                  (judul, session['nik'], dosbim, chat))

      # commit to DB
      db.commit()

      # close connection
      cur.close()

      flash('Pertanyaan di ajukan', 'success')

      return redirect(url_for('dashboard'))
   return render_template('tanya.html', data=data)


@app.route('/approve/<string:id>', methods=['GET', 'POST'])
def approve(id):
      # create cursor
   cur = db.cursor(buffered=True)

   # execute
   cur.execute(
       "UPDATE pengajuan SET status=%s WHERE id = %s", ('Pengajuan di terima', id))

   # commit to DB
   db.commit()

   # close connection
   cur.close()

   flash('Approve Berhasil', 'success')

   return redirect(url_for('dashboard_dosbim'))


@app.route('/decline/<string:id>', methods=['GET', 'POST'])
def decline(id):
   # create cursor
   cur = db.cursor(buffered=True)

   # execute
   cur.execute(
       "UPDATE pengajuan SET status=%s WHERE id = %s", ('Pengajuan di tolak', id))

   # commit to DB
   db.commit()

   # close connection
   cur.close()

   flash('Maaf Pengajuan kamu di tolak, harap melakukan pengajuan ulang kakak', 'success')

   return redirect(url_for('dashboard_dosbim'))


@app.route('/chat')
def chat():
   # yang bermasalah koneksi databasenya
   cur = db.cursor(buffered=True)
   result = cur.execute("SELECT * FROM chat ORDER BY register_date DESC")
   data = cur.fetchall()

   if data > 0:
      return render_template('chat.html', data=data)
   else:
      msg = 'Tidak ada Pengajuan'
      return render_template('chat.html', msg=msg)
   # Close Connectio
   cur.close()


@app.route('/logout')
def logout():
   session.clear()
   flash('Thanks you, You are logged out', 'success')
   return redirect(url_for('index'))


app.secret_key = 'secret123'
if __name__ == '__main__':

   app.run(debug=True)
