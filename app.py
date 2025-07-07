from flask import Flask,render_template,url_for,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt
# est. cost ka bhi karna h kuch
# user profile bhi karni h

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'
app.secret_key='vinod#kumar222'


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
    booking_time=db.Column(db.DateTime, default=datetime.now())
    duration=db.Column(db.Float,nullable=False)
    cost=db.Column(db.Float,nullable=False)

    

app.app_context().push()
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        default=Admin(admin_ID=1,username="iamadmin",password="addme")
        db.session.add(default)
        db.session.commit()





@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user_searching',methods=["POST","GET"])
def user_searching():
    if request.method=="POST":

        type=request.form["SEARCH_BY"]
        string=request.form["search_string"]

        queriedlot=[]
        if type=="location":
            filtered=Parkinglot.query.filter(Parkinglot.Prime_Location_Name.ilike(f"%{string}%")).all()
            for i in filtered:
                j=Spot.query.filter_by(Lot_ID=i.Lot_ID, Status=True).count()
                available=Spot.query.filter_by(Lot_ID=i.Lot_ID,Status=False).first()
                queriedlot.append({
                    "parking_lot":i,
                    "occupied":j,
                    "total":i.Maximum_spots,
                    "available":available
                })
        elif type=="pincode":
            filtered=Parkinglot.query.filter_by(PinCode=int(string)).all()
            for i in filtered:
                j=Spot.query.filter_by(Lot_ID=i.Lot_ID, Status=True).count()
                available=Spot.query.filter_by(Lot_ID=i.Lot_ID,Status=False).first()

                queriedlot.append({
                    "parking_lot":i,
                    "occupied":j,
                    "total":i.Maximum_spots,
                    "available":available
                })
    
        return render_template('user_searching.html',lots=queriedlot)
    
    return redirect(url_for('user_dashboard'))




@app.route('/user_booking/<int:spot_id>',methods=['GET','POST'])
def user_booking(spot_id):
    spot=Spot.query.get_or_404(spot_id)
    lot=spot.parkinglot
    user_id=session.get('user_id')
    if request.method=='POST':
        vehicle_no=request.form['vehicle_number']
        booking=Booking(user_ID=user_id,spot_ID=spot.Spot_ID,vehicle_number=vehicle_no,booking_time=datetime.now(),duration=0,cost=0)
        spot.Status=True
        db.session.commit()
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for('user_dashboard'))
    return render_template('user_booking.html',spot=spot,lot=lot,user_id=user_id)

@app.route('/release/<int:booking_id>',methods=['GET','POST'])
def release_spot(booking_id):
    booking=Booking.query.get_or_404(booking_id)
    
    
    release_time=datetime.now()
    duration=((release_time-booking.booking_time).total_seconds())/3600
    price=(booking.spot.parkinglot.Price)
    cost=duration*price
    if request.method=='POST':
        booking.duration=duration
        booking.cost=cost
        booking.spot.Status=False
        db.session.commit()
        return redirect(url_for('user_dashboard'))
    return render_template('release_spot.html',booking=booking,now=datetime.now,cost=cost)

@app.route('/delete/<int:id>',methods=["GET","POST"])
def delete(id):
    lot=Parkinglot.query.get_or_404(id)
    for i in lot.spots:
        if i.Status==True:
            return render_template('invalid.html',errormessage="All the spots must be Unoccupied",back='admin_dashboard')
            
    for i in lot.spots:
            db.session.delete(i)
    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/edit/<int:id>',methods=["GET","POST"])
def edit(id):
    lot=Parkinglot.query.get(id)
    if request.method=="POST":
        lot.Prime_Location_Name=request.form['location']
        lot.Address=request.form['Address']
        lot.PinCode=request.form['Pincode']
        lot.Price=request.form['Price']
        lot.Maximum_spots=request.form['maximum_spots']


        # in case admin changes Maximum_spots then existing spots need to be deleted
        spots_count=Spot.query.filter_by(Lot_ID=lot.Lot_ID).count()

        if int(lot.Maximum_spots)>spots_count:
            for i in range(int(lot.Maximum_spots)-spots_count):
                new_spot=Spot(Lot_ID=lot.Lot_ID,Status=False)
                db.session.add(new_spot)
        elif int(lot.Maximum_spots)< spots_count:
            delete_spot=Spot.query.filter_by(Lot_ID=lot.Lot_ID,Status=False).all()
            nonbooked=[i for i in delete_spot if not i.bookings]
            if len(nonbooked)<(spots_count-int(lot.Maximum_spots)):
                return render_template("invalid.html",errormessage="Can not delete occupied spots",back="admin_dashboard")
            for i in nonbooked[ :spots_count-int(lot.Maximum_spots)]:
                db.session.delete(i)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template('edit.html',lot=lot)


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]

        already_user=User.query.filter_by(Username=username,password=password).first()

        if already_user:
            session['user_id']=already_user.user_ID
            return redirect(url_for("user_dashboard"))
        else:
            return render_template("invalid.html", errormessage="Invalid credentials for user",back="home")


    return render_template('user_login.html')

@app.route("/user-dashboard",methods=["GET","POST"])
def user_dashboard():
    userid=session.get('user_id')
    if userid:
        bookings=Booking.query.filter_by(user_ID=userid).order_by(Booking.booking_time.desc()).all()
        return render_template('user_dashboard.html',bookings=bookings)


    return render_template('user_dashboard.html')


# lots=Parkinglot.query.all()
#     occupied_lots=[]
#     for lot in lots:
#         occupied_lot =Spot.query.filter_by(Lot_ID=lot.Lot_ID,Status=True).count()
#         occupied_lots.append({
#             "parking_lot":lot,
#             "occupied":occupied_lot,
#             "total":lot.Maximum_spots
            
#         })
#     return render_template("admin_dashboard.html",lots=occupied_lots)




@app.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        admin_username=request.form["username"]
        password=request.form["password"]

        admin=Admin.query.filter_by(username=admin_username,password=password).first()
        if admin:
            session['admin_id']=admin.admin_ID
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("invalid.html", errormessage="Invalid credentials for admin ")
    return render_template("admin_login.html")
    
@app.route("/admin-profile",methods=["GET","POST"])
def admin_profile():
    admin=Admin.query.get(session['admin_id'])
    if request.method=="POST":
        admin.username=request.form['username']
        admin.password=request.form['password']
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template('admin_profile.html',admin=admin)

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
        return redirect(url_for("home"))
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
    return render_template('users.html',users=all_users)


@app.route("/searching",methods=['GET','POST'])  # iss pure route par bhi kaam karna h
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
    return render_template('searching.html',spots=queriedspot,users=querieduser)  # it should be lot



@app.route("/admin-summary") # iss route par bhi kaam karna h
def adminsummary():

    # pie chart h ye
    lots=Parkinglot.query.all()
    label=[] 
    data=[]
    for i in lots:
        lot_revenue=0
        spots=Spot.query.filter_by(Lot_ID=i.Lot_ID).all()
        for j in spots:
            bookings=Booking.query.filter_by(spot_ID=j.Spot_ID).all()

            for k in bookings:
                lot_revenue+=k.cost
        label.append(i.Prime_Location_Name)
        data.append(lot_revenue)
    if sum(data)>0:
        plt.figure(figsize=(5,5))
        plt.pie(data,labels=label)
        plt.title('Revenue from each parking lot')
        plt.savefig("static/revenue.png")
        plt.close()
    else:
        plt.figure(figsize=(5,5))
        plt.text(0.5,0.5,'No revenue generated',fontsize=14,ha='center',va='center')
        plt.axis('off')
        plt.savefig("static/revenue.png")
        plt.close()
        
    #now calculating the total
    total=0
    for i in data:
        total+=i


# ab bar chart --- stacked
    available=[]
    occupied=[]
    for i in lots:
        spots=Spot.query.filter_by(Lot_ID=i.Lot_ID).all()
        a=0
        o=0
        for j in spots:
            if j.Status:
                o+=1
            else:
                a+=1
        available.append(a)
        occupied.append(o)
    x=range(len(label))
    plt.figure(figsize=(5,5))
    plt.bar(x,available,width=0.4,label='available',color='#4CAF50')
    plt.bar(x,occupied,width=0.4,label='occupied', bottom=available,color="#D5F80D")
    plt.xticks(x,label,rotation=20)
    plt.ylabel('number of spots')
    plt.title('Available vs Occupied spots per parking lot')
    plt.legend()
    plt.tight_layout()
    plt.savefig("static/oa.png")
    plt.close()
    
    
    return render_template('summary.html',total_revenue=total,revenue='revenue.png',oa='oa.png')  

        
        
@app.route('/user_summary')
def user_summary():
    user_id=session.get('user_id')
    bookings=Booking.query.filter_by(user_ID=user_id).all()
    lot_costs={}
    for i in bookings:
        lot_name=i.spot.parkinglot.Prime_Location_Name
        lot_costs[lot_name]=lot_costs.get(lot_name,0)+i.cost
        
    labels=list(lot_costs.keys())
    values=list(lot_costs.values())


    plt.figure(figsize=(5,5))
    plt.bar(labels,values,color='pink')
    plt.xlabel("parking lot")
    plt.ylabel('cost in Rs.')
    plt.title('Your cost of parking used lots')
    plt.savefig('static/user_summary_img.png')
    plt.close()

    return render_template('user_summary.html',chart='user_summary_img.png')







@app.route("/add-lot",methods=["GET","POST"])
def add_lot():
    if request.method=="POST":
        Prime_Location_Name=request.form['location']
        Address=request.form['Address']
        PinCode=request.form['Pincode']
        Price=float(request.form['Price'])
        Maximum_spots=request.form['maximum_spots']
        already_exist=Parkinglot.query.filter_by(Prime_Location_Name=Prime_Location_Name).first()
        if already_exist:
            return render_template('invalid.html',errormessage="Parking lot already exist")
        new_lot=Parkinglot(Prime_Location_Name=Prime_Location_Name,Address=Address,PinCode=PinCode,Price=Price,Maximum_spots=Maximum_spots)
        
        db.session.add(new_lot)
        db.session.commit()


        for i in range (int(Maximum_spots)):
            spot=Spot(Lot_ID=new_lot.Lot_ID,Status=False)
            db.session.add(spot)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template('add_lot.html')

@app.route("/spot/<int:lot_id>/<int:spot_id>",methods=["GET","POST"])
def view(lot_id,spot_id):
    spot=Spot.query.filter_by(Spot_ID=spot_id,Lot_ID=lot_id).first()
    booking=None
    if spot.Status:
        booking=Booking.query.filter_by(spot_id=spot.Spot_ID).order_by(Booking.booking_time.desc()).first()
        
    if request.method=="POST":
        if not spot.Status:
            parking_lot=Parkinglot.query.get(lot_id)
            if parking_lot and parking_lot.Maximum_spots>0:
                parking_lot.Maximum_spots-=1
            db.session.delete(spot)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("invalid.html",errormessage="Can not delete an occupied parking lot")
    return render_template("view.html",spot=spot,booking=booking)

    # isko karna h pura

@app.route('/occupied_details/booking_id')
def occupied_details(booking_id):
    booking=Booking.query.filter_by(Booking_ID=booking_id).first()
    id=booking.spot_ID
    customer_id=booking.user_ID
    vehicle_no=booking.vehicle_number
    Time=booking.booking_time
    cost=booking.cost
    details=[id,customer_id,vehicle_no,Time,cost]
    return render_template('occupied_details.html',details=details)

@app.route('/user_profile',methods=["GET","POST"])
def user_profile():
    userid=session.get('user_id')
    user=User.query.get(userid)
    if request.method=='POST':
        user.fullname=request.form['fullname']
        user.email_ID=request.form['email']
        user.address=request.form['address']
        user.PinCode=request.form['pincode']

        db.session.commit()

        return redirect(url_for('user_dashboard'))
    return render_template('user_profile.html',user=user)




if __name__=='__main__':
    app.run(debug=True)