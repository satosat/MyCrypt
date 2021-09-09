from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta

from helpers import login_required, apology, usd, process_currency, get_balance, new_lookup, get_crypto_balance, \
    search_asset, parse_to_decimal, get_assets, is_favorite, get_gain

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Clears session 1 hour after user inactivity
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")

# Connect to list of currencies supported in database
currencies = SQL("sqlite:///crypto_list.db")


@app.route("/")
@login_required
def index():
    # Gets list of currencies to display
    curr = get_assets(currencies)

    # process the currencies
    final_list = process_currency(curr)

    # Gets user's balance to display
    balance = get_balance(db)

    return render_template("home.html", assets=final_list, balance=usd(balance))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    else:
        # Validate form inputs
        if not request.form.get('username'):
            return apology('Missing username')
        elif not request.form.get('password'):
            return apology('Missing password')

        # Query username
        pwhash = db.execute("SELECT id, hash FROM user WHERE username = ?", request.form.get('username'))

        # Check username
        if not pwhash:
            return apology("Username doesn't exist")
        elif not check_password_hash(pwhash[0]["hash"], request.form.get('password')):
            return apology("Password doesn't match")

        # Store user session using user's id
        session["user_id"] = pwhash[0]["id"]

        return redirect('/')


@app.route('/logout', methods=["GET"])
@login_required
def logout():
    """Logs user out"""

    # Clear any session
    session.clear()

    # Redirect to home page
    return redirect('/login')


@app.route('/register', methods=["GET", "POST"])
def register():
    """Register new user"""
    if request.method == "GET":
        return render_template('register.html')

    else:
        # Check form inputs
        if not request.form.get('username'):
            return apology("Blank Username")
        elif not request.form.get('email'):
            return apology("Blank Email")
        elif not request.form.get('password'):
            return apology("Blank Password")
        elif not request.form.get('confirm_password'):
            return apology("Password don't match")
        elif request.form.get("password") != request.form.get('confirm_password'):
            return apology("Password don't match")

        # Query user from db
        username = db.execute("SELECT * FROM user WHERE username = ?", request.form.get('username'))
        email = db.execute("SELECT * FROM user WHERE email = ?", request.form.get('email'))

        # Check if username and email is taken
        if username:
            return apology("Username is taken")
        elif email:
            return apology("Email has been registered previously")

        # Register user
        db.execute("""INSERT INTO user (username, email, hash, cash) VALUES (?, ?, ?, ?)""",
                   request.form.get('username'), request.form.get('email'),
                   generate_password_hash(request.form.get('password')), 10000)

        return redirect('/login')


@app.route('/favorites')
@login_required
def favorites():
    """Shows user's favorite cryptocurrencies"""

    # Query user's favorite
    curr = db.execute("SELECT * FROM favorites WHERE user_id = ?", session["user_id"])

    # Parse and format the currencies
    final_list = process_currency(curr)

    # Get user's balance
    balance = get_balance(db)

    return render_template("home.html", assets=final_list, balance=usd(balance))


@app.route('/deposit', methods=["GET", "POST"])
@login_required
def deposit():
    """Allow user to deposit (dummy) money"""

    # Get user balance
    user_balance = get_balance(db)

    if request.method == "POST":
        if not request.form.get('amount'):
            return apology("Missing amount")
        elif float(request.form.get('amount')) <= 0:
            return apology("Amount must be a positive number")

        deposit_amount = float(request.form.get('amount'))

        db.execute("UPDATE user SET cash = ? WHERE id = ?", deposit_amount + user_balance, session["user_id"])

        return redirect('/favorites')
    else:
        return render_template("deposit.html", balance=usd(user_balance))


@app.route('/asset', methods=["GET", "POST"])
@login_required
def asset():
    # Get symbol from query (/asset?symbol=symbol_name)
    symbol = request.args.get('name')

    # Search for asset from currencies db through search_asset()
    cc = search_asset(currencies, symbol)

    # Checks if asset is in db
    if not cc:
        return apology("Invalid Symbol")

    # Get user info & balance
    user_info = db.execute("SELECT * FROM user WHERE id = ?", session["user_id"])
    balance = float(user_info[0]['cash'])

    # Parse and format cryptocurrency
    cc = process_currency(cc)

    # Get user's asset balance
    asset_balance = get_crypto_balance(db, session['user_id'], symbol)

    # Checks if user has favor the currency (for button text)
    if is_favorite(db, symbol):
        fav = "Remove from Favorites"
    else:
        fav = "Add to Favorites"

    gain = get_gain(db, symbol, session['user_id'])

    if request.method == "GET":
        return render_template("asset.html", asset=cc[0], asset_balance=parse_to_decimal(asset_balance), balance=usd(balance), fav=fav, gain=gain)

    """ Below are code for POST requests (handle transactions) """

    # Check if user already own the requested cc
    owned = db.execute("SELECT * FROM ownership WHERE owner_id = ? AND symbol = ?", session['user_id'], symbol)

    # Get current price of the currency
    price = new_lookup(cc[0]['CGname'], "USD")
    price = float(price[cc[0]['CGname']]['usd'])

    if request.form['submit'] == 'Sell':
        if not request.form.get('coin-amount'):
            return apology("Missing Amount")
        elif float(request.form.get('coin-amount')) <= 0:
            return apology("Amount must be more than 0")
        elif not owned:
            return apology("You don't own any amount of the cryptocurrency")
        elif float(request.form.get('coin-amount')) > float(owned[0]['amount']):
            return apology("Can't sell more than you own")

        crypto_owned = float(owned[0]['amount'])
        sell_amount = float(request.form.get('coin-amount'))

        sell_gain = float(sell_amount * price)
        money_gained = float(owned[0]['money_gained'])
        money_gained += sell_gain

        crypto_owned = crypto_owned - sell_amount;

        # Update user's cash
        db.execute("UPDATE user SET cash = ? WHERE id = ?", balance + sell_gain, session['user_id'])

        # Update user's crypto ownership
        db.execute("UPDATE ownership SET amount = ?, money_gained = ? WHERE owner_id = ? AND symbol = ?",
                   crypto_owned, money_gained, session['user_id'], symbol)

    elif request.form['submit'] == "Buy":
        if not request.form.get('usd-amount'):
            return apology('missing amount')
        elif float(request.form.get('usd-amount')) <= 0:
            return apology('Amount must be more than 0')
        elif float(request.form.get('usd-amount')) > balance:
            return apology('Insufficient balance')

        crypto_owned = 0
        money_spent = 0

        if owned:
            crypto_owned = float(owned[0]['amount'])
            money_spent = float(owned[0]['money_spent'])

        buy_amount = float(request.form.get('usd-amount'))
        money_spent += buy_amount
        crypto_owned += buy_amount/price

        balance = balance - buy_amount

        db.execute("UPDATE user SET cash = ? WHERE id = ?",
                   balance, session['user_id'])

        if owned:
            db.execute("UPDATE ownership set amount = ?, money_spent = ? WHERE owner_id = ? AND symbol = ?",
                       crypto_owned, money_spent, session['user_id'], symbol)
        else:
            db.execute("""INSERT INTO ownership (owner_id, symbol, name, money_spent, money_gained, amount) 
            VALUES (?,?,?,?,?,?)""", session["user_id"], symbol, cc[0]['name'], money_spent, 0, crypto_owned)

    return redirect(f'/asset?name={symbol}')


@app.route('/buy', methods=["POST"])
@login_required
def buy():
    # Validate form
    if not request.form.get('amount'):
        return apology("Missing amount")
    elif float(request.form.get('amount')) <= 0:
        return apology("Amount must be more than 0")

    # Get symbol from query
    symbol = request.args.get('name')

    # Check if asset exists
    cc = currencies.execute("SELECT * FROM currencies WHERE symbol = ?", symbol)

    if not cc:
        return apology("Invalid Symbol")

    # Check if user already own the requested cc
    owned = db.execute("SELECT * FROM ownership WHERE owner_id = ? AND symbol = ?", session['user_id'], symbol)

    # Process transaction
    amount = float(request.form.get("amount"))

    # Check if user has enough money
    balance = db.execute("SELECT cash FROM user WHERE id = ?", session["user_id"])
    balance = float(balance[0]['cash'])

    if balance < amount:
        return apology("Not enought balance")

    # Get asset's current price
    price = new_lookup(cc[0]['CGname'], "USD")
    price = float(price[cc[0]['CGname']]['usd'])

    # Calculate total asset bought
    total_bought = float(amount / price)

    if owned:
        db.execute("UPDATE ownership SET amount = ?, money_spent = ? WHERE owner_id = ? AND symbol = ?",
                   owned[0]['amount'] + total_bought, owned[0]['money_spent'] + amount, session['user_id'], symbol)
    else:
        db.execute("""INSERT INTO ownership (owner_id, symbol, name, money_spent, money_gained, amount)
                      VALUES (?,?,?,?,?,?)""", session['user_id'], symbol, cc[0]['name'], amount, 0, total_bought)

    # Update user's cash
    db.execute("UPDATE user SET cash = ? WHERE id = ?",
               balance - amount, session["user_id"])

    return redirect(f'/asset?name={symbol}')


@app.route('/get-price', methods=["POST"])
@login_required
def get_price():
    """Get current asset price for sel and buy price approximation"""

    # Get parameters
    action = request.args.get('action')
    symbol = request.args.get('name')

    # Search if currency exist
    cc = currencies.execute("SELECT * FROM currencies WHERE symbol = ?", symbol)

    if not cc:
        return jsonify([])

    # Get asset info
    asset_info = new_lookup(cc[0]['CGname'], "USD")

    if action == "lookup":
        return jsonify(float(asset_info[cc[0]['CGname']]['usd']))
    else:
        return jsonify(0)


@app.route('/add-fav', methods=["POST"])
@login_required
def add_fav():
    """Adds currency to user's favorite list"""

    # Get parameter
    symbol = request.args.get('name')

    # Search currency
    cc = search_asset(currencies, symbol)

    if not cc:
        return apology("Asset not supported")

    if is_favorite(db, symbol):
        db.execute("DELETE FROM favorites WHERE user_id = ? AND symbol = ?", session['user_id'], symbol)
        return "not fav"
    else:
        db.execute("INSERT INTO favorites (user_id, symbol, name, CGname) VALUES (?,?,?,?)",
                   session['user_id'], cc[0]['symbol'], cc[0]['name'], cc[0]['CGname'])
        return "fav"


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8080')
