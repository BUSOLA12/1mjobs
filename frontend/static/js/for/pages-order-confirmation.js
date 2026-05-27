async function ComfirmPayment(){
    alert("Confirming payment...");
    // Get query parameters from current page URL
    const params = new URLSearchParams(window.location.search);
    const reference = params.get("reference") || params.get("trxref");

    if (!reference) {
        console.log("Reference not found.");
        window.location.href = "/dashboard/";
        hideLoading();
        return;
    }

    try {
        console.log("sending confirmation request", reference)
        const response = await fetchProtected("/api/pricing/payment/confirmation/", {
            method: "POST",
            body: JSON.stringify({ reference })
        });

        if (response.ok) {
            const data = await response.json();
            console.log("Payment confirmed:", data);
            
            // add eventlistener to the invoice link
            document.getElementById("invoice-link").addEventListener("click", function(event) {
                event.preventDefault(); // Prevent default link behavior
                // open on a new tab
                window.open(`/invoice/${data.order_id}/`, '_blank');
            });
            const confirmContainer = document.querySelector('.order-confirmation-page')
            if (confirmContainer) confirmContainer.style.display = "block";
            hideLoading();
        } else {
            const err = response.json();
            console.log("Payment couldn't be confirmed.", err);
            window.location.reload();
        }
    } catch (error) {
        console.error("Error confirming payment:", error);
    }
};


// Load the function when the page is ready
document.addEventListener("DOMContentLoaded", ComfirmPayment); 