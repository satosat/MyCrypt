from flask import redirect, render_template, session
from functools import wraps

from pycoingecko import CoinGeckoAPI


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def new_lookup(assets, currencies):
    """
    Gets prices and 24H% change for cryptocurrencies using CoinGeckoAPI

    https://www.coingecko.com/en/api/documentation
    """

    # Creates new CoinGeckoAPI object
    cg = CoinGeckoAPI()

    # Return the call
    return cg.get_price(ids=assets, vs_currencies=currencies, include_24hr_change="true")


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def format_decimal(value):
    """Format value to 2 decimal places"""
    formatter = "{0:.2f}"
    return float(formatter.format(value))


def get_balance(db):
    """Gets user's cash balance"""
    balance = db.execute("SELECT cash FROM user WHERE id = ?", session['user_id'])

    return float(balance[0]['cash'])


def process_currency(curr):
    """Gets a formatted list of cryptocurrency to show in home.html"""
    assets = []
    for c in curr:
        assets.append(c['CGname'])

    data = new_lookup(assets, "usd")

    final_list = []
    i = 1
    for name, price in data.items():
        final_list.append({"id": i, "name": name, "price": usd(price['usd']),
                           "change24H": format_decimal(price["usd_24h_change"])})
        i += 1

    for c in final_list:
        for cc in curr:
            if c['name'] == cc['CGname']:
                c['name'] = cc['name']
                c['symbol'] = cc['symbol']
                c['CGname'] = cc['CGname']

    return final_list


def get_crypto_balance(db, user_id, symbol):
    """Gets balance of cryptocurrency"""
    balance = db.execute("SELECT * FROM ownership WHERE owner_id = ? AND symbol = ?",
                         user_id, symbol)

    if not balance:
        return 0
    else:
        return balance[0]['amount']


def parse_to_decimal(value, precision=6):
    """Parse value to 6 decimal place for cryptocurrency amount"""
    return f"{value:,.{precision}f}"


def get_assets(db):
    """Get ALL supported assets from crypto_list.db"""
    rows = db.execute("SELECT * FROM currencies")
    return rows


def search_asset(db, symbol):
    """Search if asset exist in db"""
    rows = db.execute("SELECT * FROM currencies WHERE symbol = ?", symbol)

    if not rows:
        return None

    return rows


def is_favorite(db, symbol):
    """Check is asset is in user's favorite list"""
    asset = db.execute("SELECT * FROM favorites WHERE user_id = ? AND symbol = ?", session['user_id'], symbol)

    if asset:
        return True

    return False


def get_gain(db, symbol, user_id):
    """Get user's gain on current asset"""

    asset = db.execute("SELECT * FROM ownership WHERE owner_id = ? AND symbol = ?", user_id, symbol)

    if not asset or float(asset[0]['money_spent']) == 0:
        return 0

    spent = float(asset[0]['money_spent'])
    gained = float(asset[0]['money_gained'])

    return parse_to_decimal(gained/spent, 2)
