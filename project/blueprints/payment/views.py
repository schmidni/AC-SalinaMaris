from flask import Blueprint, render_template, url_for, current_app, request, abort

import stripe
import json

payment = Blueprint('payment', __name__,
                    template_folder='templates', url_prefix='/payment')


@payment.record
def record_config(setup_state):
    stripe.api_key = setup_state.app.config['STRIPE_SECRET_KEY']


@payment.route('/products')
def products():
    angebote = read_gutscheine()
    return render_template('payment/products.html', angebote=angebote)


@payment.route('/thanks')
def thanks():
    return render_template('payment/thanks.html')


@payment.route('/stripe_pay')
def stripe_pay():
    id = request.args.get('id', None)

    if id:
        angebot = read_gutscheine()[int(id)]
    else:
        abort(404)

    session = stripe.checkout.Session.create(
        billing_address_collection='required',
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'chf',
                'unit_amount': angebot['price']*100,
                'product_data': {
                    'name': angebot["title"],
                    'images': ['https://salina.maris.ch/static/{}'.format(angebot["image"])],
                    'description': angebot["subtitle"],
                },
            },
            'quantity': 1,
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


def read_gutscheine():
    filename = current_app.root_path + \
        '/blueprints/payment/templates/payment/gutscheine.json'
    with open(filename) as f:
        angebote = json.load(f)

    return [a for a in angebote if a['active']]
