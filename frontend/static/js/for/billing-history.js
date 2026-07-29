$(document).ready(function () {
    loadActiveSubscription();
    loadBillingHistory();
});

function loadActiveSubscription() {
    fetchProtected("/api/pricing/subscription/active/")
        .then(res => (res.ok ? res.json() : null))
        .then(renderSubscription)
        .catch(() => renderSubscription(null));
}

function renderSubscription(sub) {
    const box = document.getElementById("current-subscription");
    if (!sub || !sub.plan) {
        box.innerHTML = `
            <div class="plan-card">
                <span class="plan-card__crest"><i class="icon-material-outline-loyalty"></i></span>
                <div class="plan-card__body">
                    <div class="plan-card__name">No active plan</div>
                    <div class="plan-card__meta">You're on the Free plan. Upgrade to unlock Pro perks.</div>
                </div>
                <div class="plan-card__cta">
                    <a href="/pricing-plans/" class="wallet-btn wallet-btn--brand">View plans</a>
                </div>
            </div>`;
        return;
    }
    const active = sub.is_active && !sub.has_expired;
    const pill = active
        ? '<span class="wallet-pill wallet-pill--ok">Active</span>'
        : '<span class="wallet-pill wallet-pill--fail">Expired</span>';
    const endLabel = active ? "Renews / Expires" : "Expired";
    box.innerHTML = `
        <div class="plan-card">
            <span class="plan-card__crest"><i class="icon-material-outline-loyalty"></i></span>
            <div class="plan-card__body">
                <div class="plan-card__name">${sub.plan.name} ${pill}</div>
                <div class="plan-card__meta">
                    <span><b>${capitalize(sub.billing_cycle)}</b> billing</span>
                    <span>Started <b>${formatDate(sub.start_date)}</b></span>
                    <span>${endLabel} <b>${formatDate(sub.end_date)}</b></span>
                </div>
            </div>
            <div class="plan-card__cta">
                <a href="/pricing-plans/" class="wallet-btn wallet-btn--line">${active ? "Change plan" : "Renew"}</a>
            </div>
        </div>`;
}

function loadBillingHistory() {
    fetchProtected("/api/pricing/orders/me/")
        .then(res => (res.ok ? res.json() : []))
        .then(renderHistory)
        .catch(() => renderHistory([]));
}

function renderHistory(orders) {
    const tbody = document.getElementById("billing-history-body");
    const empty = document.getElementById("billing-empty");
    const count = document.getElementById("billing-count");
    tbody.innerHTML = "";

    if (!orders || !orders.length) {
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";
    count.textContent = orders.length + (orders.length === 1 ? " entry" : " entries");
    count.hidden = false;

    orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    orders.forEach(o => {
        const planName = (o.plan_data && o.plan_data.name) || o.plan_name_snapshot || "Plan";
        const badge = statusBadge(o.status);
        const invoice = (o.status === "paid")
            ? `<a href="/invoice/${o.id}/" target="_blank" class="wallet-btn wallet-btn--line wallet-btn--sm">Invoice</a>`
            : '<span style="color:#aab2c5;">—</span>';
        tbody.insertAdjacentHTML("beforeend", `
            <tr>
                <td>${formatDate(o.created_at)}</td>
                <td>${planName}</td>
                <td>${capitalize(o.billing_cycle)}</td>
                <td class="amt">₦${formatAmount(o.amount)}</td>
                <td><span class="wallet-pill wallet-pill--${badge.cls}">${badge.label}</span></td>
                <td>${invoice}</td>
            </tr>`);
    });
}

function statusBadge(status) {
    switch (status) {
        case "paid": return { label: "Paid", cls: "ok" };
        case "pending": return { label: "Pending", cls: "pending" };
        case "failed": return { label: "Failed", cls: "fail" };
        case "cancelled": return { label: "Cancelled", cls: "neutral" };
        default: return { label: status || "Unknown", cls: "neutral" };
    }
}

function formatAmount(a) { return new Intl.NumberFormat("en-NG").format(Number(a) || 0); }
function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }
function formatDate(d) {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("en-NG", { year: "numeric", month: "short", day: "numeric" });
}
