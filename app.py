import os
from flask import Flask, flash, request, redirect, url_for,render_template, session, url_for
from werkzeug.utils import secure_filename
import cv2
import json
from datetime import datetime
from flask_mongoengine import MongoEngine
import urllib.parse
from werkzeug.security import generate_password_hash, check_password_hash, gen_salt
import urllib

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'the random string'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Mongodb Database Connection Use localHost
name = 'editing'
username = urllib.parse.quote_plus('name')
app.secret_key = 'the random string'
app.config['MONGODB_SETTINGS'] = {
    'db': name,
    'host': 'mongodb://localhost:27017/'+name,
# database connection name
}
db = MongoEngine()
db1 = MongoEngine()
db.init_app(app)
db1.init_app(app)

class ContactForm(db.Document):
    name = db.StringField(required=True)
    email = db.EmailField(required=True)
    message = db.StringField(required=True)

class users(db.Document):
    username = db.StringField()
    email = db.StringField()
    phone = db.StringField()
    profession = db.StringField()
    password = db.StringField()
    rpassword = db.StringField()
    registered_Date = db.DateTimeField(default=datetime.now)

# Login Function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        _username = request.form['email']
        _password = request.form['password']
        users1 = users.objects(email=_username).count()
        if users1 > 0:
            users_response = users.objects(email=_username).first()
            password = users_response['password']

            if check_password_hash(password, _password):
                session['logged_in'] = users_response['username']
                flash('You were logged In')
                return redirect(url_for('home'))
            else:
                error = "Invalid Login / Check Your Username And Password"
                return render_template('login.html', errormsg=error)
        else:
            error = "No User Exists"
            return render_template('login.html', errormsg=error)
    return render_template('login.html')


# Signup Function
@app.route('/signup', methods=['GET', 'POST'])
def register():

    today = datetime.today()

    if request.method == 'POST':
        _username = request.form['uname']
        _email = request.form['email']
        _phone = request.form['phone']
        _profession = request.form['phone']
        _password = request.form['password']
        _rpassword = request.form['rpassword']
        if _email and _username and _password:
            hashed_password = generate_password_hash(_password)
            users1 = users.objects(email=_email)
            if not users1:
                usersave = users(username=_username, email=_email, profession=_profession, phone=_phone,
                                password=hashed_password, rpassword=hashed_password, registered_Date=today)
                usersave.save()
                msg = '{"html":"OKay you have registered"}'
                msghtml = json.loads(msg)
                return msghtml["html"] and redirect('/login')
            else:
                msg = f"It seems that {_email} You have already Registered"
            
                return render_template('signup.html',msg=msg)
        else:
            msg="Please enter email address & required details"
            render_template("signup.html", msg=msg)
    return render_template("signup.html")


# logout Function
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were Logout Out Sucessfully')

    return redirect('/')

#Submit Function
@app.route('/submit_contact_form', methods=['POST'])
def submit_contact_form():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Create a new ContactForm document and save it to MongoDB
        contact_form = ContactForm(name=name, email=email, message=message)
        contact_form.save()

        return 'Form submitted successfully!'

    return 'Invalid request'
#Allowed File Extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
#Procssing Images
def processImage(filename,operation):
    print(f"the opeartion is {operation} and the filename is {filename}")
    img=cv2.imread(f"uploads/{filename}")
    match operation:
        case "cgray":
            newFilename=f"static/{filename}"
            imgProcessed=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            cv2.imwrite(newFilename, imgProcessed)
            return newFilename
        case "cinvert":
            new_filename = f"static/{filename.split('.')[0]}_inverted.jpg"
            img_processed = cv2.bitwise_not(img)
            cv2.imwrite(new_filename, img_processed)
            return new_filename
        case "cblur":
            new_filename = f"static/{filename.split('.')[0]}_blurred.jpg"
            img_processed = cv2.GaussianBlur(img, (15, 15), 0)
            cv2.imwrite(new_filename, img_processed)
            return new_filename
        case "cedges":
            new_filename = f"static/{filename.split('.')[0]}_edges.jpg"
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_edges = cv2.Canny(img_gray, 100, 200)
            cv2.imwrite(new_filename, img_edges)
            return new_filename
        case "cwebp":
            newFilename=f"static/{filename.split('.')[0]}.webp"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cjpg":
            newFilename=f"static/{filename.split('.')[0]}.jpg"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cpng":
            newFilename=f"static/{filename.split('.')[0]}.png"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cbmp":
            new_filename = f"static/{filename.split('.')[0]}.bmp"
            cv2.imwrite(new_filename, img)
            return new_filename
        case "ctiff":
            new_filename = f"static/{filename.split('.')[0]}.tiff"
            cv2.imwrite(new_filename, img)
            return new_filename
        
    pass

@app.route('/')
def home():
   return render_template ("index.html")

@app.route('/about')
def about():
   return render_template ("about.html")

@app.route('/contact')
def contact():
   return render_template ("contact.html")

@app.route('/edit' ,methods=["GET","POST"] )
def edit():
    if request.method == 'POST':
        operation=request.form.get("operation")
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return "error"
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return "No file found"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new=processImage(filename,operation)
            flash(f"Your image has been processed and is available <a href='/{new}' target='_blank'>here.</a>")
            return render_template ("index.html")
    return render_template ("index.html")
 
if __name__ == '__main__':
   app.run(debug=True)