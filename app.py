from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import mysql.connector
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
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
def dashboard():
   return render_template('dashboard.html')


@app.route('/add_pengajuan', methods=['GET', 'POST'])
@is_logged_in
def add_pengajuan():
   if request.method == 'POST':
      judul = request.form['judul']
      dosbim = request.form['dosbim']
      # berkas = request.form['berkas']
      sinopsis = request.form['sinopsis']
      # create cursor
      cur = db.cursor(buffered=True)
      # execute query

      cur.execute("INSERT INTO pengajuan (nik,judul,dosbim,berkas,sinopsis,status) VALUES (%s,%s, %s, %s, %s, %s)",
                  (session['nik'],judul, dosbim, 1, sinopsis,'Menunggu Konfirmasi'))

      db.commit()

      cur.close()

      flash(' Pengajuan berhasil, Cek status pengajuan', 'success')

      return redirect(url_for('status'))
   return render_template('add_pengajuan.html')


@app.route('/status')
@is_logged_in
def status():
    # yang bermasalah koneksi databasenya
      cur = db.cursor(buffered=True)
      result = cur.execute("SELECT * FROM pengajuan")
      data = cur.fetchall()

      if data > 0:
         return render_template('status.html', data=data)
      else:
         msg     = 'Tidak ada Pengajuan'
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

@app.route('/dashboard_dosbim')
@is_logged_in
def dashboard_dosbim():
    # yang bermasalah koneksi databasenya
      cur = db.cursor(buffered=True)
      result = cur.execute("SELECT * FROM pengajuan")
      data = cur.fetchall()

      if data > 0:
         return render_template('dashboard_dosbim.html', data=data)
      else:
         msg     = 'Tidak ada Pengajuan'
         return render_template('dashboard_dosbim.html', msg=msg)
      # Close Connectio
      cur.close()

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
          "UPDATE pengajuan SET status=%s WHERE id = %s", ('Pengajuan di terima',id))

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
          "UPDATE pengajuan SET status=%s WHERE id = %s", ('Pengajuan di tolak',id))

      # commit to DB
      db.commit()

      # close connection
      cur.close()

      flash('Maaf Pengajuan kamu di tolak, harap melakukan pengajuan ulang kakak', 'success')

      return redirect(url_for('dashboard_dosbim'))

@app.route('/logout')
def logout():
   session.clear()
   flash('Thanks you, You are logged out', 'success')
   return redirect(url_for('index'))


app.secret_key = 'secret123'
if __name__ == '__main__':

   app.run(debug=True)
