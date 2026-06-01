from fastapi import Request, FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import pymysql
import random  # just for testing with random bus stop key
import threading
import os, uuid
import google.generativeai as genai
from datetime import datetime, timedelta

# 🔴 ADD SESSION
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
#ADD YOUR GOOGLE GEN AI API KEY HERE
genai.configure(api_key="AQ.Ab8RN6LTABdT_apjKnXmLlwtXXr3Z0rImCMrIGhbkD9B6CNeDg")
model = genai.GenerativeModel("gemini-2.5-flash")

#------------------System prompt for Gen AI------------------
SYSTEM_PROMPT = """
You are Smart Bus Assistant, an AI assistant for a Smart Bus Ticketing System.
Your role is to help users understand how the Smart Bus service works and answer questions related to bus travel, smart cards, fares, recharges, and system usage.

## Smart Bus System Information

Smart Card:

-Every registered user receives a Smart Bus Card.
-The card must have sufficient balance before travel.
-Users can recharge their card online.

Recharge Process:

-Card recharges are processed through Recharge page.
-Users can recharge using supported payment methods available in recharge page.
-If a payment issue occurs, advise users to retry or contact support.

Ride Process:

-The first card scan when boarding starts a journey.
-The second card scan when exiting ends the journey.
-Fare is calculated automatically based on the number of stops traveled.

Bus Stops:

1. Stop A
2. Stop B
3. Stop C
4. Stop D

## Important Restrictions

Never:

-Claim to know a user's card balance.
-Claim to know a user's ride history.
-Claim to know a user's personal account details.
-Invent transaction information.
-Assume a recharge was successful unless explicitly confirmed by the system.

If users ask about:

-Card balance
-Recharge history
-Ride history
-Personal account information

Respond:
"Please check your dashboard or account portal for this information."

## Scope

Answer only questions related to:

-Smart Bus cards
-Bus travel process
-Recharge procedures
-Fare calculation rules
-Bus stops
-Smart Bus system usage

For questions unrelated to the Smart Bus system, politely respond:
"I can only assist with Smart Bus related queries."

"""

FAQS = {
    "recharge": "You can recharge your SmartBus card through the Recharge page.",

    "fare": "Fare is calculated based on the number of stops travelled.",

    "stops": "Available stops are Stop A, Stop B, Stop C and Stop D.",

    "start ride": "Tap your card once while boarding.",

    "end ride": "Tap your card again before leaving the bus.",

    "low balance": "Please recharge your card before travelling.",

    "card": "Every user receives a SmartBus card during signup.",

    "dashboard": "The dashboard shows balance, recent rides and transactions."
}

def get_faq_answer(message):

    msg = message.lower()

    for keyword, answer in FAQS.items():

        if keyword in msg:

            return answer

    return None

# 🔴 SESSION MIDDLEWARE
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CHANGE-1: bus stops - dictionary mapping stop IDs to names
stops = {0: "Stop A", 1: "Stop B", 2: "Stop C", 3: "Stop D"}


# Database connection
def get_db():
    return pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT")),
        cursorclass=pymysql.cursors.DictCursor,
    )

# CHANGE-2:fare table (Matrix representation)
fares = [
    [0, 8, 16, 24],
    [8, 0, 8, 16],
    [16, 8, 0, 8],
    [24, 16, 8, 0]
]


# CHANGE-3: searching the fare between two stops
def get_fare(from_stop, to_stop):
    return fares[from_stop][to_stop]

# # CHANGE-4: current stop
# curStopKey = random.choice(
#     list(stops.keys())
# )  # current stop will be updated from keypad
# curStop = stops[curStopKey]

# CHANGE-5: retrieving key of corresponding Stop name
def retrieveKey(stopName):
    for key, value in stops.items():
        if value == stopName:
            return key
    return None

# CHANGE-6: balance updation after fare deduction
# def balanceUpdate(card_id,fare):
#     balance = card["balance"]

#     if balance >= fare:
#             new_balance = balance - fare

# #CHANGE-7: update the stops according to current stop and fare updation
# def update_stops(card_id, curStop):
#     db = get_db()
#     cursor = db.cursor()
#     cursor.execute("SELECT from_stop, balance FROM rides where card_id=%s", (card_id,))
#     card = cursor.fetchone()
#     # tap-2
#     if card:
#         fare = get_fare(from_stop=retrieveKey(card["from_stop"]), to_stop=curStopKey) #fare fetched from fare table
#         balance = card["balance"]
#         if balance >= fare:
#             new_balance = balance - fare
#         cursor.execute("UPDATE rides SET to_stop=%s, fare=%s WHERE card_id=%s", (curStop, fare, card_id))
#         cursor.execute("UPDATE cards SET balance=%s WHERE card_id=%s", (new_balance, card_id))
#     #tap-1
#     else:
#         cursor.execute("INSERT INTO rides(card_id, from_stop, to_stop, fare) VALUES(%s,%s,%s,%s)", (card_id, curStop, None, 0))

#     db.commit()
#     cursor.close()
#     db.close()

def get_current_user(request: Request):
    return request.session.get("user")

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user

def require_admin(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.get("role", "").lower() != "admin":
        return HTMLResponse("Access Denied: Admins only", status_code=403)

    return user

# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    # Get user from session
    user = request.session.get("user")

    # Extract card_id safely
    card_id = user.get("card_id") if user else None

    db = get_db()
    cursor = db.cursor()

    card = None
    trip = None

    if card_id:
        # Fetch card details
        cursor.execute(
            "SELECT card_id, balance FROM cards WHERE card_id=%s",
            (card_id,),
        )
        card = cursor.fetchone()

        # Fetch last trip
        cursor.execute(
            """
            SELECT from_stop, to_stop, fare
            FROM rides
            WHERE card_id=%s
            ORDER BY ride_id DESC LIMIT 1
            """,
            (card_id,),
        )
        trip = cursor.fetchone()

    cursor.close()
    db.close()

    # Safe values
    balance = card["balance"] if card else 0

    name = "Guest"
    if user:
        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "user": user,
            "Name": name,
            "balance": balance,
            "card_id": card["card_id"] if card else "N/A",
            "from_stop": trip["from_stop"] if trip else "N/A",
            "to_stop": trip["to_stop"] if trip else "N/A",
            "fare": trip["fare"] if trip else 0,
            "updated_time": "N/A",
            "status": "Active" if balance > 0 else "Low Balance",
        },
    )

# ---------------- HOME REDIRECT ----------------
# @app.get("/home", response_class=HTMLResponse)
# def home_redirect(request: Request, card_id: Optional[str] = None):
#     return RedirectResponse(url=f"/?card_id={card_id}", status_code=303)

@app.get("/home")
def home_redirect(request: Request):
    return RedirectResponse("/", status_code=303)

# ------------------- SIGNUP ----------------
@app.post("/signup")
def signup(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT card_id FROM cards_in_stock WHERE status='OPEN' LIMIT 1"
    )

    row = cursor.fetchone()
    if not row:
        return RedirectResponse(
            url="/login?error=No available cards in stock",
            status_code=303
        )

    card_id = row["card_id"]  # allocate a unique card ID for the new user

    # NEW CHECK
    cursor.execute(
        "SELECT id FROM login WHERE email=%s",
        (email,)
    )

    if cursor.fetchone():
        cursor.close()
        db.close()
        return RedirectResponse("/login?error=Email already exists", status_code=303)

    cursor.execute(
        """
        INSERT INTO login(
            card_id, first_name, last_name,
            email, phone, password, role, profile_pic
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (card_id, first_name, last_name, email, phone, password, role, "/static/source/default.png"),
    )

    cursor.execute(
        "UPDATE cards_in_stock SET status='CLOSED' WHERE card_id=%s",
        (card_id,)
    )

     # Check if card already exists
    cursor.execute(
        "SELECT card_id FROM cards WHERE card_id=%s",
        (card_id,)
    )

    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO cards(card_id, balance, status) VALUES(%s,%s,%s)",
            (card_id, 0.00, "active")
        )

    db.commit()

    cursor.close()
    db.close()

    return RedirectResponse("/login", status_code=303)

# ---------------- LOGIN ----------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": error
        }
    )

@app.post("/login")
def login_user(request: Request, email: str = Form(...), password: str = Form(...)):

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        "SELECT * FROM login WHERE email=%s AND password=%s",
        (email, password),
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user:
        request.session["user"] = {
            "id": user.get("id"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "email": user.get("email"),
            "role": (user.get("role") or "").strip().lower(),
            "card_id": user.get("card_id"),
            "profile_pic": user.get("profile_pic") or "/static/source/default.png",
        }

        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": "Invalid credentials"
        },
    )

# ---------------- SCAN ----------------
@app.post("/scan")
def scan_card(card_id: str = Form(...), keyStop: int = Form(...), device_id: str = Form("100.0.0.3")):

    db = get_db()
    cursor = db.cursor()

    # Validate stop
    if keyStop not in stops:
        return {"error": f"Invalid stop: {keyStop}"}

    curStop = stops[keyStop]

    # device_id and bus_no mapping
    cursor.execute(""" SELECT b.bus_no FROM devices d JOIN buses b ON d.bus_id = b.bus_id WHERE d.device_id=%s """, (device_id,))
    bus_row = cursor.fetchone()
    if not bus_row:
        return {"error": "Invalid device ID"}
    bus_no = bus_row["bus_no"]

    print("SCAN:", card_id, keyStop, "Device:", device_id, "Bus No:", bus_no)

    # Check for active ride
    cursor.execute(
        """
        SELECT r.from_stop, c.balance, c.status
        FROM rides r
        JOIN cards c ON r.card_id = c.card_id
        WHERE r.card_id=%s AND r.to_stop IS NULL
        LIMIT 1
        """,
        (card_id,)
    )

    active_ride = cursor.fetchone()

    # =========================
    # TAP-2 → END RIDE
    # =========================
    if active_ride:
        from_stop = active_ride["from_stop"]
        balance = active_ride["balance"]
        status = active_ride["status"]

        # Card inactive
        if status != "active":
            return {"error": "Card is inactive"}

        to_stop = curStop

        # DUPLICATE STOP CHECK (NEW)
        if from_stop == to_stop:
            return {
                "status": "duplicate tap",
                "message": "Tap ignored: Same stop scanned twice",
                "stop": to_stop,
            }

        # check pending rides for the same card_id
        cursor.execute(
            "SELECT id, to_stop,fare FROM pending_rides WHERE card_id=%s LIMIT 1",
            (card_id,)
        )
        pending = cursor.fetchone()

        if pending:
            if pending["to_stop"] != to_stop:
                return {
                    "error": "Stop mismatch - Pending ride exists for a different destination"
                }
            fare = pending["fare"]

            if balance >= fare:
                new_balance = balance - fare
                # Update ride
                cursor.execute(
                    "UPDATE rides SET to_stop=%s, fare=%s, bus_no=%s, device_id=%s WHERE card_id=%s AND to_stop IS NULL",
                    (to_stop, fare, bus_no, device_id, card_id)
                )

                # Update balance
                cursor.execute(
                    "UPDATE cards SET balance=%s WHERE card_id=%s",
                    (new_balance, card_id)
                )

                # Store transaction
                description = f"{from_stop} → {to_stop}"
                cursor.execute(
                    "INSERT INTO transactions(type, card_id, description, amount, bus_no, device_id) VALUES(%s,%s,%s,%s,%s,%s)",
                    ("ride", card_id, description, fare, bus_no, device_id)
                )

                # Remove pending rides
                cursor.execute(
                    "DELETE FROM pending_rides WHERE id=%s",
                    (pending["id"],)
                )
                db.commit()

                return {
                    "status": "ride completed",
                    "card_id": card_id,
                    "from": from_stop,
                    "to": to_stop,
                    "fare": fare,
                    "balance": new_balance
                }

            else:
                return {
                    "status": "insufficient balance",
                    "card_id": card_id,
                    "balance": balance,
                    "required": fare
                }

        #normal fare calculation - no pending rides(through plan_ride)
        from_key = retrieveKey(from_stop)

        # additional safety
        if from_key is None:
            return {"error": f"Invalid from_stop: {from_stop}"}

        fare = get_fare(from_key, keyStop)
        # additional safety
        if fare is None or fare < 0:
            return {"error": "Fare calculation failed"}

        if balance >= fare:
            new_balance = balance - fare

            # Update ride
            cursor.execute(
                """
                UPDATE rides
                SET to_stop=%s, fare=%s, bus_no=%s, device_id=%s
                WHERE card_id=%s AND to_stop IS NULL
                """,
                (to_stop, fare, bus_no, device_id, card_id),
            )

            # Update balance
            cursor.execute(
                """
                UPDATE cards
                SET balance=%s
                WHERE card_id=%s
                """,
                (new_balance, card_id),
            )

            # Store transaction
            description = f"{from_stop} → {to_stop}"
            cursor.execute(
                """
                INSERT INTO transactions(type, card_id, description, amount, bus_no, device_id)
                VALUES(%s,%s,%s,%s,%s,%s)
                """,
                ("ride", card_id, description, fare, bus_no, device_id)
            )

            db.commit()

            return {
                "status": "ride completed",
                "card_id": card_id,
                "from": from_stop,
                "to": to_stop,
                "fare": fare,
                "balance": new_balance,
            }

        else:
            return {
                "status": "insufficient balance",
                "card_id": card_id,
                "balance": balance,
                "required": fare,
            }

    # =========================
    # TAP-1 → START RIDE
    # =========================
    else:
        cursor.execute(
            "SELECT * FROM cards WHERE card_id=%s",
            (card_id,)
        )
        existing_card = cursor.fetchone()

        #exist card check
        if not existing_card:
            return {"error": "Card not found"}

        #active card check
        if existing_card["status"] != "active":
            return {"error": "Card is inactive"}

        balance = existing_card["balance"]

        if balance <= 0:
            return {
                "status": "low balance",
                "card_id": card_id,
                "balance": balance,
                "message": "Please recharge your card to start a ride"
            }

        # Extra safety
        cursor.execute(
            """
            SELECT * FROM rides
            WHERE card_id=%s AND to_stop IS NULL
            """,
            (card_id,),
        )

        if cursor.fetchone():
            return {"error": "Ride already in progress"}

        # Start ride
        cursor.execute(
            """
            INSERT INTO rides(card_id, from_stop, to_stop, fare, bus_no, device_id)
            VALUES(%s,%s,%s,%s,%s,%s)
            """,
            (card_id, curStop, None, 0, bus_no, device_id),
        )

        db.commit()

        return {
            "status": "ride started",
            "from": curStop,
            "card_id": card_id
            }

# # ---------------- TAP CARD ----------------
# @app.post("/tap_card")
# def tap_card(
#     card_id: str = Form(...),
#     # fare: float = Form(...),
#     # Starting_place: str = Form(...),
#     # Ending_place: str = Form(...),
#     keyStop: int = Form(...),
# ):

#     db = get_db()
#     cursor = db.cursor(pymysql.cursors.DictCursor)

#     cursor.execute("SELECT balance FROM cards WHERE card_id=%s", (card_id,))
#     card = cursor.fetchone()

#     if not card:
#         cursor.close()
#         db.close()
#         return {"status": "Card not found"}

#     balance = card["balance"]

#     if balance < fare:
#         cursor.close()
#         db.close()
#         return {"status": "Insufficient balance"}

#     cursor.execute(
#         "UPDATE cards SET balance = balance - %s WHERE card_id=%s",
#         (fare, card_id),
#     )

#     cursor.execute(
#         """
#         INSERT INTO rides(card_id, from_stop, to_stop, fare)
#         VALUES (%s,%s,%s,%s)
#         """,
#         (card_id, Starting_place, Ending_place, fare),
#     )

#     description = f"{Starting_place} → {Ending_place}"

#     cursor.execute(
#         """
#         INSERT INTO transactions(type, card_id, description, amount)
#         VALUES (%s,%s,%s,%s)
#         """,
#         ("Ride", card_id, description, fare),
#     )

#     db.commit()

#     cursor.close()
#     db.close()

#     return RedirectResponse(url=f"/dashboard?card_id={card_id}", status_code=303)

#----------------------------------------------------------------
# fine/ penalty apply and deduction
@app.post("/apply_penalty")
def apply_penalty(card_id: str, bus_no: str, device_id: str):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Find incomplete ride
    cursor.execute("""
        SELECT ride_id, from_stop, ride_time, bus_no, device_id
        FROM rides
        WHERE card_id=%s AND to_stop IS NULL
        LIMIT 1
    """, (card_id,))
    ride = cursor.fetchone()

    if not ride:
        return {"status": "no penalty", "card_id": card_id}

    # Check if 24 hrs have passed
    start_time = ride["ride_time"]
    now = datetime.now()
    if (now - start_time).total_seconds() < 40:
        return {"status": "grace period", "card_id": card_id}

    # check if pending rides present
    cursor.execute(""" SELECT to_stop, fare FROM pending_rides WHERE card_id=%s LIMIT 1""", (card_id,))
    pending = cursor.fetchone()
    if pending:
        fine_amount = pending["fare"]
        fine_reason = f"Pending ride fare deduction ({ride['from_stop']} → {pending['to_stop']})"
        cursor.execute("DELETE FROM pending_rides WHERE card_id=%s", (card_id,))
    else:
        fine_amount = 50  # Dummy fine
        fine_reason = "No tap out within 24 hrs"

    # Deduct balance
    cursor.execute("SELECT balance FROM cards WHERE card_id=%s", (card_id,))
    card = cursor.fetchone()
    if not card:
        return {"error": "Card not found"}

    balance = card["balance"]

    if balance < fine_amount:
        return {
            "status": "insufficient balance for fine",
            "card_id": card_id,
            "balance": balance,
            "fine": fine_amount
        }

    new_balance = balance - fine_amount

    cursor.execute("UPDATE cards SET balance=%s WHERE card_id=%s", (new_balance, card_id))

    # Store fine transaction
    cursor.execute("""
        INSERT INTO transactions(type, card_id, description, amount, bus_no, device_id, fine_reason)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
    """, ("fine", card_id, f"Penalty: Incomplete ride from {ride['from_stop']}", fine_amount, bus_no, device_id, fine_reason))

    # Close ride with penalty
    cursor.execute("UPDATE rides SET to_stop='Penalty', fare=%s WHERE ride_id=%s", (fine_amount, ride["ride_id"]))
    db.commit()

    return {
        "status": "fine imposed",
        "card_id": card_id,
        "fine": fine_amount,
        "balance": new_balance
    }

#------------------------------------------------------------------------------------

# NEW ADDITION-------- plan rides before reaching destination ----------------
@app.post("/plan_ride")
def plan_ride(
        card_id: str = Form(...),
        Starting_place: str = Form(None),
        Ending_place: str = Form(...),
        fare: float = Form(None),
    ):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Find active ride (Tap-1 already done)
    cursor.execute(
        """
        SELECT from_stop FROM rides
        WHERE card_id=%s AND to_stop IS NULL
        LIMIT 1
        """,
        (card_id,)
    )

    active = cursor.fetchone()

    if not active:
        return {"error": "No active ride found. Tap card first."}

    from_stop = active["from_stop"]

    # check duplicate stop here also
    if from_stop == Ending_place:
        return {
            "status": "duplicate stop",
            "message": "Please select a different destination than your starting point",
            "from_stop": from_stop,
            "to_stop": Ending_place
        }

    # Calculate fare automatically
    from_key = retrieveKey(from_stop)
    to_key = retrieveKey(Ending_place)
    fare = get_fare(from_key, to_key)

    # Store planned ride in pending queue
    cursor.execute(
        """
        INSERT INTO pending_rides(card_id, from_stop, to_stop, fare)
        VALUES(%s,%s,%s,%s)
        """,
        (card_id, from_stop, Ending_place, fare)
    )
    db.commit()

    cursor.close()
    db.close()

    return RedirectResponse(
        url=f"/dashboard?card_id={card_id}",
        status_code=303
    )

#-----------------------New addition for dashboard display-----------------------


#---------------------- fetch active ride details - source stop of corresponding card_id----------------------
@app.get("/get_active_ride")
def get_active_ride(card_id: str):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "SELECT from_stop FROM rides WHERE card_id=%s AND to_stop IS NULL LIMIT 1",
        (card_id,)
    )
    active = cursor.fetchone()
    cursor.close()
    db.close()
    return {"from_stop": active["from_stop"] if active else None}

#----------------------fetch fare for the active ride as per planned destination----------------------
@app.get("/calculate_fare")
def calculate_fare(card_id: str, to_stop: str):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "SELECT from_stop FROM rides WHERE card_id=%s AND to_stop IS NULL LIMIT 1",
        (card_id,)
    )
    active = cursor.fetchone()
    if not active:
        return {"fare": None}
    from_stop = active["from_stop"]
    fare = get_fare(retrieveKey(from_stop), retrieveKey(to_stop))
    cursor.close()
    db.close()
    return {"fare": fare}

# ---------------- DASHBOARD ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, card_id: str = None):

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    balance = None
    rides = []
    last_ride = None
    last_fare = None
    total_rides = 0
    status = "Active"

    if card_id:
        cursor.execute(
            "SELECT balance, status FROM cards WHERE card_id=%s",
            (card_id,)
        )
        card = cursor.fetchone()

        if card:
            balance = card["balance"]
            status = card["status"]

        cursor.execute(
            """
            SELECT transaction_time, description, amount
            FROM transactions
            WHERE card_id=%s
            ORDER BY transaction_time DESC
            """,
            (card_id,),
        )

        rides = cursor.fetchall()
        total_rides = len(rides)

        if rides:
            last_ride = rides[0]["description"]
            last_fare = rides[0]["amount"]

    cursor.close()
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "user": request.session.get("user"),
            "card_id": card_id,
            "balance": balance,
            "rides": rides,
            "last_ride": last_ride,
            "last_fare": last_fare,
            "total_rides": total_rides,
            "status": status,
        },
    )

# ---------------- ADMIN ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    card_id: str = None,
    day: str = None,
    date: str = None,
    month: str = None,
    year: str = None,
    bus_no: str = None,
    device_id: str = None,
    from_date: str = None,
    to_date: str = None,
    page: int = 1,
    all : str = None
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Pagination setup
    limit = 10
    offset = (page - 1) * limit

    # Build filter clause once
    filter_sql = ""
    params = []

    if card_id:
        filter_sql += " AND card_id=%s"
        params.append(card_id)
    if day:
        filter_sql += " AND DAY(transaction_time)=%s"
        params.append(day)
    if date:
        filter_sql += " AND DAY(transaction_time)=%s"
        params.append(date)
    if month:
        filter_sql += " AND MONTH(transaction_time)=%s"
        params.append(month)
    if year:
        filter_sql += " AND YEAR(transaction_time)=%s"
        params.append(year)
    if bus_no:
        filter_sql += " AND description LIKE %s"
        params.append(f"%{bus_no}%")
    if device_id:
        filter_sql += " AND description LIKE %s"
        params.append(f"%{device_id}%")
    if from_date and to_date:
        filter_sql += " AND DATE(transaction_time) BETWEEN %s AND %s"
        params.extend([from_date, to_date])

    filter_query = "&".join([
        f"{k}={v}" for k, v in {
            "card_id": card_id,
            "day": day,
            "date": date,
            "month": month,
            "year": year,
            "bus_no": bus_no,
            "device_id": device_id,
            "from_date": from_date,
            "to_date": to_date
        }.items() if v
    ])

    # Main query with pagination
    query = f"""
        SELECT transaction_id, type, card_id, description, amount, transaction_time, bus_no, device_id
        FROM transactions
        WHERE 1=1 {filter_sql}
        ORDER BY transaction_time DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, tuple(params + [limit, offset]))
    rides = cursor.fetchall()

    # Count query for total pages
    count_query = f"SELECT COUNT(*) AS total_count FROM transactions WHERE 1=1 {filter_sql}"
    cursor.execute(count_query, tuple(params))
    total_count = cursor.fetchone()["total_count"]
    total_pages = (total_count + limit - 1) // limit  # ceil division

    filters_applied = bool(card_id or day or date or month or year or bus_no or device_id or (from_date and to_date))
    show_all = bool(all)

    # Stats query (same filters, but type='ride')
    stats_query = f"""
        SELECT 
            COUNT(DISTINCT card_id) AS active_cards,
            SUM(amount) AS total_fare,
            COUNT(*) AS rides_count
        FROM transactions
        WHERE type='ride' {filter_sql}
    """
    if not filters_applied and not show_all:
        stats_query += " AND DATE(transaction_time) = CURDATE()"
    elif show_all:
        pass # no filter applied here, all transactions shown

    cursor.execute(stats_query, tuple(params))
    stats = cursor.fetchone()

    active_cards = stats["active_cards"] or 0
    total_fare = stats["total_fare"] or 0
    rides_today = stats["rides_count"] or 0

    cursor.close()
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "request": request,
            "user": require_admin(request),
            "rides": rides,
            "active_cards": active_cards,
            "total_fare": total_fare,
            "rides_today": rides_today,
            "page": page,
            "total_pages": total_pages,
            "filter_query": filter_query,
            "filters_applied": filters_applied,
            "show_all": show_all
        },
    )



# ---------------- RECHARGE ----------------
@app.get("/recharge", response_class=HTMLResponse)
def recharge_page(request: Request):

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # FETCH BALANCE ALWAYS
    cursor.execute(
        "SELECT balance FROM cards WHERE card_id=%s",
        (user["card_id"],)
    )
    card = cursor.fetchone()

    cursor.close()
    db.close()

    balance = card["balance"] if card else 0

    return templates.TemplateResponse(
        request=request,
        name="recharge.html",
        context={
            "request": request,
            "user": user,
            "balance": balance
        }
    )

@app.post("/recharge")
def recharge(request: Request, card_id: str = Form(...), amount: float = Form(...)):

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=303)

    if card_id != user["card_id"]:
        return templates.TemplateResponse(
            request=request,
            name="recharge.html",
            context={
                "request": request,
                "user": user,
                "error": "Invalid Card ID"
            }
        )

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # check if card exists
    cursor.execute(
        "SELECT * FROM cards WHERE card_id=%s",
        (card_id,)
    )
    card = cursor.fetchone()

    if not card:
        cursor.close()
        db.close()
        return templates.TemplateResponse(
            request=request,
            name="recharge.html",
            context={
                "request": request,
                "user": request.session.get("user"),
                "error": "Card not found"
            }
        )

    cursor.execute(
        "UPDATE cards SET balance = balance + %s WHERE card_id = %s",
        (amount, card_id),
    )
    db.commit()

    cursor.execute(
        "SELECT card_id, balance FROM cards WHERE card_id = %s",
        (card_id,),
    )
    card = cursor.fetchone()

    cursor.close()
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="recharge.html",
        context={
            "request": request,
            "user": request.session.get("user"),
            "card_id": card["card_id"],
            "balance": card["balance"],
            "success": True
        },
    )

# ---------------- LOGOUT ----------------
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

# ----profile profile ----
@app.get("/profile")
def profile(request: Request):

    session_user = request.session.get("user")

    # check if logged in
    if not session_user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        """
        SELECT
        l.first_name,l.last_name,l.email,l.phone,l.role,
        coalesce(l.card_id,c.card_id) AS card_id,
        coalesce(c.balance, 0) AS balance,
        l.profile_pic
        FROM login l
        LEFT JOIN cards c ON l.card_id = c.card_id
        WHERE l.id=%s
        """,
        (session_user["id"],),
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    # safety check
    if not user:
        return RedirectResponse("/login", status_code=303)

    pic = user.get("profile_pic")

    # fallback if NULL or file deleted
    disk_path = pic.lstrip("/") if pic else None

    if not pic or not os.path.exists(disk_path):

        pic = "/static/source/default.png"

        db2 = get_db()
        cursor2 = db2.cursor()

        cursor2.execute(
            "UPDATE login SET profile_pic=%s WHERE id=%s",
            (pic, session_user["id"])
        )

        db2.commit()
        cursor2.close()
        db2.close()

    user = {
        "first_name": user.get("first_name", "Rahul"),
        "last_name": user.get("last_name", "Kumar"),
        "role": user.get("role", "Admin"),
        "email": user.get("email", "rahul@example.com"),
        "card_id": user.get("card_id", "123456"),
        "balance": user.get("balance", 250),
        "profile_pic": pic,
    }

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "request": request,
            "user": user
        }
    )

@app.post("/profile")
async def update_profile(
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(...),
        photo: UploadFile = File(None)
    ):
    session_user = request.session.get("user")
    if not session_user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    file_path = None

    # VALIDATION (ONLY if file is selected)
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1].lower()
        if photo.content_type not in ["image/jpeg", "image/png"] or ext not in ["jpg", "jpeg", "png"]:

            cursor.execute(
                """
                SELECT
                    l.first_name,l.last_name,l.email,l.phone,l.role,
                    coalesce(l.card_id,c.card_id) AS card_id,
                    coalesce(c.balance, 0) AS balance,
                    l.profile_pic
                FROM login l
                LEFT JOIN cards c ON l.card_id = c.card_id
                WHERE l.id=%s
                """,
                (session_user["id"],)
            )

            user = cursor.fetchone()

            user = {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": user.get("role", ""),
                "email": user.get("email", ""),
                "card_id": user.get("card_id", ""),
                "balance": user.get("balance", 0),
                "profile_pic": user.get("profile_pic", None)
            }

            cursor.close()
            db.close()

            return templates.TemplateResponse(
                request=request,
                name="profile.html",
                context={
                    "request": request,
                    "user": user,
                    "error": "Only JPG/PNG/JPEG allowed"
                }
            )

    # SAVE IMAGE (ONLY if selected)
    if photo and photo.filename:
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # delete old image
        cursor.execute(
            "SELECT profile_pic FROM login WHERE id=%s",
            (session_user["id"],)
        )
        old_data = cursor.fetchone()

        if old_data and old_data.get("profile_pic"):
            old = old_data["profile_pic"]
            disk_old = old.lstrip("/") if old else None

            if old != "/static/source/default.png" and disk_old and os.path.exists(disk_old):
                os.remove(disk_old)

        # save new image
        ext = photo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        disk_path = os.path.join("static/uploads", filename)
        file_path = f"/static/uploads/{filename}"

        with open(disk_path, "wb") as f:
            f.write(await photo.read())

    # UPDATE DATABASE
    if file_path:
        cursor.execute(
            """
            UPDATE login
            SET first_name=%s, last_name=%s, email=%s, profile_pic=%s
            WHERE id=%s
            """,
            (first_name, last_name, email, file_path, session_user["id"])
        )
    else:
        cursor.execute(
            """
            UPDATE login
            SET first_name=%s, last_name=%s, email=%s
            WHERE id=%s
            """,
            (first_name, last_name, email, session_user["id"])
        )

    db.commit()

    # UPDATE SESSION
    request.session["user"]["first_name"] = first_name
    request.session["user"]["last_name"] = last_name
    request.session["user"]["email"] = email

    if file_path:
        request.session["user"]["profile_pic"] = file_path

    cursor.close()
    db.close()

    return RedirectResponse("/profile", status_code=303)

# Chatbot functionality
@app.post("/chat")
def chat(request: Request, message: str = Form(...)):

    # CHECK LOGIN FIRST
    user = request.session.get("user")

    if not user:

        return {
            "reply":
            "Please login to use the SmartBus AI Assistant."
        }

    # FAQ FOR LOGGED-IN USERS
    faq_answer = get_faq_answer(message)

    if faq_answer:

        return {
            "reply": faq_answer
        }

    # GEMINI FOR OTHER QUESTIONS
    try:

        prompt = (
            SYSTEM_PROMPT
            + "\n\nUser Question:\n"
            + message
        )

        response = model.generate_content(
            prompt
        )

        return {
            "reply": response.text
        }

    except Exception:

        return {
            "reply":
            "Sorry, I couldn't process your question at the moment."
        }