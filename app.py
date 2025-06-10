from flask import Flask,render_template,url_for,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'

db=SQLAlchemy(app)

class Admin(db.Model):
    admin_ID=db.Column(db.Integer,primary_key=True,auto_increment=True)
    username=db.Column(db.String(100),nullable=False)
    password=db.Column(db.String(100),nullable=False)


class User(db.Model):
    user_ID=db.Column(db.Integer,primary_key=True,auto_increment=True)
    Username=db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(100),nullable=False)
    fullname=db.Column(db.String(200),nullable=False)
    email_ID=db.Column(db.String(200),nullable=False)
    address=db.Column(db.String(300),nullable=False)
    PinCode=db.Column(db.Integer,nullable=False)
    booking=db.relationship("Booking",backref="user",lazy=True)


class Parkinglot(db.Model):
    Lot_ID=db.Column(db.Integer,primary_key=True,auto_increment=True)
    Prime_Location_Name=db.Column(db.String(200),nullable=False,unique=True)
    Address=db.Column(db.String(300),nullable=False)
    PinCode=db.Column(db.Integer,nullable=False)
    Price=db.Column(db.Float,nullable=False)
    Maximum_spots=db.Column(db.Integer,nullable=False)
    spots=db.relationship("Spot",backref="parkinglot",lazy=True)


class Spot(db.Model):
    Lot_ID=db.Column(db.Integer,db.ForeignKey('parkinglot.Lot_ID'),nullable=False)
    Spot_ID=db.Column(db.Integer,primary_key=True,auto_increment=True)
    Status=db.Column(db.Boolean,nullable=False,default=False)
    bookings=db.relationship("Booking",backref="spot",lazy=True)


class Booking(db.Model):
    Booking_ID=db.Column(db.Integer,primary_key=True,auto_increment=True)
    user_ID=db.Column(db.Integer,db.ForeignKey('user.user_ID'),nullable=False)
    spot_ID=db.Column(db.Integer,db.ForeignKey('spot.Spot_ID'),nullable=False)
    vehicle_number=db.Column(db.String(20),nullable=False)
    booking_time=db.Column(db.DateTime, default=datetime.utcnow)
    duration=db.Column(db.Integer,nullable=False)
    cost=db.Column(db.Float,nullable=False)

    

with app.app_context():
    db.create_all()





@app.route('/')
def home():
    return render_template('index.html')


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]

        already_user=User.query.filter_by(Username=username,password=password).first()

        if already_user:
            return redirect(url_for("user_dashboard"))
        else:
            return render_template("invalid.html", errormessage="Invalid credentials for user")


    return render_template('login.html')



@app.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        admin_username=request.form["username"]
        password=request.form["password"]

        if admin_username=="iamadmin" and password=="addme":
            return redirect(url_for("admindashboard"))
        else:
            return render_template("invalid.html", errormessage="Invalid credentials for admin ")
    return render_template("admin_login.html")
    


@app.route("/registration", methods=["GET","POST"])
def registration():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]
        fullname=request.form["fullname"]
        email=request.form["email"]
        address=request.form["address"]
        pincode=request.form["pincode"]

        add_user=User(Username=username,password=password,fullname=fullname,email_ID=email,address=address,PinCode=pincode)
        db.session.add(add_user)
        db.session.commit()
        return redirect(url_for("login"))
    # on get method it opens registration page
    return render_template("registration.html")


@app.route('/admin-dashboard')
def admin_dashboard():
    lots=Parkinglot.query.all()
    return render_template("admin_dashboard.html",lots=lots)

@app.route('/registered-users')
def all_users():
    all_users=User.query.all()
    return render_template('users.html',users=all_users)


@app.route("/search-a-lot",methods=['GET','POST'])
def searching():
    lots=[]
    if request.method=='POST':
        location=request.form['lot']

@app.route("/admin-summary")
def adminsummary():
    return 0

        

if __name__=='__main__':
    app.run(debug=True)