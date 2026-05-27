document.getElementById('search-box-btn').addEventListener('click', function() {
    where  = document.getElementById('autocomplete-input');
    title = document.getElementById('intro-keywords').value.trim();

    const location = where.getAttribute("value") || where.value.trim();

    const queryParms = new URLSearchParams({
        search: title,
        location: location
    }).toString();

    console.log("Keyword:", title);
    console.log("Location:", location);
    window.location.href = `/jobs/?${queryParms}`;

});



document.addEventListener('DOMContentLoaded', async () => {

  //Job Category

    // Mapping between backend category values and icons
const categoryIcons = {
    accounting_and_finance: "icon-line-awesome-calculator",
    clerical_and_data_entry: "icon-line-awesome-keyboard-o",
    customer_service: "icon-line-awesome-headphones",
    engineering_and_technical: "icon-line-awesome-cogs",
    healthcare: "icon-line-awesome-heartbeat",
    hospitality_and_tourism: "icon-line-awesome-plane",
    information_technology: "icon-line-awesome-laptop",
    legal: "icon-line-awesome-gavel",
    marketing_and_advertising: "icon-line-awesome-bullhorn",
    sales_and_business_development: "icon-line-awesome-shopping-cart",
    skilled_trades_and_services: "icon-line-awesome-wrench",
    education_and_training: "icon-line-awesome-graduation-cap",
    creative_and_design: "icon-line-awesome-paint-brush",
    real_estate_and_property_management: "icon-line-awesome-building",
    transportation_and_logistics: "icon-line-awesome-truck",
    construction_and_maintenance: "icon-line-awesome-road",
    research_and_development: "icon-line-awesome-flask",
    non_profit_and_volunteering: "icon-line-awesome-handshake-o",
    government_and_public_service: "icon-line-awesome-university",
    media_and_entertainment: "icon-line-awesome-video-camera",
    telecommunications: "icon-line-awesome-phone",
    energy_and_utilities: "icon-line-awesome-bolt",
    agriculture_and_environment: "icon-line-awesome-leaf",
    science_and_technology: "icon-line-awesome-rocket",
    other: "icon-line-awesome-briefcase",
};

    const categoriesContainer = document.getElementById("categories-container");
    try {
        const response = await fetch("/api/jobs/job-categories/");
        const categories = await response.json();
        console.log("categories:", categories);
        if (Array.isArray(categories) && categories.length > 0) {
            categoriesContainer.innerHTML = "";
            categories.forEach(category => {
                const iconClass = categoryIcons[category.category] || "icon-line-awesome-briefcase";
                const categoryBox = `
                <a href="/jobs/?category=${category.category}" class="category-box">
                <div class="category-box-icon"><i class="${iconClass}"></i></div>
                <div class="category-box-counter">${category.total}</div>
                <div class="category-box-content">
                <h3>${category.name}</h3>
                <p>Explore ${category.name} jobs</p>
                </div>
                </a>
                `;
                categoriesContainer.innerHTML += categoryBox;
            });
        }
    } catch (error) {
        console.error("Error:", error);
    }



    //Featured Jobs

    const featuredContainer = document.querySelector(".listings-container.compact-list-layout")

    if (featuredContainer) {
      const res = await fetch("/api/jobs/featured-jobs/");

      if (res.ok) {
        const resData = await res.json();
        console.log("Featured Jobs:", resData);

        if (Array.isArray(resData) && resData.length > 0) {
          featuredContainer.innerHTML = "";

          for (const r of resData) {
            const fList = `
            <a href="/job-page/${r.id}/" class="job-listing with-apply-button">

						<!-- Job Listing Details -->
						<div class="job-listing-details">

							<!-- Logo -->
							<div class="job-listing-company-logo">
								<img src="${(r.company_info && r.company_info.logo_url) ? r.company_info.logo_url : '/static/images/company-logo-placeholder.png'}" alt="">
							</div>

							<!-- Details -->
							<div class="job-listing-description">
								<h3 class="job-listing-title">${r.title}</h3>

								<!-- Job Listing Footer -->
								<div class="job-listing-footer">
									<ul>
										<li><i class="icon-material-outline-business"></i> ${r.company_info ? r.company_info.company_name : ''} <div class="verified-badge" title="Verified Employer" data-tippy-placement="top"></div></li>
										<li><i class="icon-material-outline-location-on"></i> ${r.company_info ? r.company_info.company_country : ''}</li>
										<li><i class="icon-material-outline-business-center"></i> ${r.job_type}</li>
										<li><i class="icon-material-outline-access-time"></i> ${r.updated_at ? new Date(r.updated_at).toDateString() : ''}</li>
									</ul>
								</div>
							</div>

							
						</div>
					</a>
          `;
            featuredContainer.insertAdjacentHTML("beforeend", fList);
          }
        }

      }
    } else {
      console.log("Featured Jobs Container Null");
    }


    const featuredCitiesContainer = document.getElementById("featured-cities-container");

if (featuredCitiesContainer) {
  const res = await fetch("/api/jobs/featured-city/");

  if (res.ok) {
    const resData = await res.json();
    console.log("Featured Cities:", resData);
    if (Array.isArray(resData) && resData.length > 0) {
      const cityEmptyState = featuredCitiesContainer.querySelector(".js-empty-state");
      if (cityEmptyState) cityEmptyState.remove();
    }
    for (const r of resData) {
      const cityBox = `
      <div class="col-xl-3 col-md-6">
        <!-- Photo Box -->
        <a href="/jobs/?city=${r.city}" class="photo-box" style="background-image: url('${r.img ? r.img : 'static/images/default-city.png'}');">
          <div class="photo-box-content">
            <h3>${r.city ? r.city : 'Unknown City'}</h3>
            <span>${r.job_count ? r.job_count : 0} Jobs</span>
          </div>
        </a>
      </div>
      `;
      featuredCitiesContainer.insertAdjacentHTML("beforeend", cityBox);
    }
  }
} else {
  console.log("featuredCitiesContainer Null")
}
});

// Fetch profiles using current filters & page
async function loadProfiles() {
    const container = document.querySelector(".freelancers-container");
    const API_BASE = "/api/users/profiles/";
    try {
      const url = `${API_BASE}?page_size=10&page=1&ordering=-rating,created_at`;
      const resp = await fetch(url, { headers: { "Accept": "application/json" } });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const results = data.results || data; // if not paginated
      renderProfiles(results);
    } catch (err) {
      console.error("Failed to load profiles:", err);
      container.innerHTML = `<div class="error">Failed to load profiles. Refresh the page and try again.</div>`;
    }
  }

//   Render profiles
function renderProfiles(profiles = []) {
    console.log("profiles:", profiles);
    const container = document.querySelector(".freelancers-container");
    const emptyState = document.getElementById("freelancers-empty-state");
    container.innerHTML = ""; // clear

    if (!profiles.length) {
        if (emptyState) emptyState.style.display = "";
        return;
    }
    if (emptyState) emptyState.style.display = "none";

    profiles.forEach(profile => {
    const card = document.createElement("div");
    card.className = "freelancer";

    // Map API fields to UI fields with safe fallbacks
    const name = profile.full_name || profile.name || (profile.user && (profile.user.first_name || profile.user.username)) || "Unknown";
    const title = profile.tagline || profile.skill || profile.role || "N/A";
    const avatar = profile.avatar || profile.avatar_url || "images/user-avatar-placeholder.png";
    const isVerified = profile.verified || profile.is_verified || false;
    const rating = (profile.rating !== undefined && profile.rating !== null) ? profile.rating : "N/A";
    const location = profile.nationality || (profile.user && profile.user.location) || "N/A";
    const rate = profile.hourly_rate !== undefined && profile.hourly_rate !== null ? profile.hourly_rate : null;
    const jobSuccess = profile.job_success !== undefined && profile.job_success !== null ? profile.job_success : null;
    const countryCode = profile.country_code || (profile.country && profile.country.toLowerCase && profile.country.toLowerCase()) || null;
    const flagImg = countryCode ? `images/flags/${countryCode.toLowerCase()}.svg` : "";

    card.innerHTML = `
    <div class="freelancer-overview">
    <div class="freelancer-overview-inner">
    <span class="bookmark-icon"></span>
    <div class="freelancer-avatar">
        ${isVerified ? '<div class="verified-badge"></div>' : ''}
        <a href="/freelancer-profile/${profile.id}"><img src="${avatar}" alt=""></a>
    </div>
    <div class="freelancer-name">
        <h4>
        <a href="/freelancer-profile/${profile.id}">
            ${name}
            ${flagImg ? `<img class="flag" src="${flagImg}" alt="${countryCode}" title="${countryCode.toUpperCase()}" data-tippy-placement="top">` : ''}
        </a>
        </h4>
        <span>${title}</span>
    </div>
    <div class="freelancer-rating">
        ${rating ? `<div class="star-rating" data-rating="${rating}"></div>` : `<span class="company-not-rated margin-bottom-5">Minimum of 3 votes required</span>`}
    </div>
    </div>
    </div>

    <div class="freelancer-details">
    <div class="freelancer-details-list">
    <ul>
        <li>Location <strong><i class="icon-material-outline-location-on"></i> ${location}</strong></li>
        <li>Rate <strong>${rate}</strong></li>
        <li>Job Success <strong>${jobSuccess}</strong></li>
    </ul>
    </div>
    <a href="/freelancer-profile/${profile.id}" class="button button-sliding-icon ripple-effect">View Profile <i class="icon-material-outline-arrow-right-alt"></i></a>
    </div>
    `;

    // Append the card to the container
    container.appendChild(card);
    });

    // optional: initialize star ratings or tooltips here if your page uses them
    // e.g. initStarRatings(); initTooltips();
 
    starRating('.star-rating');

    $('.default-slick-carousel').slick('refresh');

}

// function escapeHtml(str) {
//     if (typeof str !== "string") return str;
//     return str.replace(/[&<>"']/g, tag => ({
//         '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
//     }[tag]));
// }

document.addEventListener('DOMContentLoaded', function() {
    loadProfiles();
    updateUserNavInfo();
});

