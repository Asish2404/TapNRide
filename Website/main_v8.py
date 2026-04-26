from fastapi import Request, FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import pymysql
import random  # just for testing with random bus stop key
import threading
import os, uuid

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
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT")),
        cursorclass=pymysql.cursors.DictCursor,
    )

# CHANGE-2:fare table (Matrix representation)
fares = [[0, 8, 8, 10], [8, 0, 8, 10], [8, 8, 0, 8], [10, 10, 8, 0]]


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

    cursor.execute("SELECT card_id FROM cards_in_stock WHERE status='OPEN' LIMIT 1")

    row = cursor.fetchone()
    if not row:
        return RedirectResponse(
            url="/login?error=No available cards in stock", status_code=303
        )

    card_id = row["card_id"]  # allocate a unique card ID for the new user

    cursor.execute(
        """
        INSERT INTO login(card_id, first_name, last_name, email, phone, password, role, profile_pic)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            card_id,
            first_name,
            last_name,
            email,
            phone,
            password,
            role,
            "static/source/default.png"
        ),
    )

    cursor.execute(
        "UPDATE cards_in_stock SET status='CLOSED' WHERE card_id=%s", (card_id,)
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
            "profile_pic": user.get("profile_pic") or "static/source/default.png",
        }

        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": "Invalid credentials",
        },
    )

# ---------------- SCAN ----------------

@app.post("/scan")
def scan_card(card_id: str = Form(...), keyStop: int = Form(...)):

    db = get_db()
    cursor = db.cursor()

    # Validate stop
    if keyStop not in stops:
        return {"error": f"Invalid stop: {keyStop}"}

    curStop = stops[keyStop]

    print("SCAN:", card_id, keyStop)

    # Check for active ride
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
            (card_id,),
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
                    "UPDATE rides SET to_stop=%s, fare=%s WHERE card_id=%s AND to_stop IS NULL",
                    (to_stop, fare, card_id),
                )

                # Update balance
                cursor.execute(
                    "UPDATE cards SET balance=%s WHERE card_id=%s",
                    (new_balance, card_id),
                )

                # Store transaction
                description = f"{from_stop} → {to_stop}"
                cursor.execute(
                    "INSERT INTO transactions(type, card_id, description, amount) VALUES(%s,%s,%s,%s)",
                    ("ride", card_id, description, fare),
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
                    "balance": new_balance,
                }

            else:
                return {
                    "status": "insufficient balance",
                    "card_id": card_id,
                    "balance": balance,
                    "required": fare,
                }

        # normal fare calculation - no pending rides(through plan_ride)
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
                SET to_stop=%s, fare=%s
                WHERE card_id=%s AND to_stop IS NULL
                """,
                (to_stop, fare, card_id),
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
                INSERT INTO transactions(type, card_id, description, amount)
                VALUES(%s,%s,%s,%s)
                """,
                ("ride", card_id, description, fare),
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

        if not existing_card:
            cursor.execute(
                """
                INSERT INTO cards(card_id, balance, status)
                VALUES(%s,%s,%s)
                """,
                (card_id, 0.00, "active"),
            )
            db.commit()
        else:
            if existing_card["status"] != "active":
                return {"error": "Card is inactive"}

        balance = existing_card["balance"]

        if balance <= 0:
            return {
                "status": "low balance",
                "card_id": card_id,
                "balance": balance,
                "message": "Please recharge your card to start a ride",
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
            INSERT INTO rides(card_id, from_stop, to_stop, fare)
            VALUES(%s,%s,%s,%s)
            """,
            (card_id, curStop, None, 0),
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


# NEW ADDITION-------- plan rides before reaching destination ----------------
@app.post("/plan_ride")
def plan_ride(
    card_id: str = Form(...),
    Starting_place: str = Form(None),   # auto-detected
    Ending_place: str = Form(...),      # passenger-selected to_stop
    fare: float = Form(None),           # auto-calculated
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
        (card_id,),
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
            "to_stop": Ending_place,
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
        (card_id, from_stop, Ending_place, fare),
    )
    db.commit()

    cursor.close()
    db.close()

    return RedirectResponse(
        url=f"/dashboard?card_id={card_id}",
        status_code=303
    )

# -----------------------New addition for dashboard display-----------------------


# ---------------------- fetch active ride details - source stop of corresponding card_id----------------------
@app.get("/get_active_ride")
def get_active_ride(card_id: str):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "SELECT from_stop FROM rides WHERE card_id=%s AND to_stop IS NULL LIMIT 1",
        (card_id,),
    )
    active = cursor.fetchone()
    cursor.close()
    db.close()
    return {"from_stop": active["from_stop"] if active else None}

# ----------------------fetch fare for the active ride as per planned destination----------------------
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
        request=request,
        name="admin.html",
        context={
            "request": request,
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
            "balance": balance,
        },
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
                "error": "Invalid Card ID",
            },
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
                "error": "Card not found",
            },
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
            "success": True,
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
    cursor = db.cursor(pymysql.cursors.DictCursor)  # IMPORTANT

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
    if not pic or not os.path.exists(pic):
        pic = "static/source/default.png"

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
    photo: UploadFile = File(None),
    ):
    session_user = request.session.get("user")
    if not session_user:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    file_path = None

    # VALIDATION (ONLY if file is selected)
    if photo and photo.filename:
        if photo.content_type not in ["image/jpeg", "image/png", "image/jpg"]:

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

            user = {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": user.get("role", ""),
                "email": user.get("email", ""),
                "card_id": user.get("card_id", ""),
                "balance": user.get("balance", 0),
                "profile_pic": user.get("profile_pic", None),
            }

            cursor.close()
            db.close()

            return templates.TemplateResponse(
                request=request,
                name="profile.html",
                context={
                    "request": request,
                    "user": user,
                    "error": "Only JPG/PNG/JPEG allowed",
                },
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
            if old != "static/default.png" and os.path.exists(old):
                os.remove(old)

        # save new image
        ext = photo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(await photo.read())

    # UPDATE DATABASE
    if file_path:
        cursor.execute(
            """
            UPDATE login
            SET first_name=%s, last_name=%s, email=%s, profile_pic=%s
            WHERE id=%s
            """,
            (first_name, last_name, email, file_path, session_user["id"]),
        )
    else:
        cursor.execute(
            """
            UPDATE login
            SET first_name=%s, last_name=%s, email=%s
            WHERE id=%s
            """,
            (first_name, last_name, email, session_user["id"]),
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
