import sys
import os
from flask import Flask
from cal_events import events_bp
from mail import mail


# Flask-Mail configuration for Outlook
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ['APP_SECRET_KEY']
    app.config['MAIL_SERVER'] = 'smtp.princeton.edu'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ['MAIL_ADDR']  # Replace with your Gmail address
    app.config['MAIL_PASSWORD'] = os.environ['MAIL_PWD']  # Use app password if 2FA is enabled

    mail.init_app(app)
    app.register_blueprint(events_bp)
    return app

app = create_app()

def main():
    port = int(os.getenv("PORT", 5000))  # Default to 5000 if PORT is not set

    try:
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()