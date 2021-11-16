import json
from datetime import datetime

import socketio
from flask import Flask, render_template, request, redirect, url_for, session,flash
import os
import requests
from functools import wraps
from flask import Flask, session, flash, redirect, render_template, request, jsonify
from flask_session import Session
from flask_socketio import SocketIO, send, emit
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool





app = Flask(__name__)
app.debug=True
TEMPLATES_AUTO_RELOAD = True
app.secret_key = "my secret key"
app.config["SESSION_TYPE"] = "filesystem"

Session(app)




socketio = SocketIO(app, manage_session=False)
app.config['SECURITY_RECOVERABLE'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_database6.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#initialize database
db = SQLAlchemy(app) 
SQLALCHEMY_TRACK_MODIFICATIONS = False

bd = sqlite3.connect('sample_database6.db', check_same_thread=False)
print ("Opened database successfully")


#Socket IO Function in Reservation Page
# When user chooses a check in and check out date,
    # it's sent here
    # Dates are checked in database for available rooms
    # available rooms are sent back to reservation page

@socketio.on('message')
def handleMessage(date):

    # Get all rooms and room types !
    allrooms = bd.execute(
        "Select room.roomname, room.roomid from room join roomtype on roomtype.roomtypeid = room.roomtypeid").fetchall()
    bd.commit()

    # Fetch all rooms that lie between the specified dateaa
    reservedrooms = bd.execute("Select room.roomname, room.roomid from room left join roomres on room.roomid = roomres.roomid where (? >= roomres.checkin and ? <= roomres.checkout) or (? >= roomres.checkin and ? <= roomres.checkout) or (? <= roomres.checkin and ? >= checkout)", ([date["checkin"], date["checkin"], date["checkOut"], date["checkOut"], date["checkin"], date["checkOut"]])).fetchall()
    bd.commit()

    # Remove all rooms that have been reserved for specified dates
    for a in reservedrooms:
        if a in allrooms:
            allrooms.remove(a)

    # send this data to reservation page
    emit("gotrooms", {"rooms" : allrooms})


# Log in page
def go_login():
    if session.get("user_id") is None:
        print("redirect required")
        return redirect("/login")
    else:
        print("NO logIn")


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            print("redirect required")
            return redirect("/")
        else:
            print("NO logIn")
        return f(*args, **kwargs)
    return decorated_function



@app.route('/', methods=["GET", "POST"])
def Home():

     if request.method  == "GET":
        return render_template("Home.html")
     else:

        return  redirect(url_for('Home'))


@app.route('/main', methods=["GET", "POST"])
def Main():

     if request.method  == "GET":
        return render_template("book.html")
     else:

        return  redirect(url_for('Main'))

@app.route('/Details', methods=["GET", "POST"])
def Details():

     if request.method  == "GET":
        return render_template("GuestRoomDetails.html")
     else:

        return  redirect(url_for('reservation'))

@app.route('/logout', methods=["GET"])
def logout():

    session.clear()
    return  redirect(url_for('Home'))




@app.route('/login', methods=["GET", "POST"])
def login():
     #clear any session

     if request.method  == "GET":
        return render_template("Log-In.html")

     else:

        print("LOGGING IN")

        # Get CNIC and Password From Form
        Cnic = request.form.get("CNIC")
        password = request.form.get("Password")

        # Check if Log in Credentials are valid
        checkuser = bd.execute("select * from newguests where identification = ? and password = ?", ([Cnic, password])).fetchone()
        bd.commit()

        # If credentials are wrong, user prompted to Registration
        if (checkuser is None):
            return redirect(url_for('register'))


        session["user_id"] = Cnic
        session["usertype"] = checkuser[13]

        return  redirect(url_for('reservation'))



@login_required
@app.route('/reservation', methods=["GET", "POST"])
def reservation():
    if request.method == "GET":
        if session.get("user_id") is None:
            return redirect(url_for('login'))

        # Get all reservations
        allbookings = bd.execute("Select room.roomname, roomres.checkin, roomres.checkout, reservation.reservationid, reservation.status, reservation.identification, reservation.resforid from roomres join room on roomres.roomid = room.roomid join reservation on reservation.reservationid = roomres.reservationid where identification = ? or resforid = ? order by status", ([session["user_id"] , session["user_id"]])).fetchall()

        allbookings2 = []

        # Convert Date to DD-MM-YYYY Format
        for a in allbookings:
            checkin2 = a[1].replace('-', '')
            checkout2 = a[2].replace('-', '')

            datetimeobject = datetime.strptime(checkin2, '%Y%m%d')
            datetimeobject2 = datetime.strptime(checkout2, '%Y%m%d')

            checkindateSet = datetimeobject.strftime('%d-%m-%Y')
            checkoutdateSet = datetimeobject2.strftime('%d-%m-%Y')

            a = list(a)

            a[1] = checkindateSet
            a[2] = checkoutdateSet

            a = tuple(a)
            allbookings2.append(a)

        return render_template("reservation.html", allbookings=allbookings2, id=session["user_id"], type=session["usertype"])


    else:

        cnic = request.form.get('name')
        reference = request.form.get('text')
        pov = request.form.get('text-1')
        checkin = request.form.get('date')
        checkout = request.form.get('date-1')
        room = request.form.get('select')

        # Insert Reservation Details into Database
        bd.execute("insert into reservation (purposeofvisit, reference, identification, status, resforid) values (?, ?, ?, ?,?);", ([pov, reference, session["user_id"], "Active", cnic]))
        bd.commit()

        # Get the ID for last reservation
        id = bd.execute("SELECT * FROM reservation order by reservationid desc LIMIT 1;").fetchone()
        bd.commit()

        # insert Reservation dates into Roomres
        bd.execute("insert into roomres (roomid, checkin, checkout, reservationid) values (?, ?, ?, ?) ", ([room[0], checkin, checkout, int(id[0])]))
        bd.commit()

        return redirect(url_for('reservation'))




@app.route('/register', methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "GET":
        return render_template("Sign-Up.html")

    else:
        #Get CNIC, Passwor and type from the form

        password = request.form.get("password")
        type = request.form.get("select")
        name = request.form.get("name")
        gender = request.form.get("select")
        identification = request.form.get("identification")
        nationality = request.form.get("Nationality")
        phone_Number = request.form.get("Phone_Number")
        email_Address = request.form.get("Email_Address")
        org = request.form.get("org")
        address = request.form.get("Address")
        allergies = request.form.get("Allergies")
        medical = request.form.get("Medical")

        # Register User to Database
        bd.execute('Insert into newguests (GuestName, password,  identification, phonenumber, email, org, posAdd, gender, allergies, medicalneeds) values (?,?,?,?,?,?,?,?,?,?)', ([name, password, identification, phone_Number, email_Address,org, address,  gender, allergies, medical]))
        bd.commit()

        return redirect('/register')





@app.route('/roomtype', methods=["GET", "POST"])
def roomtype():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))

    if request.method == "GET":

        allroomtypes = bd.execute("Select * from RoomType").fetchall()

        # if there are roomtypes already
        if allroomtypes is not None:
            return render_template("roomtype.html", allroomtypes=allroomtypes,type=session["usertype"])
        else:
            return render_template("roomtype.html", type=session["usertype"])
    else:

        typename = request.form.get("roomtypename")
        Description = request.form.get("textarea")
        status = request.form.get("select")
        SPrice = request.form.get("email")
        DPrice = request.form.get("text")

        # Check if roomtype is already present in database
        check = bd.execute("select typename from roomtype where typename=?", ([typename])).fetchone()

        if (check is not None and check[0].strip() == typename.strip()):
            print("Roomtype already present;")
        else:
            # insert into Database the roomtype
            bd.execute("Insert into RoomType (typename , description , status , standardprice , discountedprice ) values (?,?,?,?,?)",
                       ([typename, Description, status, SPrice, DPrice]))

            bd.commit()

        return redirect(url_for('roomtype'))


@app.route('/room', methods=["GET", "POST"])
def Room():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == "GET":

        allroomtypes = bd.execute("select typename, roomtypeid from roomtype;").fetchall()
        bd.commit()

        allrooms = bd.execute("Select room.roomid, room.roomname, room.desc, room.roomstatus, room.roomtypeid, roomtype.typename from room, roomtype where roomtype.roomtypeid = room.roomtypeid").fetchall()
        bd.commit()
        if (allrooms is not None):

            return render_template("room.html", allroomtypes=allroomtypes, allrooms=allrooms, type=session["usertype"])
        else:
            return render_template("room.html", type=session["usertype"])

    else:
        roomName = request.form.get('roomname')
        status = request.form.get('status')
        type = request.form.get('roomtype')
        desc = request.form.get('desc')

        bd.execute("Insert into room (roomname, desc, roomstatus, roomtypeid) values(?, ?,?,?)", ([roomName,desc,  status, type]))

        return redirect (url_for('Room'))


@app.route('/servicehistory', methods=["GET", "POST"])
def servicehistory():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == 'GET':

        allres = bd.execute(
            "select reservationid, roomname from reservation join roomres using (reservationid) join room using (roomid) where checkin <= DATE('now') and checkout >= DATE('now')"
        ).fetchall()

        allser = bd.execute(
            "select serviceid, servicename, servicecharges from services"
        ).fetchall()

        return render_template("service-history.html", allres=allres, allser=allser, type=session["usertype"])

    else:
        reservation = request.form.get('select-1')
        service = request.form.get('select')
        dprice = request.form.get('dprice')
        quantity = request.form.get('quantity')


        bd.execute(
            "insert into servicehistory (serviceid, reservationid, quantity) values (?,?,?)",
            ([service, reservation, quantity])
        )
        bd.commit()

        return redirect(url_for('servicehistory'))


@app.route('/externalservice', methods=["GET", "POST"])
def externalservice():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == 'GET':

        allres = bd.execute(
            "select reservationid, roomname from reservation join roomres using (reservationid) join room using (roomid) where checkin <= DATE('now') and checkout >= DATE('now')"
        ).fetchall()

        return render_template("externalservice.html", allres=allres, type=session["usertype"])

    else:
        reservation = request.form.get('select-1')
        name = request.form.get('servicename')
        rate = request.form.get('servicecharges')
        quantity = request.form.get('text')
        provider = request.form.get('text-1')
        id = request.form.get('text-2')

        bd.execute(
            "insert into externalservice (reservationid, externalservicename, externalservicerate, externalservicequantity, externalserviceprovider, exRecieptID) values (?,?,?,?,?,?)",
            ([reservation, name, rate, quantity, provider, id])
        )
        bd.commit()

        return redirect(url_for('externalservice'))



@app.route('/bill', methods=["GET", "POST"])
def bill():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == 'GET':

        allres = bd.execute(
            "select reservationid, roomname, checkin, checkout from reservation join roomres using (reservationid) join room using (roomid)"
        ).fetchall()
        bd.commit()

        return render_template("bill.html", allres=allres, type=session["usertype"])

    else:
        reservation = request.form.get('select')
        print("ID:", reservation)

        allres = bd.execute(
            "select reservationid, roomname, checkin, checkout from reservation join roomres using (reservationid) join room using (roomid)"
        ).fetchall()
        bd.commit()

        dates = bd.execute(
                "SELECT roomname, typename, standardprice, ROUND((JULIANDAY(checkout) - JULIANDAY(checkin))) as noofdays, ROUND((JULIANDAY(checkout) - JULIANDAY(checkin))) * standardprice, reservation.paid  FROM 'roomres' join 'room' using (roomid) join 'roomtype' using (roomtypeid) join reservation using (reservationid) where roomres.reservationid = ?",
            ([reservation])
        ).fetchall()
        bd.commit()

        total = 0
        num = 0

        for a in dates:
            if a is not None:
                total += int(a[4])

        services = bd.execute(
            " select quantity, servicename, servicecharges, quantity * servicecharges from servicehistory join services using (serviceid) where reservationid = ?",
            ([reservation])
        ).fetchall()

        for a in services:
            if a[0] is not None:
                total += int(a[0]) * int(a[2])

        extservice = bd.execute(
            "select externalservicequantity, externalservicename, externalservicerate, externalservicequantity * externalservicerate from externalservice where reservationid = ?",
            ([reservation])
        ).fetchall()


        for a in extservice:
            if a[0] is not None:
                total += int(str(a[0])) * int(str(a[2]))
                if a[0] is None:
                    dates.remove(dates[num])
                num += 1

        return render_template('bill.html', dates=dates, allres=allres, services=services, extservice=extservice,total=total, reservation=reservation)


@app.route('/servicecharges', methods=["GET", "POST"])
def servicecharges():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == 'GET':

        allservices = bd.execute(
            "select * from services"
        ).fetchall()
        return render_template("ServiceCharges.html", allservices=allservices, type=session["usertype"])
    else:
        servicename = request.form.get('servicename')
        servicecharges = request.form.get('servicecharges')
        status = request.form.get('select')

        bd.execute(
            "insert into services (servicename, servicecharges, status) values (?,?,?) ", ([servicename, servicecharges, status])
        )
        bd.commit()

        return redirect(url_for('servicecharges'))


@app.route('/pendings', methods=["GET", "POST"])
def pendings():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))

    if request.method == "POST":

        return redirect('/pendings')

    else:
        prof = []

        pendingUsers = bd.execute("Select guestID, identification, guestname, org, usertype from newguests").fetchall()
        bd.commit()
        for a in pendingUsers:
            prof.append({"userID" : a[0], "name" : a[2], "CNIC" : a[1]})

        return render_template("pendings.html", all_pendings = pendingUsers, type=session["usertype"], CurrentTime= datetime.now().strftime("%d/%m/%Y %H:%M:%S"))



@app.route('/execute', methods=["GET", "POST"])
def execute():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))

    # bd.execute("Create table RoomType (roomtypeid INTEGER PRIMARY KEY, typename text, description text, status text, standardprice int, discountedprice int);")
    # bd.commit();

    return redirect('/')


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'\

@app.route('/addRegion', methods=['POST'])
def addRegion():
    a = ""
    for key in request.form.keys():
        a += key

    bd.execute("Update reservation set status = 'Canceled' Where reservationid = ? ", ([key]))
    bd.commit()
    return redirect(url_for('reservation'))


@app.route('/paid', methods=['POST'])
def setpaid():
    a = ""
    for key in request.form.keys():
        a += key

    bd.execute("Update reservation set paid = 'paid' Where reservationid = ? ", ([key]))
    bd.commit()
    return redirect(url_for('bill'))


@app.route('/updatesuer', methods=['POST'])
def updateuser():

    b = ""
    for a in request.form.values():
        b += a
    if b == "setAdmin" or b == "setUser":
        a = ""
        for key in request.form.keys():
            a += key

    op = ""
    for key in request.form.values():

        op += key
    print(request.form.items())
    a = ""
    for key in request.form.keys():
        a += key

    bd.execute("Update newguests set usertype = ? Where guestid = ? ", ([op, key]))
    bd.commit()
    return redirect(url_for('pendings'))



@app.route('/cancelreservation', methods=['POST'])
def cancelres():
    print("WORKING ")
    print(request.form)
    return 'Server shutting down...'









if __name__ == '__main__':
    app.run()

























