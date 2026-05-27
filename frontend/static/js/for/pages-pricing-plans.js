async function loadPricingPlans(planType = null) {
  try {
    const response = await fetch(`/api/pricing/plans/${planType? ("?user_type=" + planType) : ""}`);
    const plans = await response.json();

    console.log("Plans gotten back: ",plans)

    // Prefer a role-specific container if it exists in the DOM; otherwise fall
    // back to the generic .pricing-plans-container that the active template uses.
    let containerSelector = ".pricing-plans-container";
    if (planType && document.querySelector(`#${planType}`)) {
      containerSelector = `#${planType}`;
    }
    const selector = `${containerSelector} .pricing-plan`;

    const emptyStateEl = document.getElementById("membership-plans-empty-state");
    const containerEl = document.querySelector(containerSelector);
    if (!Array.isArray(plans) || plans.length === 0) {
      if (containerEl) containerEl.style.display = "none";
      if (emptyStateEl) emptyStateEl.style.display = "block";
      return plans;
    }
    if (emptyStateEl) emptyStateEl.style.display = "none";
    if (containerEl) containerEl.style.display = "";

    const planElements = document.querySelectorAll(selector);

    plans.forEach((plan, index) => {
      const planElement = planElements[index];

      // Option 1: Set data-plan-id on the whole pricing plan element
      planElement.dataset.planId = plan.id;
      planElement.dataset.userType = plan.user_type;

      // Option 2: If Buy Now button exists, set it there too
      const buyNowBtn = planElement.querySelector('.buy-now-btn');
      if (buyNowBtn) {
        buyNowBtn.dataset.planId = plan.id;
        buyNowBtn.dataset.userType = plan.user_type;
      }

      // Set plan title and description
      const titleElement = planElement.querySelector('h3');
      const descElement = planElement.querySelector('p');

      if (titleElement) titleElement.textContent = `${capitalize(plan.name)} Plan`;
      if (descElement) descElement.textContent = capitalize(plan.description);

      // Update monthly and yearly pricing labels
      const monthlyLabel = planElement.querySelector('.billed-monthly-label');
      const yearlyLabel = planElement.querySelector('.billed-yearly-label');

      if (monthlyLabel) {
        monthlyLabel.innerHTML = `<strong>₦${parseFloat(plan.monthly_price).toLocaleString('en-NG')}</strong>/ monthly`;
      }
      if (yearlyLabel) {
        yearlyLabel.innerHTML = `<strong>₦${parseFloat(plan.yearly_price).toLocaleString('en-NG')}</strong>/ yearly`;
      }

      // Update features list
      const featuresContainer = planElement.querySelector('.pricing-plan-features');
      featuresContainer.querySelector("strong").textContent = `Features of ${capitalize(plan.name)} Plan`;

      // create features list
      const featuresList = featuresContainer.querySelector("ul");
      // Clear existing features
      featuresList.innerHTML = '';

      // Add new features based on plan data
      if (plan.features.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No Features';
        featuresList.appendChild(li);
      }

      plan.features.forEach(feature => {
        const li = document.createElement('li');
        li.textContent = `${capitalize(feature.feature_name.replace(/_/g, ' '))}: ${feature.limit === null ? 'Unlimited' : feature.limit}`;
        featuresList.appendChild(li);
      });    
    });

    return plans;
  } catch (error) {
    console.error('Failed to load pricing plans:', error);
  }
}
    
function buyItNow(plan1, plan2) {
  // Get all Buy Now buttons
  const buyNowButtons = document.querySelectorAll(".buy-now-btn");

  buyNowButtons.forEach(button => {
  button.addEventListener("click", async function (e) {
    e.preventDefault();

    const planId = this.dataset.planId;
    const user_type = this.dataset.userType;

    const plans = user_type === "freelancer" ? plan1 : plan2;

    // Determine billing cycle
    const billingCycle = document.querySelector("#radio-6").checked ? "yearly" : "monthly";

    const selectedPlan = plans.find(plan => plan.id === parseInt(planId));

    if (!selectedPlan) {
      console.error("Plan not found for id:", planId, plans);
      alert("Invalid plan selected");
      return;
    }

    // pick price correctly
    const amount = billingCycle === "yearly"
      ? selectedPlan.yearly_price
      : selectedPlan.monthly_price;

    try {
      const response = await fetchProtected("/api/pricing/orders/", {
        method: "POST",
        body: JSON.stringify({
          plan: planId,
          billing_cycle: billingCycle,
          amount: amount,
        })
      });

      const data = await response.json();
      console.log("Order gotten back: ", data);

      if (response.ok) {
        window.location.href = `/checkout/${data.id}/`;
      } else {
        console.error("Order creation failed:", data);
        alert(data.detail || "Failed to create order. Try again.");
      }
    } catch (error) {
      console.error("Network error:", error);
    }
  });
});
}

document.addEventListener("DOMContentLoaded", async () => {
  // Determine which plans to show based on the logged-in user's role.
  // Falls back to freelancer plans for unauthenticated visitors.
  let role = "freelancer";
  try {
    const authed = await isAuthenticated();
    if (authed && userInfo && userInfo.role === "employer") {
      role = "employer";
    }
  } catch (e) {
    console.warn("Could not resolve user role; defaulting to freelancer plans.", e);
  }

  const plans = await loadPricingPlans(role);

  if (role === "employer") {
    buyItNow(null, plans);
  } else {
    buyItNow(plans, null);
  }
});
    