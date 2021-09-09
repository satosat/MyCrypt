#MyCrypt
___
###A dummy cryptocurrency exchange where you can buy and sell crypto assets with dummy money made as a Final Project for CS50x
___
##Overview
To complete Harvard's [CS50x](https://cs50.harvard.edu/x/2021/), I made this dummy cryptocurrency exchange that allows user to buy and sell cryptocurrencies using Flask as the backend framework.

Because of the popularity that cryptocurrency gained over the past few months, I'd like to introduce them to some of my friends who are still unsure about it. This way, they can buy and sell some assets without having to spend any money and can also keep track of their gains.

The prices are taken in realtime using [CoinGecko's API](https://www.coingecko.com/en/api/documentation). So massive shout out to them who has provided a very powerful API for free and making such good documentations for it.

Charts are provided by the lovely team at [TradingView](https://www.tradingview.com/widget/advanced-chart/).
___
##Technologies
This project is built with:
* Python 3.9
* Flask 2.0.1
* Werkzeug 2.0.1
* pycoingecko 2.2.0
* cs50 7.0.2
* Boostrap 5.1.0
* jQuery 3.6.0
* SQLite3
___
##Setup
To run on port **5000** simply run 
```bash
flask run
```
Optionally, you can also run
```bash
python app.py
```
to run it on port **8080**
___
##Databases
###users.db
![users.db schema](static/schema.png)
Consists of 3 tables:
  * `user` which stores user information and credentials, consists of 5 columns:
    * `id`: Primary Key
    * `username`
    * `email`
    * `hash`: User's hashed password
    * `cash`: User's cash balance
  * `favorites` which stores the list of cryptocurrency assets that are favorited by the user. Consisted of 4 columns:
    * `user_id`: Foreign key referencing `username` on `user` table
    * `symbol`: Asset's symbol (BTC, ETH, etc.)
    * `name`: Asset's name (Bitcoin, Ethereum, etc.)
    * `CGname`: Short for CoinGecko name, asset's index key to search using CoinGecko's API
  * `ownersip` which stores the list of cryptocurrency assets that the user owns. Consisted of 6 tables:
    * `owner_id`: Foreign key referencing `username` on `user` table
    * `symbol`: Asset's symbol (BTC, ETH, etc.)
    * `name`: Asset's name (Bitcoin, Ethereum, etc.)
    * `money_spent`: Amount of money spent on this cryptocurrency
    * `money_gained`: Amount of money gained on this cryptocurrency
    * `amount`: Amount of cryptocurrency held
###crypto_list.db
Consists of 1 table:
  * `currencies` which stores the list of cryptocurrencies that are supported. Consisted of 4 columns:
    * `id`
    * `name`: asset's name
    * `symbol`: asset's symbol
    * `CGname`: short for CoinGecko name, for which is the symbol used by the CoinGecko's API .
  * `currencies` is also indexed by `currency` that indexes on columns `id` and `name` 
  * If you want to add your own list of asset, you can add it here!
___
##Upgrades
* Database: Although I've made the database as efficient possible to search (with my limited knowledge), I still feel that it can definitely be improved on.
* Mobile compatibility: Even though I design this for both mobile and desktop, the mobile version still needs tweaks and upgrades.
___

