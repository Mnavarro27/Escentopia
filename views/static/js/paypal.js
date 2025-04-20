async function iniciarPagoPaypal(monto) {
    try {
        const response = await fetch('http://localhost:5000/api/paypal/create-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ monto })
        });

        const data = await response.json();
        if (response.ok && data.redirectUrl) {
            alert('El monto total es $' + monto);
            console.log("Enviando a PayPal:", monto);

            // Redirecciona al usuario a la URL de aprobación de PayPal
            window.location.href = data.redirectUrl;
        } else {
            alert('Error al iniciar el pago con PayPal');
        }
    } catch (error) {
        console.error('Error en la integración de PayPal:', error);
        alert('Error al procesar el pago');
    }
}
