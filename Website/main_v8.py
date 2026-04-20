from fastapi import Request, FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import pymysql
import random  # just for testing with random bus stop key
import threading
from fastapi import Form

# 🔴 ADD SESSION
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# 🔴 SESSION MIDDLEWARE
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CHANGE-1: bus stops - dictionary mapping stop IDs to names
stops = {0: "Stop A", 1: "Stop B", 2: "Stop C", 3: "Stop D"}


# Database connection
def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="smart_bus",
        cursorclass=pymysql.cursors.DictCursor,
    )


# CHANGE-2:fare table (Matrix representation)
fares = [[0, 8, 8, 10], [8, 0, 8, 10], [8, 8, 0, 8], [10, 10, 8, 0]]


# CHANGE-3: searching the fare between two stops
def get_fare(from_stop, to_stop):
    return fares[from_stop][to_stop]


# CHANGE-4: current stop
curStopKey = random.choice(
    list(stops.keys())
)  # current stop will be updated from keypad
curStop = stops[curStopKey]


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

    if user.get("role") != "admin":
        return HTMLResponse("Access Denied: Admins only", status_code=403)

    return user


# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, card_id: Optional[str] = None):

    user = request.session.get("user")
    if card_id == "None":
        card_id = None

    db = get_db()
    cursor = db.cursor()

    card = None
    trip = None

    if card_id:
        cursor.execute(
            "SELECT card_id, balance FROM cards WHERE card_id=%s", (card_id,)
        )
        card = cursor.fetchone()

        cursor.execute(
            """
            SELECT from_stop, to_stop, fare
            FROM rides
            WHERE card_id=%s
            ORDER BY id DESC LIMIT 1
            """,
            (card_id,),
        )
        trip = cursor.fetchone()

    cursor.close()
    db.close()

    balance = card["balance"] if card else 0

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": request.session.get("user"),
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
@app.get("/home", response_class=HTMLResponse)
def home_redirect(request: Request, card_id: Optional[str] = None):
    return RedirectResponse(url=f"/?card_id={card_id}", status_code=303)


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
        "INSERT INTO login(first_name, last_name, email, phone, password, role) VALUES(%s,%s,%s,%s,%s,%s)",
        (first_name, last_name, email, phone, password, role),
    )

    db.commit()

    cursor.close()
    db.close()

    return RedirectResponse("/login", status_code=303)


# ---------------- LOGIN ----------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


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
        }

        return RedirectResponse(url="/home", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
    )


# ---------------- SCAN ----------------


@app.post("/scan")
def scan_card(card_id: str = Form(...), keyStop: int = Form(...)):

    db = get_db()
    cursor = db.cursor()

    # ✅ Validate stop
    if keyStop not in stops:
        return {"error": f"Invalid stop: {keyStop}"}

    curStop = stops[keyStop]

    print("SCAN:", card_id, keyStop)

    # 🔍 Check for active ride
    cursor.execute(
        """
        SELECT r.from_stop, c.balance, c.status
        FROM rides r
        JOIN cards c ON r.card_id = c.card_id
        WHERE r.card_id=%s AND r.to_stop IS NULL
        LIMIT 1
    """,
        (card_id,),
    )

    active_ride = cursor.fetchone()

    # =========================
    # 🚩 TAP-2 → END RIDE
    # =========================
    if active_ride:
        from_stop = active_ride["from_stop"]
        balance = active_ride["balance"]
        status = active_ride["status"]

        # ❌ Card inactive
        if status != "active":
            return {"error": "Card is inactive"}

        to_stop = curStop

        # 🚫 DUPLICATE STOP CHECK (NEW)
        if from_stop == to_stop:
            return {
                "status": "duplicate tap",
                "message": "Tap ignored: Same stop scanned twice",
                "stop": to_stop,
            }

        from_key = retrieveKey(from_stop)

        if from_key is None:
            return {"error": f"Invalid from_stop: {from_stop}"}

        fare = get_fare(from_key, keyStop)

        if fare is None or fare < 0:
            return {"error": "Fare calculation failed"}

        if balance >= fare:
            new_balance = balance - fare

            # ✅ Update ride
            cursor.execute(
                """
                UPDATE rides 
                SET to_stop=%s, fare=%s
                WHERE card_id=%s AND to_stop IS NULL
            """,
                (to_stop, fare, card_id),
            )

            # ✅ Update balance
            cursor.execute(
                """
                UPDATE cards 
                SET balance=%s
                WHERE card_id=%s
            """,
                (new_balance, card_id),
            )

            # ✅ Store transaction
            description = f"{from_stop} → {to_stop}"
            cursor.execute(
                """
                INSERT INTO transactions(type, card_id, description, amount)
                VALUES(%s,%s,%s,%s)
            """,
                ("ride", card_id, description, fare),
            )

            db.commit()

            return {
                "status": "ride completed",
                "from": from_stop,
                "to": to_stop,
                "fare": fare,
                "balance": new_balance,
            }

        else:
            return {
                "status": "insufficient balance",
                "balance": balance,
                "required": fare,
            }

    # =========================
    # 🚩 TAP-1 → START RIDE
    # =========================
    else:
        cursor.execute("SELECT * FROM cards WHERE card_id=%s", (card_id,))
        existing_card = cursor.fetchone()

        if not existing_card:
            cursor.execute(
                """
                INSERT INTO cards(card_id, balance, status)
                VALUES(%s,%s,%s)
            """,
                (card_id, 100, "active"),
            )
        else:
            if existing_card["status"] != "active":
                return {"error": "Card is inactive"}

        # 🔒 Extra safety
        cursor.execute(
            """
            SELECT * FROM rides
            WHERE card_id=%s AND to_stop IS NULL
        """,
            (card_id,),
        )

        if cursor.fetchone():
            return {"error": "Ride already in progress"}

        # ✅ Start ride
        cursor.execute(
            """
            INSERT INTO rides(card_id, from_stop, to_stop, fare)
            VALUES(%s,%s,%s,%s)
        """,
            (card_id, curStop, None, 0),
        )

        db.commit()

        return {"status": "ride started", "from": curStop, "card_id": card_id}


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
        cursor.execute("SELECT balance, status FROM cards WHERE card_id=%s", (card_id,))
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
        "dashboard.html",
        {
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
def admin_dashboard(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        """
        SELECT transaction_id, type, card_id, description, amount, transaction_time
        FROM transactions
        ORDER BY transaction_time DESC
        """
    )
    rides = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(DISTINCT card_id) AS active_cards
        FROM cards
        WHERE status = 'active'
    """
    )
    active_cards = cursor.fetchone()["active_cards"]

    cursor.execute(
        """
        SELECT SUM(amount) AS total_fare
        FROM transactions
        WHERE type='ride' AND DATE(transaction_time) = CURDATE()
    """
    )
    result = cursor.fetchone()
    total_fare = result["total_fare"] if result["total_fare"] else 0

    cursor.execute(
        """
        SELECT COUNT(*) AS rides_today
        FROM transactions
        WHERE type='ride' AND DATE(transaction_time) = CURDATE()
    """
    )
    rides_today = cursor.fetchone()["rides_today"]

    cursor.close()
    db.close()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user,
            "user": require_admin(request),
            "rides": rides,
            "active_cards": active_cards,
            "total_fare": total_fare,
            "rides_today": rides_today,
        },
    )


# ---------------- RECHARGE ----------------
@app.get("/recharge", response_class=HTMLResponse)
def recharge_page(request: Request):

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "recharge.html", {"request": request, "user": user}
    )


@app.post("/recharge")
def recharge(request: Request, card_id: str = Form(...), amount: float = Form(...)):

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # ✅ check if card exists
    cursor.execute("SELECT balance FROM cards WHERE card_id=%s", (card_id,))
    card = cursor.fetchone()

    if not card:
        cursor.close()
        db.close()
        return templates.TemplateResponse(
            "recharge.html",
            {"request": request, "error": "Card not found"},
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
        "recharge.html",
        {
            "request": request,
            "user": request.session.get("user"),
            "card_id": card["card_id"],
            "balance": card["balance"],
        },
    )


# ---------------- LOGOUT ----------------
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/profile")
def profile(request: Request):

    session_user = request.session.get("user")

    # ✅ check if logged in
    if not session_user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)  # ✅ IMPORTANT

    cursor.execute(
        """
    SELECT 
        l.first_name, 
        l.last_name, 
        l.email, 
        l.phone, 
        l.role, 
        c.card_id, 
        c.balance 
    FROM login l
    LEFT JOIN cards c ON l.card_id = c.card_id
    WHERE l.id=%s
    """,
        (session_user["id"],),
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    # ✅ safety check
    if not user:
        return RedirectResponse("/login", status_code=303)

    # ✅ optional defaults
    user = {
        "first_name": user.get("first_name", "Rahul"),
        "last_name": user.get("last_name", "Kumar"),
        "role": user.get("role", "Admin"),
        "email": user.get("email", "rahul@example.com"),
        "card_id": user.get("card_id", "123456"),
        "balance": user.get("balance", 250),
    }

    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user}
    )


@app.post("/profile")
async def update_profile(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
):
    print(first_name, last_name, email)

    session_user = request.session.get("user")
    if not session_user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        """
            UPDATE login
            SET first_name=%s, last_name=%s, email=%s
            WHERE id=%s
        """,
        (first_name, last_name, email, session_user["id"]),
    )
    db.commit()

    cursor.close()
    db.close()

    request.session["user"]["first_name"] = first_name
    request.session["user"]["last_name"] = last_name
    request.session["user"]["email"] = email

    return RedirectResponse("/profile", status_code=303)
