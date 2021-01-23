const button = document.getElementsByClassName('sa-buy');

for (let i = 0; i<button.length; i++){
    let product_id = button[i].dataset.id;

    button[i].addEventListener('click', event => {
        fetch('/payment/stripe_pay?id=' + product_id)
        .then((result) => { return result.json(); })
        .then((data) => {
            var stripe = Stripe(data.checkout_public_key);
            stripe.redirectToCheckout({
                sessionId: data.checkout_session_id
            }).then(function (result) {
                // If redirectToCheckout fails due to a browser or network
                // error, you should display the localized error message to your
                // customer using error.message.
                if (result.error) {
                  alert(result.error.message);
                }
              })
              .catch(function (error) {
                console.error("Error:", error);
              });
        })
    });


}