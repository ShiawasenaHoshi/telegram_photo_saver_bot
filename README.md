# Telegram photo saver bot
Bot for saving and manage photo from chats.
# Install
1) ```sudo apt-get install python3 git```
2) ```git clone git@github.com:ShiawasenaHoshi/telegram_photo_saver_bot.git; cd telegram_photo_saver_bot```
3) ```python3 -m venv venv; source venv/bin/activate; export FLASK_APP=bot.py;pip install -r requirements.txt; flask db upgrade```
4) Create ```.env``` in project directory and define further variables in it:
YD_TOKEN=<yandex disk token>
TG_TOKEN=<telegram token>
TG_ADMIN_ID=<telegram bot owner id>
WEBHOOK_HOST=<VPS ip>
5) ```openssl genrsa -out webhook_pkey.pem 2048; openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem```
When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply with the same value in you put in WEBHOOK_HOST
6) ```python start.py```
