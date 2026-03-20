from fastapi import Request, FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import datetime
import pymysql

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Database connection
def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="smart_bus",
        cursorclass=pymysql.cursors.DictCursor,
    )


@app.get("/home", response_class=HTMLResponse)
def home(request: Request, card_id: Optional[str] = None):

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)  # ✅ FIXED

    card = None
    trip = None

    if card_id:
        cursor.execute(
            "SELECT card_id, balance FROM cards WHERE card_id=%s", (card_id,)
        )
        card = cursor.fetchone()

        cursor.execute(
            """
            SELECT from_stop, to_stop, fare, timestamp
            FROM rides
            WHERE card_id=%s
            ORDER BY id DESC LIMIT 1
        """,
            (card_id,),
        )
        trip = cursor.fetchone()

    # ✅ Safe time formatting
    if trip and trip.get("timestamp"):
        ts = trip["timestamp"]
        if isinstance(ts, str):
            ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        time_str = ts.strftime("%I:%M %p")
    else:
        time_str = "N/A"

    cursor.close()
    db.close()

    balance = card["balance"] if card else 0

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "balance": balance,
            "card_id": card["card_id"] if card else "N/A",
            "from_stop": trip["from_stop"] if trip else "N/A",
            "to_stop": trip["to_stop"] if trip else "N/A",
            "fare": trip["fare"] if trip else 0,
            "updated_time": time_str,
            "status": "Active" if balance > 0 else "Low Balance",
        },
    )


@app.post("/scan", response_class=HTMLResponse)
def scan_card(card_id: str, from_stop: str, to_stop: str):
    db = get_db()
    cursor = db.cursor()
    # fare amount
    fare = 10
    # check if card exists
    cursor.execute("SELECT * FROM cards WHERE card_id=%s", (card_id,))
    card = cursor.fetchone()
    if card:
        balance = card["balance"]
        if balance >= fare:
            new_balance = balance - fare
            # update balance
            cursor.execute(
                "UPDATE cards SET balance=%s WHERE card_id=%s", (new_balance, card_id)
            )
            # insert ride record
            cursor.execute(
                "INSERT INTO rides(card_id, from_stop, to_stop, fare) VALUES(%s,%s,%s,%s)",
                (card_id, from_stop, to_stop, fare),
            )
            # insert transaction record
            description = f"{from_stop} → {to_stop}"
            cursor.execute(
                "INSERT INTO transactions(type, card_id, description, amount) VALUES(%s,%s,%s,%s)",
                ("ride", card_id, description, fare),
            )
            db.commit()
            return {
                "status": "ride successful",
                "card_id": card_id,
                "fare": fare,
                "balance": new_balance,
            }
        else:
            return {"status": "insufficient balance", "balance": balance}
    else:
        # register new card automatically
        cursor.execute(
            "INSERT INTO cards(card_id, balance, status) VALUES(%s,%s,%s)",
            (card_id, 100, "active"),
        )
        db.commit()
        return {"status": "new card registered", "card_id": card_id, "balance": 100}


@app.post("/tap_card")
def tap_card(
    card_id: str = Form(...),
    fare: float = Form(...),
    Starting_place: str = Form(...),
    Ending_place: str = Form(...),
):

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT balance FROM cards WHERE card_id=%s", (card_id,))
    card = cursor.fetchone()

    if not card:
        cursor.close()
        db.close()
        return {"status": "Card not found"}

    balance = card["balance"]

    if balance < fare:
        cursor.close()
        db.close()
        return {"status": "Insufficient balance"}

    # Deduct balance
    cursor.execute(
        "UPDATE cards SET balance = balance - %s WHERE card_id=%s",
        (fare, card_id),
    )

    # Save ride
    cursor.execute(
        """
        INSERT INTO rides(card_id, from_stop, to_stop, fare)
        VALUES (%s,%s,%s,%s)
        """,
        (card_id, Starting_place, Ending_place, fare),
    )

    description = f"{Starting_place} → {Ending_place}"

    # Save transaction
    cursor.execute(
        """
        INSERT INTO transactions(type, card_id, description, amount)
        VALUES (%s,%s,%s,%s)
        """,
        ("Ride", card_id, description, fare),
    )

    db.commit()

    cursor.close()
    db.close()

    return RedirectResponse(url=f"/dashboard?card_id={card_id}", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, card_id: str = None):

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    balance = None
    rides = []
    last_ride = None
    last_fare = None
    total_rides = 0
    status = "Active"

    if card_id:

        # get balance + status
        cursor.execute("SELECT balance, status FROM cards WHERE card_id=%s", (card_id,))
        card = cursor.fetchone()

        if card:
            balance = card["balance"]
            status = card["status"]

        # get all rides
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
            "card_id": card_id,
            "balance": balance,
            "rides": rides,
            "last_ride": last_ride,
            "last_fare": last_fare,
            "total_rides": total_rides,
            "status": status,
        },
    )


@app.post("/rides")
def create_ride(card_id: str, from_stop: str, to_stop: str, fare: float):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO rides(card_id, from_stop, to_stop, fare)
        VALUES (%s,%s,%s,%s)
        """,
        (card_id, from_stop, to_stop, fare),
    )
    description = f"{from_stop} → {to_stop}"
    cursor.execute(
        """
        INSERT INTO transactions(type, card_id, description, amount)
        VALUES (%s,%s,%s,%s)
        """,
        ("Ride", card_id, description, fare),
    )

    db.commit()
    return {
        "message": "Ride recorded successfully",
        "card_id": card_id,
        "from": from_stop,
        "to": to_stop,
        "fare": fare,
    }


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
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
        WHERE status = 'active';
    """
    )
    active_cards = cursor.fetchone()["active_cards"]
    cursor.execute(
        """
        SELECT SUM(amount) AS TotalFareCollected
        FROM transactions
        WHERE type='ride' AND DATE(transaction_time) = CURDATE();
    """
    )
    total_fare = cursor.fetchone()["TotalFareCollected"]

    cursor.execute(
        """
        SELECT COUNT(*) AS rides_today
        FROM transactions
        WHERE type='ride' AND DATE(transaction_time) = CURDATE();
    """
    )
    rides_today = cursor.fetchone()["rides_today"]

    cursor.close()

    db.close()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "rides": rides,
            "active_cards": active_cards,
            "total_fare": total_fare,
            "rides_today": rides_today,
        },
    )


@app.get("/recharge", response_class=HTMLResponse)
def recharge_page(request: Request):
    return templates.TemplateResponse("recharge.html", {"request": request})


@app.post("/recharge", response_class=HTMLResponse)
def recharge(request: Request, card_id: str = Form(...), amount: float = Form(...)):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "UPDATE cards SET balance = balance + %s WHERE card_id = %s", (amount, card_id)
    )
    db.commit()
    cursor.execute("SELECT card_id, balance FROM cards WHERE card_id = %s", (card_id,))
    card = cursor.fetchone()
    cursor.close()
    db.close()
    return templates.TemplateResponse(
        "recharge.html",
        {"request": request, "card_id": card["card_id"], "balance": card["balance"]},
    )
