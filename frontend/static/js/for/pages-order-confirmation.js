const MAX_AUTO_RETRIES = 3;      // extra attempts after the first
const AUTO_RETRY_DELAY_MS = 2500; // wait between attempts

async function ComfirmPayment(attempt = 0) {
    // Get query parameters from current page URL
    const params = new URLSearchParams(window.location.search);
    const reference = params.get("reference") || params.get("trxref");

    if (!reference) {
        console.log("Reference not found.");
        window.location.href = "/dashboard/";
        return;
    }

    try {
        console.log("sending confirmation request", reference, "attempt", attempt);
        const response = await fetchProtected("/api/pricing/payment/confirmation/", {
            method: "POST",
            body: JSON.stringify({ reference })
        });

        // Parse the body once (safely) regardless of status.
        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            console.log("Payment confirmed:", data);

            const invoice = document.getElementById("invoice-link");
            if (invoice) {
                invoice.addEventListener("click", function (event) {
                    event.preventDefault();
                    window.open(`/invoice/${data.order_id}/`, "_blank");
                });
            }
            const confirmContainer = document.querySelector(".order-confirmation-page");
            if (confirmContainer) confirmContainer.style.display = "block";
            hideLoading();
            return;
        }

        // Not OK. If the payment is merely still pending, it may complete a
        // moment later, so auto-retry a few times (keeping the loader up)
        // before surfacing a manual Retry. Never reload / loop forever.
        if (data && data.status === "pending" && attempt < MAX_AUTO_RETRIES) {
            console.log(`Payment still pending, retry ${attempt + 1}/${MAX_AUTO_RETRIES} in ${AUTO_RETRY_DELAY_MS}ms`);
            setTimeout(() => ComfirmPayment(attempt + 1), AUTO_RETRY_DELAY_MS);
            return;
        }

        console.log("Payment couldn't be confirmed.", data);
        hideLoading();
        showConfirmationStatus(data);
    } catch (error) {
        console.error("Error confirming payment:", error);
        // Transient network error: retry a few times before giving up.
        if (attempt < MAX_AUTO_RETRIES) {
            setTimeout(() => ComfirmPayment(attempt + 1), AUTO_RETRY_DELAY_MS);
            return;
        }
        hideLoading();
        showConfirmationStatus({ error: "Network error while confirming your payment." });
    }
}

// Render a non-looping status message with Retry / Dashboard actions.
function showConfirmationStatus(data) {
    const pending = data && data.status === "pending";
    const title = pending ? "Payment processing" : "Payment not confirmed";
    const message = pending
        ? "Your payment is still being processed. If you have completed payment, wait a few seconds and click Retry."
        : (data && data.error ? data.error : "We couldn't confirm your payment. If you were charged, please contact support.");

    let box = document.getElementById("payment-status-box");
    if (!box) {
        box = document.createElement("div");
        box.id = "payment-status-box";
        box.style.cssText =
            "max-width:640px;margin:80px auto;padding:32px;border:1px solid #e5e5e5;" +
            "border-radius:12px;text-align:center;font-family:sans-serif;background:#fff;";
        document.body.prepend(box);
    }
    box.innerHTML =
        `<h3 style="margin:0 0 12px;">${title}</h3>` +
        `<p style="color:#555;margin:0 0 24px;">${message}</p>` +
        `<button id="retry-confirm" class="button ripple-effect" style="margin-right:8px;">Retry</button>` +
        `<a href="/dashboard/" class="button ripple-effect" style="background:#9aa0a6;">Go to Dashboard</a>`;

    const retry = document.getElementById("retry-confirm");
    if (retry) {
        retry.addEventListener("click", function () {
            box.remove();
            ComfirmPayment(); // restart from attempt 0 (another round of auto-retries)
        });
    }
}

// Load the function when the page is ready
document.addEventListener("DOMContentLoaded", ComfirmPayment);
