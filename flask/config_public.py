import os


class Config(object):
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'ASDFSASFDSDDSSWWERASD'
    SERVER_NAME = 'localhost:5000'
    AC_KEY = "***"
    AC_URL = "https://***.api-us1.com/api/3/"
    STRIPE_PUBLIC_KEY = "pk_test_***"
    STRIPE_SECRET_KEY = "sk_test_***"
    SENDGRID_API_KEY = "SG.***"
    SENDER_MAIL = "order@salina.maris.ch"
    INTERNAL_MAIL = "info@salina.maris.ch"