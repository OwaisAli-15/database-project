import json
from datetime import datetime
from flask_ngrok import run_with_ngrok
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


run_with_ngrok(app)

socketio = SocketIO(app, manage_session=False)
app.config['SECURITY_RECOVERABLE'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_database6.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#initialize database
db = SQLAlchemy(app) 
SQLALCHEMY_TRACK_MODIFICATIONS = False

bd = sqlite3.connect('sample_database6.db', check_same_thread=False)
print ("Opened database successfully")



# socketio = SocketIO(app, cors_allowed_origins='*')
# SocketIO(app,cors_allowed_origins="http://localhost")
# Session(app)

@socketio.on('message')
def handleMessage(date):

    print(date)

    print("YOLO: ", datetime.strptime(date["checkin"], '%Y-%m-%d').strftime('%D-%M-%Y'))


    # checkindate  = date["checkin"].replace('-', '')
    # checkoutdate  = date["checkOut"].replace('-', '')
    # print(checkindate)

    # datetimeobject = datetime.strptime(checkindate, '%Y%m%d')
    # print("WORK: ", datetimeobject.strftime('%d-%m-%Y'))
    checkindateSet = datetime.strptime(date["checkOut"].replace('-', ''), '%Y%m%d').strftime('%d-%m-%Y')
    checkoutdateSet = datetime.strptime(date["checkin"].replace('-', ''), '%Y%m%d').strftime('%d-%m-%Y')


    allrooms = bd.execute(
        "Select room.roomname, room.roomid from room join roomtype on roomtype.roomtypeid = room.roomtypeid").fetchall() #and roomres.checkin < ? and roomres.checkout > ?

    bd.commit()
    reservedrooms = bd.execute("Select room.roomname, room.roomid from room left join roomres on room.roomid = roomres.roomid where (? >= roomres.checkin and ? <= roomres.checkout) or (? >= roomres.checkin and ? <= roomres.checkout) or (? <= roomres.checkin and ? >= checkout)", ([date["checkin"], date["checkin"], date["checkOut"], date["checkOut"], date["checkin"], date["checkOut"]])).fetchall()
    # reservedrooms = bd.execute("Select room.roomname, room.roomid from room left join roomres on room.roomid = roomres.roomid where roomres.checkin <= ? and ? <= roomres.checkout", ([checkindateSet, checkindateSet])).fetchall()
    bd.commit()
    for a in reservedrooms:
        print("a: ", a)
        print("RESERVED: ", a[0])
        if a in allrooms:
            print("REMOVING: ", allrooms)
            allrooms.remove(a)
        print("Type: ", type(a))
    print(reservedrooms)

    if (allrooms is not None):
        for a in allrooms:
            print("ATYO:", a)
    print('Message: ' + json.dumps(date) )
    print("rooms: ", allrooms)

    date = allrooms

    emit("gotrooms", {"rooms" : allrooms})



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



#bd.execute('CREATE TABLE users (userID INTEGER PRIMARY KEY, CNIC TEXT NOT NULL,Password TEXT NOT NULL,Type TEXT NOT NULL,Transaction_Time TEXT NOT NULL, Status TEXT NOT NULL)')




@app.route('/home', methods=["GET", "POST"])
def Home():

     if request.method  == "GET":
        return render_template("Main2.html")
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
    return  redirect(url_for('reservation'))






@app.route('/', methods=["GET", "POST"])
def login():
     #clear any session

     if request.method  == "GET":
        return render_template("Log-In.html")
     else:
        print("FORM: ", request.form)
        Cnic = request.form.get("CNIC")
        password = request.form.get("Password")

        print("CNIC: ", Cnic, "\npassword: ", password)

        checkuser = bd.execute("select * from newguests where identification = ? and password = ?", ([Cnic, password])).fetchone()
        bd.commit()
        print(checkuser)

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
            return redirect(url_for('register'))
        print("Session: ", session)
        allbookings = bd.execute("Select room.roomname, roomres.checkin, roomres.checkout, reservation.reservationid, reservation.status, reservation.identification, reservation.resforid from roomres join room on roomres.roomid = room.roomid join reservation on reservation.reservationid = roomres.reservationid where identification = ? or resforid = ? order by status", ([session["user_id"] , session["user_id"]])).fetchall()


        allbookings2 = []

        for a in allbookings:
            checkin2 = a[1].replace('-', '')
            checkout2 = a[2].replace('-', '')
            print(checkin2)

            datetimeobject = datetime.strptime(checkin2, '%Y%m%d')
            datetimeobject2 = datetime.strptime(checkout2, '%Y%m%d')
            print("WORK: ", datetimeobject.strftime('%d-%m-%Y'))
            checkindateSet = datetimeobject.strftime('%d-%m-%Y')
            checkoutdateSet = datetimeobject2.strftime('%d-%m-%Y')

            print("CHECK IN:", checkindateSet, "\nCHECK OUT: ", checkoutdateSet)

            a = list(a)

            a[1] = checkindateSet
            a[2] = checkoutdateSet
            print(a)

            a = tuple(a)
            allbookings2.append(a)
        print("ALL: ", allbookings2)



        return render_template("reservation.html", allbookings=allbookings2, id=session["user_id"], type=session["usertype"])
    else:

        cnic = request.form.get('name')
        reference = request.form.get('text')
        pov = request.form.get('text-1')
        checkin = request.form.get('date')
        checkout = request.form.get('date-1')
        room = request.form.get('select')

        print("cnic: ", cnic)
        print("reference: ", reference)
        print("pov: ", pov)
        print("checkout: ", checkout)
        print("checkin: ", checkin)
        print("room: ", room)

        bd.execute("insert into reservation (purposeofvisit, reference, identification, status, resforid) values (?, ?, ?, ?,?);", ([pov, reference, session["user_id"], "Active", cnic]))
        bd.commit()

        id = bd.execute("SELECT * FROM reservation order by reservationid desc LIMIT 1;").fetchone()
        bd.commit()

        print("Last reservation: ", id)

        bd.execute("insert into roomres (roomid, checkin, checkout, reservationid) values (?, ?, ?, ?) ", ([room[0], checkin, checkout, int(id[0])]))
        bd.commit()


        all = bd.execute("Select * from reservation").fetchall()

        print("All res")
        for a in all:
            print(a)

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


        print("password: ", password)
        print("type: ", type)
        print("name: ", name)
        print("gender: ", gender)
        print("Nationality: ", nationality)
        print("Phone_Number: ", phone_Number)
        print("Email_Address: ", email_Address)
        print("org: ", org)
        print("Address: ", address)
        print("Allergies: ", allergies)
        print("Medical: ", medical)
        print("identification: ", identification)


        bd.execute('Insert into newguests (GuestName, password,  identification, phonenumber, email, org, posAdd, gender, allergies, medicalneeds) values (?,?,?,?,?,?,?,?,?,?)', ([name, password, identification, phone_Number, email_Address,org, address,  gender, allergies, medical]))
        bd.commit()


        return redirect('/register')





@app.route('/roomtype', methods=["GET", "POST"])
def roomtype():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))

    if request.method == "GET":

        allroomtypes = bd.execute("Select * from RoomType").fetchall()

        if allroomtypes is not None:
            for a in allroomtypes:
                print(a)

            print(type(allroomtypes))
            return render_template("roomtype.html", allroomtypes=allroomtypes,type=session["usertype"])
        else:
            return render_template("roomtype.html", type=session["usertype"])
    else:

        typename = request.form.get("roomtypename")
        Description = request.form.get("textarea")
        status = request.form.get("select")
        SPrice = request.form.get("email")
        DPrice = request.form.get("text")

        print("Typename: ", typename)
        print("Description: ", Description)
        print("status: ", status)
        print("SPrice: ", SPrice)
        print("DPrice: ", DPrice)


        check = bd.execute("select typename from roomtype where typename=?", ([typename])).fetchone()


        if (check is not None and check[0].strip() == typename.strip()):
            print("Roomtype already present;")
        else:
            print("AYOOOO: ", check==typename)

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

        for a in allroomtypes:
            print("Type: ", a)


        allrooms = bd.execute("Select room.roomid, room.roomname, room.desc, room.roomstatus, room.roomtypeid, roomtype.typename from room, roomtype where roomtype.roomtypeid = room.roomtypeid").fetchall()
        bd.commit()
        if (allrooms is not None):
            for a in allrooms:
                print("ATYO:", a)
            return render_template("room.html", allroomtypes=allroomtypes, allrooms=allrooms, type=session["usertype"])
        else:
            print("Nothing")
            return render_template("room.html", type=session["usertype"])

    else:
        roomName = request.form.get('roomname')
        status = request.form.get('status')
        type = request.form.get('roomtype')
        desc = request.form.get('desc')

        bd.execute("Insert into room (roomname, desc, roomstatus, roomtypeid) values(?, ?,?,?)", ([roomName,desc,  status, type]))

        print("roomname: ", roomName)
        print("status: ", status)
        print("type: ", type)
        print("desc: ", desc)

        return redirect (url_for('Room'))






@app.route('/servicehistory', methods=["GET", "POST"])
def servicehistory():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == 'GET':

        allres = bd.execute(
            "select reservationid, roomname from reservation join roomres using (reservationid) join room using (roomid) where checkin <= DATE('now') and checkout >= DATE('now')"
        ).fetchall()

        print("Allres:", allres)

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
        print("Allres: ", allres)

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

        print(dates)


        total = 0
        num = 0

        for a in dates:
            if a is not None:
                total += int(a[4])
        print("TOTAL: ", total)

        services = bd.execute(
            " select quantity, servicename, servicecharges, quantity * servicecharges from servicehistory join services using (serviceid) where reservationid = ?",
            ([reservation])
        ).fetchall()

        for a in services:
            if a[0] is not None:
                total += int(a[0]) * int(a[2])

        print("TOTAL: ", total)

        extservice = bd.execute(
            "select externalservicequantity, externalservicename, externalservicerate, externalservicequantity * externalservicerate from externalservice where reservationid = ?",
            ([reservation])
        ).fetchall()




        print("SSSSSSSSSSSSSSSSSSSSSSSSSSS: ", services)

        for a in extservice:
            if a[0] is not None:
                total += int(str(a[0])) * int(str(a[2]))
                if a[0] is None:
                    dates.remove(dates[num])
                num += 1
        print("TOTAL: ", total)

        print("Ext:", extservice)

        return render_template('bill.html', dates=dates, allres=allres, services=services, extservice=extservice,total=total, reservation=reservation)


@app.route('/servicecharges', methods=["GET", "POST"])
def servicecharges():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))
    if request.method == 'GET':

        allservices = bd.execute(
            "select * from services"
        ).fetchall()
        print(allservices)
        return render_template("ServiceCharges.html", allservices=allservices, type=session["usertype"])
    else:
        servicename = request.form.get('servicename')
        servicecharges = request.form.get('servicecharges')
        status = request.form.get('select')

        print("servicename: ", servicename)
        print("servicecharges: ", servicecharges)
        print("status: ", status)

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

        print(zip(request.form.get("result")))

        for a in request.form.getlist("result") :
            print(a)

        print(request.form)

        print("Json : ", request.get_json())

        return redirect('/pendings')

    else:
        onebooking = {'userID': '1', 'CNIC': '1236', }

        secondbooking = {'userID': '2', 'UserId': '12336'}


        prof = []

    pendingUsers = bd.execute("Select guestID, identification, guestname, org, usertype from newguests").fetchall()
    bd.commit()
    for a in pendingUsers:
        # print(a)
        prof.append({"userID" : a[0], "name" : a[2], "CNIC" : a[1]})



    return render_template("pendings.html", all_pendings = pendingUsers, type=session["usertype"], CurrentTime= datetime.now().strftime("%d/%m/%Y %H:%M:%S"))



@app.route('/execute', methods=["GET", "POST"])
def execute():
    if session.get("user_id") is None or session.get("usertype") is None:
        return redirect(url_for('login'))

    #bd.execute("CREATE TABLE newguests (guestID INTEGER PRIMARY KEY, GuestName TEXT, title text, password text,  identification integer, idtype text, phonenumber text, email text, org text, posAdd text, gender text, allergies text, medicalneeds text );")

    # bd.execute("Create table RoomType (roomtypeid INTEGER PRIMARY KEY, typename text, description text, status text, standardprice int, discountedprice int);")
    # bd.commit();

    # bd.execute("Drop table room;")


    # bd.execute("Insert into roomres (roomid, checkin, checkout, reservationid) values (?,?,?,?)", ([3, '02-01-2021', '10-10-2021', 1]))

    # for a in bd.execute("Select room.roomid, roomres.checkin, roomres.checkout,  room.roomname, room.desc, room.roomstatus, room.roomtypeid, roomtype.typename from room join roomtype on roomtype.roomtypeid = room.roomtypeid left join roomres on room.roomid = roomres.roomid where roomres.checkin <= ? and ? <= roomres.checkout", (["10-10-2021", "10-10-2021"])).fetchall():
    #     print("Worko: ", a)

    # a = bd.execute("Delete from reservation;").fetchall()
    #
    # a = bd.execute("Delete from  roomres;").fetchall()
    # a = bd.execute("Delete from  servicehistory;").fetchall()
    # bd.commit()

    bd.execute(".schema reservation")
    bd.commit()

    # for b in a:
    #     print(a)

    bd.commit()

    # bd.execute(
    #     "CREATE table externalservice (externalserviceid INTEGER Primary Key, externalservicename text, externalservicerate Integer , externalservicequantity Integer, externalserviceprovider text, exRecieptID Integer);")
    # bd.commit()

    print("Dont!")
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
        print("AYOOOO: ", b)
        a = ""
        for key in request.form.keys():
            a += key

    op = ""
    for key in request.form.values():
        print("KEY: ", key)
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

























