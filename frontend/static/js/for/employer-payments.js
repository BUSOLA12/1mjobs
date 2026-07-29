/* Employer Payments console: escrow pipeline + payment ledger.
   Data: GET /api/payments/employer/ -> [{id, job_title, freelancer_name,
   amount, status, payment_status, payment_url}, ...] */

let ALL_PAYMENTS = [];
let CURRENT_FILTER = "all";

// Which pipeline bucket a payment status belongs to.
function bucketOf(status) {
	switch (status) {
		case "ESCROWED": return "escrow";
		case "RELEASED": return "done";
		default: return "await"; // NOT_INITIATED, INITIATED, PROCESSING, FAILED
	}
}

function statusConfig(status) {
	switch (status) {
		case "NOT_INITIATED": return { label: "Not paid", pill: "neutral", action: "pay" };
		case "INITIATED": return { label: "Awaiting payment", pill: "info", action: "continue" };
		case "PROCESSING": return { label: "Processing", pill: "pending", action: "none" };
		case "ESCROWED": return { label: "In escrow", pill: "info", action: "release" };
		case "RELEASED": return { label: "Completed", pill: "ok", action: "none" };
		case "FAILED": return { label: "Failed", pill: "fail", action: "retry" };
		default: return { label: status || "Unknown", pill: "neutral", action: "none" };
	}
}

function actionButton(payment, cfg) {
	switch (cfg.action) {
		case "pay":
			return `<button class="wallet-btn wallet-btn--brand wallet-btn--sm pay-btn" data-url="${payment.payment_url || ""}"><i class="icon-feather-arrow-up-right"></i> Pay now</button>`;
		case "continue":
			return `<button class="wallet-btn wallet-btn--brand wallet-btn--sm pay-btn" data-url="${payment.payment_url || ""}">Continue</button>`;
		case "retry":
			return `<button class="wallet-btn wallet-btn--line wallet-btn--sm pay-btn" data-url="${payment.payment_url || ""}">Retry</button>`;
		case "release":
			return `<button class="wallet-btn wallet-btn--release wallet-btn--sm release-btn" data-id="${payment.id}"><i class="icon-feather-check"></i> Release</button>`;
		default:
			return "";
	}
}

function initials(name) {
	if (!name || !name.trim()) return "?";
	const parts = name.trim().split(/\s+/);
	return (parts[0][0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
}

function paymentRow(payment) {
	const cfg = statusConfig(payment.payment_status);
	const freelancer = payment.freelancer_name || "Freelancer";
	const action = actionButton(payment, cfg);
	return `
		<div class="pay-item" data-bucket="${bucketOf(payment.payment_status)}">
			<span class="wallet-avatar">${initials(freelancer)}</span>
			<span>
				<div class="pay-item__title">${payment.job_title || "Untitled job"}</div>
				<div class="pay-item__sub">
					<span class="wallet-pill wallet-pill--${cfg.pill}">${cfg.label}</span>
					<span>${freelancer}</span>
				</div>
			</span>
			<span class="pay-item__right">
				<span class="pay-item__amt num">₦${formatAmount(payment.amount)}</span>
				<span class="pay-item__action">${action}</span>
			</span>
		</div>`;
}

function renderSummary(payments) {
	const sums = { await: 0, escrow: 0, done: 0 };
	const counts = { all: payments.length, await: 0, escrow: 0, done: 0 };
	payments.forEach(p => {
		const b = bucketOf(p.payment_status);
		sums[b] += Number(p.amount) || 0;
		counts[b] += 1;
	});

	document.getElementById("await-amount").textContent = formatAmount(sums.await);
	document.getElementById("escrow-amount").textContent = formatAmount(sums.escrow);
	document.getElementById("done-amount").textContent = formatAmount(sums.done);

	const jobs = n => n + (n === 1 ? " job" : " jobs");
	document.getElementById("await-count").textContent = jobs(counts.await);
	document.getElementById("escrow-count").textContent = jobs(counts.escrow);
	document.getElementById("done-count").textContent = jobs(counts.done);

	document.querySelectorAll("#payment-filters .cnt").forEach(el => {
		el.textContent = counts[el.dataset.count] ?? 0;
	});

	const total = document.getElementById("pay-count");
	total.textContent = counts.all + (counts.all === 1 ? " payment" : " payments");
	total.hidden = counts.all === 0;
}

function renderList() {
	const container = document.getElementById("payments-card-container");
	const empty = document.getElementById("empty-state");
	const rows = CURRENT_FILTER === "all"
		? ALL_PAYMENTS
		: ALL_PAYMENTS.filter(p => bucketOf(p.payment_status) === CURRENT_FILTER);

	if (!ALL_PAYMENTS.length) {
		container.innerHTML = "";
		empty.style.display = "block";
		return;
	}
	empty.style.display = "none";

	if (!rows.length) {
		container.innerHTML =
			'<div class="wallet-empty" style="padding:40px 24px;">' +
				'<div class="wallet-empty__icon"><i class="icon-material-outline-check"></i></div>' +
				'<h5>Nothing here</h5><p>No payments in this state right now.</p></div>';
		return;
	}
	container.innerHTML = rows.map(paymentRow).join("");
}

function renderPayments(payments) {
	ALL_PAYMENTS = Array.isArray(payments) ? payments : [];
	renderSummary(ALL_PAYMENTS);
	renderList();
}

/* ---- Interactions --------------------------------------------------------- */
$(document).on("click", "#payment-filters .wallet-tab", function () {
	$("#payment-filters .wallet-tab").removeClass("is-active");
	$(this).addClass("is-active");
	CURRENT_FILTER = $(this).data("filter");
	renderList();
});

$(document).on("click", ".pay-btn", function () {
	const button = $(this);
	const url = button.data("url");
	if (!url) { showNotification("Payment link unavailable", "error"); return; }
	button.prop("disabled", true).text("Redirecting...");
	window.location.href = url;
});

// Release escrowed funds to the freelancer (platform keeps the 10% commission).
$(document).on("click", ".release-btn", async function () {
	const button = $(this);
	const id = button.data("id");
	if (!confirm("Release the funds to the freelancer? The platform keeps a 10% commission and the rest becomes the freelancer's available balance.")) {
		return;
	}
	button.prop("disabled", true).html("Releasing...");
	try {
		const res = await fetchProtected(`/api/payments/employer/${id}/release/`, { method: "POST" });
		const data = await res.json();
		if (res.ok) {
			showNotification(`Released. Commission ₦${formatAmount(data.commission)} kept, ₦${formatAmount(data.net)} paid to the freelancer.`, "success");
			loadPayments();
		} else {
			showNotification(data.error || "Could not release funds.", "error");
			button.prop("disabled", false).html('<i class="icon-feather-check"></i> Release');
		}
	} catch (err) {
		console.error("Release error:", err);
		showNotification("Something went wrong releasing funds.", "error");
		button.prop("disabled", false).html('<i class="icon-feather-check"></i> Release');
	}
});

function showNotification(message, type = "success") {
	const t = document.getElementById("wallet-toast");
	if (!t) return;
	t.textContent = message;
	t.className = "wallet-toast show " + (type === "error" ? "wallet-toast--err" : "wallet-toast--ok");
	clearTimeout(t._timer);
	t._timer = setTimeout(() => t.classList.remove("show"), 4000);
}

function formatAmount(amount) {
	return new Intl.NumberFormat("en-NG").format(Number(amount) || 0);
}

function loadPayments() {
	$.ajax({
		url: "/api/payments/employer/",
		method: "GET",
		success: renderPayments,
		error: function () { showNotification("Failed to load payments", "error"); }
	});
}

$(document).ready(loadPayments);
