function renderTimeline(status) {
    const steps = [
        { key: "INITIATED", label: "Payment Initiated" },
        { key: "PROCESSING", label: "Payment Processing" },
        { key: "ESCROWED", label: "Funds Secured (Escrow)" },
        { key: "RELEASED", label: "Payment Completed" }
    ];

    let html = "";

    steps.forEach(step => {
        const active = isStepActive(status, step.key);

        html += `
            <li class="${active ? 'active' : ''}">
                <strong>${step.label}</strong>
                <br>
                <small>${active ? 'Completed' : 'Pending'}</small>
            </li>
        `;
    });

    $("#payment-timeline").html(html);
}

function isStepActive(currentStatus, step) {
    const order = [
        "NOT_INITIATED",
        "INITIATED",
        "PROCESSING",
        "ESCROWED",
        "RELEASED"
    ];

    return order.indexOf(currentStatus) >= order.indexOf(step);
}

function setStatusBadge(status) {
    const config = getStatusConfig(status);

    $("#payment-status-badge")
        .removeClass()
        .addClass(`dashboard-status-button ${config.color}`)
        .text(config.label);
}

function renderBreakdown(amount) {
    const fee = Math.round(amount * 0.05); // 5% example
    const total = amount + fee;

    $("#breakdown-amount").text(formatAmount(amount));
    $("#platform-fee").text(formatAmount(fee));
    $("#total-amount").text(formatAmount(total));
}

function renderActions(payment) {
    const status = payment.payment_status;
    let html = "";

    if (status === "NOT_INITIATED" || status === "FAILED") {
        html = `
            <button class="button ripple-effect pay-btn" data-url="${payment.payment_url}">
                Pay Now
            </button>
        `;
    } 
    else if (status === "INITIATED") {
        html = `
            <button class="button ripple-effect pay-btn" data-url="${payment.payment_url}">
                Continue Payment
            </button>
        `;
    }
    else if (status === "PROCESSING") {
        html = `<button class="button gray" disabled>Processing...</button>`;
    }
    else if (status === "ESCROWED") {
        html = `<p>Funds are securely held in escrow until job completion.</p>`;
    }
    else if (status === "RELEASED") {
        html = `<p>Payment has been successfully completed.</p>`;
    }

    $("#action-container").html(html);
}

$(document).ready(function () {
    const paymentId = getPaymentIdFromURL();
    loadPaymentDetail(paymentId);
});

function loadPaymentDetail(id) {
    $.ajax({
        url: `/api/employer/payments/${id}/`,
        method: "GET",
        success: function (data) {
            populatePaymentDetail(data);
        },
        error: function () {
            showNotification("Failed to load payment details", "error");
        }
    });
}

function populatePaymentDetail(payment) {
    $("#job-title").text(payment.job_title);
    $("#freelancer-name").text(payment.freelancer_name);
    $("#payment-amount").text(formatAmount(payment.amount));

    setStatusBadge(payment.payment_status);
    renderTimeline(payment.payment_status);
    renderBreakdown(payment.amount);
    renderActions(payment);
}

$(document).on("click", ".pay-btn", function () {
    const paymentId = getPaymentIdFromURL();
    const button = $(this);

    button.prop("disabled", true).text("Processing...");

    $.ajax({
        url: `api/payments/employer/${paymentId}/initiate/`,
        method: "POST",
        success: function (res) {
            window.location.href = res.payment_url;
        },
        error: function () {
            showNotification("Failed to initiate payment", "error");
            button.prop("disabled", false).text("Pay Now");
        }
    });
});

function getPaymentIdFromURL() {
    const path = window.location.pathname;
    return path.split("/").filter(Boolean).pop();
}