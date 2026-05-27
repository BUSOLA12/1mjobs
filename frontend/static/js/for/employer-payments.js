function createPaymentCard(payment) {
    const statusConfig = getStatusConfig(payment.payment_status);

    return `
    <div class="col-xl-4 col-md-6 margin-bottom-30">
        <div class="dashboard-box">

            <div class="headline">
                <h3>${payment.job_title}</h3>
            </div>

            <div class="content padding-20">

                <p><strong>Freelancer:</strong> ${payment.freelancer_name}</p>
                <p><strong>Amount:</strong> ₦${formatAmount(payment.amount)}</p>

                <div class="margin-top-10 margin-bottom-15">
                    <span class="dashboard-status-button ${statusConfig.color}">
                        ${statusConfig.label}
                    </span>
                </div>

                <div>
                    ${renderActionButton(payment, statusConfig)}
                </div>

            </div>

        </div>
    </div>
    `;
}

function getStatusConfig(status) {
    switch(status) {
        case "NOT_INITIATED":
            return { label: "Not Paid", color: "gray", action: "pay" };
        case "INITIATED":
            return { label: "Continue Payment", color: "blue", action: "continue" };
        case "PROCESSING":
            return { label: "Processing", color: "yellow", action: "none" };
        case "ESCROWED":
            return { label: "In Escrow", color: "purple", action: "view" };
        case "RELEASED":
            return { label: "Completed", color: "green", action: "none" };
        case "FAILED":
            return { label: "Failed", color: "red", action: "retry" };
        default:
            return { label: "Unknown", color: "gray", action: "none" };
    }
}

function renderActionButton(payment, statusConfig) {
    switch(statusConfig.action) {
        case "pay":
            return `<button class="button ripple-effect pay-btn" data-url="${payment.payment_url}">
                        Pay Now
                    </button>`;
        case "continue":
            return `<button class="button ripple-effect pay-btn" data-url="${payment.payment_url}">
                        Continue Payment
                    </button>`;
        case "retry":
            return `<button class="button dark ripple-effect pay-btn" data-url="${payment.payment_url}">
                        Retry Payment
                    </button>`;
        case "view":
            return `<a href="/employer/payments/${payment.id}/" class="button gray">
                        View Details
                    </a>`;
        default:
            return `<button class="button gray" disabled>No Action</button>`;
    }
}

function renderPayments(payments) {
    const container = $("#payments-card-container");
    container.empty();

    if (!payments.length) {
        $("#empty-state").show();
        return;
    }

    $("#empty-state").hide();

    payments.forEach(payment => {
        container.append(createPaymentCard(payment));
    });
}

$(document).on("click", ".pay-btn", function () {
    const button = $(this);
    const url = button.data("url");

    if (!url) {
        showNotification("Payment link unavailable", "error");
        return;
    }

    button.prop("disabled", true).text("Redirecting...");

    window.location.href = url;
});

function showNotification(message, type="success") {
    const html = `
        <div class="notification ${type} closeable">
            <p>${message}</p>
            <a class="close"></a>
        </div>
    `;
    $("#payment-notification-area").html(html);
}

function formatAmount(amount) {
    return new Intl.NumberFormat().format(amount);
}


$(document).ready(function () {
    loadPayments();
});

function loadPayments() {
    $.ajax({
        url: "/api/payments/employer/",
        method: "GET",
        success: function (data) {
            renderPayments(data);
        },
        error: function () {
            showNotification("Failed to load payments", "error");
        }
    });
}

