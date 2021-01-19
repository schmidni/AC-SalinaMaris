from flask import Blueprint, render_template, url_for, current_app, request, abort

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import stripe
import json

payment = Blueprint('payment', __name__,
                    template_folder='templates', url_prefix='/payment')

from project.extensions import csrf


@payment.record
def record_config(setup_state):
    stripe.api_key = setup_state.app.config['STRIPE_SECRET_KEY']


@ payment.route('/products')
def products():
    angebote = read_gutscheine()
    return render_template('payment/products.html', angebote=angebote)


@ payment.route('/thanks')
def thanks():
    return render_template('payment/thanks.html')


@ payment.route('/stripe_pay')
def stripe_pay():
    id = request.args.get('id', None)

    try:
        if id:
            angebot = read_gutscheine()[int(id)]
        else:
            return {'error': 'No Product ID'}, 403

        session = stripe.checkout.Session.create(
            billing_address_collection='required',
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'chf',
                    'unit_amount': angebot['price'] * 100,
                    'product_data': {
                        'name': angebot["title"],
                        'images': ['https://salina.maris.ch/static/{}'.format(angebot["image"])],
                        'description': angebot["subtitle"],
                        'metadata': {'prod_id': angebot['id']}
                    },
                },
                'quantity': 1

            }],
            mode='payment',
            locale='de',
            success_url=url_for('payment.thanks', _external=True) +
            '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment.products', _external=True),
        )
        return {
            'checkout_session_id': session['id'],
            'checkout_public_key': current_app.config['STRIPE_PUBLIC_KEY']
        }
    except Exception as e:
        return {'error': str(e)}, 403


@payment.route('/stripe_webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    print('WEBHOOK CALLED')

    # check content size for huge payload
    if request.content_length > 1024 * 1024:
        print('REQUEST TOO BIG')
        abort(400)

    payload = request.get_data()
    sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = 'whsec_bLSOubNYeVgALEbP8GHmuU9zmVefKAdr'
    event = None

    # security, make sure the request is valid and from stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print('INVALID PAYLOAD')
        return {}, 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print('INVALID SIGNATURE')
        return {}, 400

    # if it is a completed session, handle order fulfillment
    if event['type'] == 'checkout.session.completed':
        gutscheine = read_gutscheine()
        session = event['data']['object']

        # get necessary data for confirmation
        email_data = parse_checkout_session(session, gutscheine)

        # send confirmation mails
        sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
        try:
            # internal confirmation
            send_mail(sg, current_app.config['INTERNAL_MAIL'],
                      email_data, 'd-95cb04609d3e44beb088e5ec1c1bf093')
            # customer confirmation
            send_mail(sg, session['customer_details']['email'],
                      email_data, 'd-1a92894c9c42498cbd374782cfb87947')
        except Exception as e:
            print(str(e))
            return {}, 400

    return {}, 200


def read_gutscheine():
    filename = current_app.root_path + \
        '/blueprints/payment/templates/payment/gutscheine.json'
    with open(filename) as f:
        angebote = json.load(f)

    return [a for a in angebote if a['active']]


def send_mail(client, to, data, template):
    mail = Mail(from_email=current_app.config['SENDER_MAIL'], to_emails=to)
    mail.dynamic_template_data = data
    mail.template_id = template
    response = client.send(mail)
    return response


def parse_checkout_session(session, all_products):
    # get/create necessary data
    parsed_data = {}
    currency = session['currency'].upper()

    # retrieve purchased line items
    line_items = stripe.checkout.Session.list_line_items(
        session['id'], limit=1)

    # retrieve payment intent with customer and payment data
    payment_intent = stripe.PaymentIntent.retrieve(
        session['payment_intent'])

    # get payment data
    try:
        if len(payment_intent['charges']['data']) > 1:
            raise Exception
        card = payment_intent['charges']['data'][0]['payment_method_details']['card']
        parsed_data['payment_info'] = {
            'payment_type': card['brand'],
            'payment_description': "**** **** **** {}".format(card['last4'])
        }
    except:
        parsed_data['payment_info']['payment_description'] = "Credit Card"

    # get paid amount data
    parsed_data['payment_info']['total'] = '{} {:.2f}'.format(
        currency, session['amount_total'] / 100)
    parsed_data['payment_info']['taxes'] = '{} {:.2f}'.format(currency, (session['amount_total'] / 100) -
                                                              (session['amount_total'] / 107.7))
    parsed_data['payment_info']['stripe_reference'] = session['payment_intent']

    # get relevant product info
    parsed_data['items'] = []
    for item in line_items['data']:
        try:
            product = stripe.Product.retrieve(item['price']['product'])
            item_dict = {
                'price': '{} {:.2f}'.format(item['currency'].upper(), item['amount_total'] / 100),
                'quantity': item['quantity'],
                'name': item['description'],
                'services': next((g for g in all_products if g['id'] == product['metadata']['prod_id']))['details']['services']
            }
        except:
            item_dict = {'name': item['description']}
        parsed_data['items'].append(item_dict)

    # get customer data
    try:
        parsed_data['customer'] = stripe.util.convert_to_dict(
            payment_intent['charges']['data'][0]['billing_details'])
    except:
        parsed_data['customer'] = stripe.util.convert_to_dict(
            session['customer_details'])
    return parsed_data
