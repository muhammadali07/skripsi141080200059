from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import mysql.connector
from passlib.hash import sha256_crypt


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
         return render_template('add_pengajuan.html')
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

@app.route('/add_pengajuan',methods=['GET', 'POST'])
def add_pengajuan():
   if request.method == 'POST':
      judul = request.form['judul']
      kaprodi = request.form['kaprodi']
      dosbim = request.form['dosbim']
      abstrak = request.form['abstrak']
      # create cursor
      cur = db.cursor(buffered=True)
      # execute query

      cur.execute("INSERT INTO pengajuan (judul, kaprodi, dosbim, username, abstrak, nik) VALUES (%s, %s, %s, %s, %s, %s)",(judul, kaprodi, dosbim, session['nik'], abstrak, 2))

      db.commit()

      cur.close()

      cur = db.cursor(buffered=True)

      nik = session['nik']
      result=cur.execute("SELECT * FROM pengajuan WHERE nik = %s",[nik])
      data = cur.fetchall()

      if result > 0:
         return render_template('add_pengajuan.html', data=data)
      else:
         msg = 'No Articles Found'
         return render_template('add_pengajuan.html', msg=msg)

      # commit to DB
      db.commit()
      # close connection
      cur.close()

      flash(' Pengajuan berhasil, Cek status pengajuan', 'success')

      return redirect(url_for('add_pengajuan'))
   return render_template('add_pengajuan.html')

def is_logged_in(f):
   @wraps(f)
   def wrap(*args, **kwargs):
      if 'logged_in' in session:
         return f(*args, **kwargs)
      else:
         flash('Unauthorized, Please Log In', 'danger')
         return redirect(url_for('login'))
   return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      # Get Form Field
      nik = request.form['nik']
      password_candidate = request.form['password']
      # password = request.form['password']
      # Create Cursor
      cur = db.cursor(buffered=True)

      # Get user by username
      sSql = ''' SELECT nik, password, level FROM users WHERE nik = '{0}' '''.format(nik,)
      result = cur.execute(sSql)
      data = cur.fetchone()

      if data :
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
         else :
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


app.secret_key = 'secret123'
if __name__ == '__main__':

   app.run(debug=True)
