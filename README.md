# Telegram photo saver bot
Bot for saving and manage photo from chats.

# Installation
1) ```sudo apt-get install python3 git```
2) ```git clone git@github.com:ShiawasenaHoshi/telegram_photo_saver_bot.git; cd telegram_photo_saver_bot```
3) ```python3 -m venv venv; source venv/bin/activate; export FLASK_APP=bot.py;pip install -r requirements.txt; flask db upgrade```
4) Copy ```.env.example``` to ```.env``` and change the YD_TOKEN, TG_TOKEN, TG_ADMIN_ID
 
 If you will use this bot from the local machine, then skip next section and go to ``Starting the bot``.
 
## On production server
On production server follow these steps: 
1) ```openssl genrsa -out webhook_pkey.pem 2048; openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem```
When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply with the same value in you put in WEBHOOK_HOST
2) Set ```WEBHOOK_ENABLE=1``` in ```.env```

## Starting the bot 
1) ```python start.py```
