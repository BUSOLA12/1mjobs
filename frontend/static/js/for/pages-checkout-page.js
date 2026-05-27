async function fetchOrder() {
  const pathSegments = window.location.pathname.split('/').filter(Boolean);
  const lastSegment = pathSegments[pathSegments.length - 1];

  if (!isNaN(lastSegment)) {
    const orderId = parseInt(lastSegment);

    try {
      const response = await fetchProtected(`/api/pricing/orders/${orderId}/`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch order: ${response.status}`);
      }

      const currentOrder = await response.json();
      console.log('Order fetched:', currentOrder);

      // You can now use `currentOrder` elsewhere in your code
      updateBillingSummary(currentOrder);

      submitBillingCycleUpdate(currentOrder)

    } catch (error) {
      console.error('Error retrieving order:', error);
    }
  } else {
    console.error('Invalid order ID in URL:', lastSegment);
  }
};


function updateBillingSummary(order) {
  const monthlyRadio = document.getElementById("radio-5");
  const yearlyRadio = document.getElementById("radio-6");

  // Plan details from order
  const planName = order.plan_data.name;
  const monthlyPrice = parseFloat(order.plan_data.monthly_price);
  const yearlyPrice = parseFloat(order.plan_data.yearly_price);
  const billingCycle = order.billing_cycle; // "monthly" or "yearly"

  // Select summary elements
  const summaryItems = document.querySelectorAll('.boxed-widget-inner ul li');
  const planLabel = summaryItems[0].querySelector('span');
  const vatLabel = summaryItems[1].querySelector('span');
  const finalPriceLabel = summaryItems[2].querySelector('span');

  // Set billing radio
  if (billingCycle === "monthly") {
    monthlyRadio.checked = true;
  } else if (billingCycle === "yearly") {
    yearlyRadio.checked = true;
  }

  // Function to update summary based on selection
  function setSummaryPrices(cycle) {
    let basePrice = cycle === "monthly" ? monthlyPrice : yearlyPrice;
    let vat = +(basePrice * 0.20).toFixed(2);
    let finalPrice = +(basePrice + vat).toFixed(2);

    // Update pricing labels in radios
    document.querySelector('.regular-price-tag').textContent = `₦${monthlyPrice.toLocaleString('en-NG')} / month`;
    document.querySelector('.discounted-price-tag').textContent = `₦${yearlyPrice.toLocaleString('en-NG')} / year`;
    document.querySelector('.line-through').textContent = `₦${(yearlyPrice / 0.9).toLocaleString('en-NG')} / year`; // Assuming 10% discount

    // Update summary section
    summaryItems[0].innerHTML = `${planName} Plan <span>₦${basePrice.toLocaleString('en-NG')}</span>`;
    vatLabel.textContent = `₦${vat.toLocaleString('en-NG')}`;
    finalPriceLabel.textContent = `₦${finalPrice.toLocaleString('en-NG')}`;
  }

  // Initial summary load
  setSummaryPrices(billingCycle);

  // Event listeners
  monthlyRadio.addEventListener('change', () => {
    if (monthlyRadio.checked) {
      setSummaryPrices("monthly");
    }
  });

  yearlyRadio.addEventListener('change', () => {
    if (yearlyRadio.checked) {
      setSummaryPrices("yearly");
    }
  });
}


// Function 1: Updates order with selected billing cycle and proceeds to payment
function submitBillingCycleUpdate(order) {
  const confirmBtn = document.getElementById("confirm-plan-btn");
  confirmBtn.addEventListener("click", function () {
    // Determine selected billing type
    const selectedCycle = document.querySelector('input[name="radio-payment-type"]:checked');
    let billingCycle = "monthly"; // default
    let amount = order.plan_data.monthly_price;

    if (selectedCycle && selectedCycle.id === "radio-6") {
      billingCycle = "yearly";
      amount = order.plan_data.yearly_price;
    }

    alert(`Selected Cycle: ${billingCycle}, Amount: $${amount}`);
    // Send POST request to update billing cycle
    fetchProtected(`/api/pricing/orders/${order.id}/`, {
      method: "PATCH",
      body: JSON.stringify({
        billing_cycle: billingCycle,
        amount: amount
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error("Failed to update order billing cycle");
      }
      return response.json();
    })
    .then(data => {
      console.log("Order updated:", data);
      // Proceed to checkout
      redirectToPayment(order.id);
    })
    .catch(error => {
      console.error("Error updating order:", error);
    });
  });
}

// Function 2: Redirects to payment link
function redirectToPayment(orderId) {
  fetchProtected(`/api/pricing/checkout/${orderId}/`)
    .then(response => {
      if (!response.ok) {
        throw new Error("Failed to initiate checkout");
      }
      return response.json();
    })
    .then(data => {
      if (data.payment_url) {
        window.location.href = data.payment_url;  // Redirect to Paystack
      } else {
        console.error("Payment URL not found in response");
      }
    })
    .catch(error => {
      console.error("Error redirecting to payment:", error);
    });
}


fetchOrder();