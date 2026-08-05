
async function loadTaskandBidCount() {
    const bidCont = document.querySelector(".task-bid-won");
    const jobCont = document.querySelector(".job-applied-for");
    const reviewCont = document.querySelector(".reviews-count");

    if (!bidCont || !jobCont) {
        console.warn("Task/Bid count elements not found.");
        return;
    }

    console.log("Before fetch - textContent:", bidCont.textContent, jobCont.textContent);

    try {
        const res = await fetchProtected("/api/taskandbidcount/");
        if (!res.ok) throw new Error('Failed to fetch');

        const data = await res.json();
        console.log("Fetched data:", data);

        bidCont.textContent = data.bid_won || 0;
        jobCont.textContent = data.job_app || 0;
        if (reviewCont) reviewCont.textContent = data.reviews || 0;
        console.log("After update - textContent:", bidCont.textContent, jobCont.textContent);

        // Double-check after delay
        $(".task-bid-won, .job-applied-for").rCounter({
			duration: 20
		});

    } catch (err) {
        console.error("Error loading:", err);
    }
}

document.addEventListener('DOMContentLoaded', loadTaskandBidCount);




async function loadUserOrders() {
	const ordersContainer = document.querySelector('#orders-list .dashboard-box-list');
	if (!ordersContainer) return;

	try {
		const response = await fetchProtected('/api/pricing/orders/me/', {
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) throw new Error('Failed to fetch orders');

		const orders = await response.json();

		console.log('Orders:', orders);

		ordersContainer.innerHTML = ''; // Clear previous content

		orders.slice(0, 5).forEach(order => {
			const planName = order.plan_data?.name || 'Unknown Plan';
			const orderId = order.id;
			const createdDate = new Date(order.created_at).toLocaleDateString('en-GB'); // DD/MM/YYYY format
			const status = order.status.toLowerCase();

			let statusClass = 'unpaid';
			let buttonLabel = 'Finish Payment';
			let buttonColor = 'button';
			let buttonHref = `/checkout/${orderId}`;

			if (status === 'paid') {
				statusClass = 'paid';
				buttonLabel = 'View Invoice';
				buttonColor = 'button gray';
				buttonHref = `/invoice/${orderId}" target="_blank`;
			} else if (status === 'cancelled' || status === 'failed') {
				statusClass = 'unpaid';
				buttonLabel = 'Restart Payment';
				buttonColor = 'button warning';
				buttonHref = `/checkout/${orderId}`;
			}

			const li = document.createElement('li');
			li.innerHTML = `
				<div class="invoice-list-item">
					<strong>${planName}</strong>
					<ul>
						<li><span class="${statusClass}">${status.charAt(0).toUpperCase() + status.slice(1)}</span></li>
						<li>Order: #${orderId}</li>
						<li>Date: ${createdDate}</li>
					</ul>
				</div>
				<div class="buttons-to-right">
					<a href="${buttonHref}" class="${buttonColor}">${buttonLabel}</a>
				</div>
			`;

			ordersContainer.appendChild(li);
		});
	} catch (err) {
		console.error('Error loading orders:', err);
	}
}

loadUserOrders();

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', async function() {
	try {
		await updateUserNavInfo();
	} catch (error) {
		console.error('Error loading user orders:', error);
	}

	let firstName = userInfo.first_name.trim();
	console.log("User's first name:", firstName);
	document.getElementById('dashboard-greet').textContent = `Howdy${userInfo.firstName !== ' ' ? (', ' + firstName) : ''}!`;

	// "Complete Your Profile" popup removed per request — it recurred every 40s.
	// (confirmUserProfileCompletion / showOverAllPopup are left defined for the
	// pricing / login popups that reuse them.)

});
