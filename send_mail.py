from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'muhalibakhtiar@gmail.com'
app.config['MAIL_PASSWORD'] = '7januari1994'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/')
def index():
   msg = Message('Hello', sender='muhalibakhtiar@gmail.com',
	               recipients=['muhalibakhtiar@gmail.com'])
   msg.body = "Hello Flask message sent from Flask-Mail"
   mail.send(msg)
   return "Sent"


if __name__ == '__main__':
    app.run(debug=True)
