from flask import Flask,render_template,url_for,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'

db=SQLAlchemy(app)

class Admin(db.Model):
    admin_ID=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String(100),nullable=False)
    password=db.Column(db.String(100),nullable=False)


class User(db.Model):
    user_ID=db.Column(db.Integer,primary_key=True,autoincrement=True)
    Username=db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(100),nullable=False)
    fullname=db.Column(db.String(200),nullable=False)
    email_ID=db.Column(db.String(200),nullable=False)
    address=db.Column(db.String(300),nullable=False)
    PinCode=db.Column(db.Integer,nullable=False)
    booking=db.relationship("Booking",backref="user",lazy=True)


class Parkinglot(db.Model):
    Lot_ID=db.Column(db.Integer,primary_key=True,autoincrement=True)
    Prime_Location_Name=db.Column(db.String(200),nullable=False,unique=True)
    Address=db.Column(db.String(300),nullable=False)
    PinCode=db.Column(db.Integer,nullable=False)
    Price=db.Column(db.Float,nullable=False)
    Maximum_spots=db.Column(db.Integer,nullable=False)
    spots=db.relationship("Spot",backref="parkinglot",lazy=True)


class Spot(db.Model):
    Lot_ID=db.Column(db.Integer,db.ForeignKey('parkinglot.Lot_ID'),nullable=False)
    Spot_ID=db.Column(db.Integer,primary_key=True,autoincrement=True)
    Status=db.Column(db.Boolean,nullable=False,default=False)
    bookings=db.relationship("Booking",backref="spot",lazy=True)


class Booking(db.Model):
    Booking_ID=db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_ID=db.Column(db.Integer,db.ForeignKey('user.user_ID'),nullable=False)
    spot_ID=db.Column(db.Integer,db.ForeignKey('spot.Spot_ID'),nullable=False)
    vehicle_number=db.Column(db.String(20),nullable=False)
    booking_time=db.Column(db.DateTime, default=datetime.utcnow)
    duration=db.Column(db.Integer,nullable=False)
    cost=db.Column(db.Float,nullable=False)

    

app.app_context().push()
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


    return render_template('user_login.html')

@app.route("/user-dashboard",methods=["GET","POST"])
def user_dashboard():
    return render_template('user_dashboard')



@app.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        admin_username=request.form["username"]
        password=request.form["password"]

        if admin_username=="iamadmin" and password=="addme":
            return redirect(url_for("admin_dashboard"))
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


        already_users=User.query.filter((User.Username==username)|(User.email_ID==email)).first()
        if already_users:
            return render_template("invalid.html",errormessage="User already registered with this credentials")

        add_user=User(Username=username,password=password,fullname=fullname,email_ID=email,address=address,PinCode=pincode)
        db.session.add(add_user)
        db.session.commit()
        return redirect(url_for("login"))
    # on get method it opens registration page
    return render_template("registration.html")


@app.route('/admin-dashboard')
def admin_dashboard():
    lots=Parkinglot.query.all()
    occupied_lots=[]
    for lot in lots:
        occupied_lot =Spot.query.filter_by(Lot_ID=lot.Lot_ID,Status=True).count()
        occupied_lots.append({
            "parking_lot":lot,
            "occupied":occupied_lot,
            "total":lot.Maximum_spots
            
        })
    return render_template("admin_dashboard.html",lots=occupied_lots)

@app.route('/registered-users')
def all_users():
    all_users=User.query.all()
    return render_template('users.html',users=all_users) #iss pure route par kaam karna h


@app.route("/search-a-lot",methods=['GET','POST'])  # iss pure route par bhi kaam karna h
def searching():
    type=request.form["SEARCH_BY"]
    string=request.form["search_string"]

    queriedspot=[]
    querieduser=[]
    if type=="location":
        filtered=Parkinglot.query.filter(Parkinglot.Prime_Location_Name.ilike(f"%{string}%")).all()
        for i in filtered:
            j=Spot.query.filter_by(Lot_ID=i.Lot_ID, Status=True).count()
            queriedspot.append({
                "parking_lot":i,
                "occupied":j,
                "total":i.Maximum_spots
            })
    elif type=="parking_lot":
        filtered=Parkinglot.query.filter_by(Lot_ID=string).first()
        if filtered:
            j=Spot.query.filter_by(Lot_ID=filtered.Lot_ID,Status=True).count()
            queriedspot.append({
                "parking_lot":filtered,
                "occupied":j,
                "total":filtered.Maximum_spots
            })
    elif type=="user_id":
        filtered=User.query.filter_by(user_ID=string).first()
        if filtered: # agar ye nhi ho to isko bhi handle karna hoga
            querieduser.append({
                "ID":filtered.user_ID,
                "Email":filtered.email_ID,
                "Fullname":filtered.fullname,
                "address":filtered.address,
                "pincode":filtered.PinCode
            })
    elif type=="email_ID":
        filtered=User.query.filter_by(email_ID=string).first()
        if filtered:
            querieduser.append({
                "ID":filtered.user_ID,
                "Email":filtered.email_ID,
                "Fullname":filtered.fullname,
                "address":filtered.address,
                "pincode":filtered.PinCode
            })
    elif type=="username":
        filtered=User.query.filter_by(Username=string).first()
        if filtered:
            querieduser.append({
                "ID":filtered.user_ID,
                "Email":filtered.email_ID,
                "Fullname":filtered.fullname,
                "address":filtered.address,
                "pincode":filtered.PinCode
            })
    elif type=="pincode":
        filtered=User.query.filter_by(PinCode=string).all()
        for i in filtered:
            querieduser.append({
                "ID":i.user_ID,
                "Email":i.email_ID,
                "Fullname":i.fullname,
                "address":i.address,
                "pincode":i.PinCode
            })
    elif type=="fullname":
        filtered=User.query.filter_by(fullname=string).all()
        for i in filtered:
            querieduser.append({
                "ID":i.user_ID,
                "Email":i.email_ID,
                "Fullname":i.fullname,
                "address":i.address,
                "pincode":i.PinCode
            })
    return render_template('searching.html',spots=queriedspot,users=querieduser)

# <option value="location">Location</option>
#                 <option value="user_id">User ID</option>
#                 <option value="parking_lot">Parking lot ID</option>
#                 <option value="email_ID">Email ID</option>
#                 <option value="username">Username</option>
#                 <option value="pincode">Pincode</option>
#                 <option value="fullname">Full Name</option>

@app.route("/admin-summary") # iss route par bhi kaam karna h
def adminsummary():
    return 0

@app.route("/admin-profile")
def admin_profile():
    return 0
@app.route("/add-lot")
def add_lot():
    return 0

if __name__=='__main__':
    app.run(debug=True)