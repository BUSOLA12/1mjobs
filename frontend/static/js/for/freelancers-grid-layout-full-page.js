// Profiles UI loader with filters + pagination
(() => {
  const API_BASE = "/api/users/profiles/"; // change if needed
  const PAGE_SIZE = 10; // desired page size, also sent to API as page_size

  // DOM refs
  const container = document.querySelector(".freelancers-container");
  const paginationUl = document.querySelector(".pagination ul");
  const searchButton = document.querySelector(".sidebar-search-button-container .button");

  // Filter inputs
  const locationInput = document.querySelector("#autocomplete-input");
  const categorySelect = document.querySelector(".selectpicker.default");
  const keywordInputs = document.getElementById("keywords-list");
  const tagsContainer = document.querySelector(".tags-container");
  const rangeSlider = document.querySelector(".range-slider");
  const extraSKills = document.getElementById("extra-skills-list");
  const sortSelect = document.getElementById('sort-select');

  // Keep last-applied filters so pagination keeps them
  let currentFilters = {};
  let currentPage = 1;

  // Helper: read range slider values robustly (supports plugin value as JSON or simple "min,max")
  function parseRangeValue(sliderEl){
    // if (!sliderEl) return { min: null, max: null };
    // // try data-slider-value attribute first
    // const dataVal = sliderEl.getAttribute("data-slider-value") || sliderEl.value || "";
    // try {
    //   // common plugin format: "[10,250]" or JSON-like
    //   const parsed = JSON.parse(dataVal);
    //   if (Array.isArray(parsed) && parsed.length >= 2) {
    //     return { min: Number(parsed[0]) || null, max: Number(parsed[1]) || null };
    //   }
    // } catch (e) {
    //   // not JSON - try "10,250" or "10 250"
    //   const cleaned = dataVal.replace(/[\[\]\s]+/g, "");
    //   if (cleaned.includes(",")) {
    //     const [a,b] = cleaned.split(",");
    //     return { min: Number(a) || null, max: Number(b) || null };
    //   }
    // }
    // // fallback to data attributes
    // const minAttr = sliderEl.getAttribute("data-slider-min");
    // const maxAttr = sliderEl.getAttribute("data-slider-max");
    // return { min: Number(minAttr) || null, max: Number(maxAttr) || null };

    const minValue = document.getElementById("min-value")
    const maxValue = document.getElementById("max-value")

    return { min: Number(minValue.value) || null, max: Number(maxValue.value) || null };
  }

  // Collect filter values from sidebar
  function getFiltersFromUI() {
    const filters = {};

    // Location
    const location = locationInput ? locationInput.value.trim() : "";
    if (location) filters.location = location;

    // Categories (multiple)
    if (categorySelect) {
      const selected = Array.from(categorySelect.selectedOptions).map(o => o.value || o.textContent.trim());
      if (selected.length) filters.categories = selected;
    }

    // Keywords (collect all keyword-inputs values + tokens inside keywords-list if any)
    const keywords = [];
    keywordInputs.querySelectorAll(".keyword").forEach(input => {
      const v = input.textContent && input.textContent.trim();
      if (v) keywords.push(v);
    });

    if (keywords.length) filters.keywords = keywords;

    // Hourly Rate
    const range = parseRangeValue(rangeSlider);
    if (range.min !== null) filters.min_rate = range.min;
    if (range.max !== null) filters.max_rate = range.max;

    // Skills: checked checkboxes inside .tags-container AND any custom skill keyword-input (assume second keywords input is skills)
    const skills = [];
    if (tagsContainer) {
      tagsContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (cb.checked) {
          // try to read associated label text
          const id = cb.id;
          let labelText = "";
          if (id) {
            const lbl = document.querySelector(`label[for="${id}"]`);
            if (lbl) labelText = lbl.textContent.trim();
          }
          if (!labelText && cb.nextSibling) labelText = cb.nextSibling.textContent.trim();
          if (labelText) skills.push(labelText);
        }
      });
    }
    // collect "add more skills" inputs (there's likely another .keyword-input for skills)
    extraSKills.querySelectorAll(".keyword").forEach(input => {
      const v = input.textContent && input.textContent.trim();
      if (v) skills.push(v);
    });

    // Deduplicate and normalize skills/keywords
    if (skills.length) filters.skills = Array.from(new Set(skills.map(s => s.toLowerCase())));

    // final normalization of keywords
    if (filters.keywords) filters.keywords = Array.from(new Set(filters.keywords.map(s => s.toLowerCase())));
    
    // Sort
    let sortVal = sortSelect.value.toLowerCase();
    switch (sortVal) {
      case 'newest': filters.ordering = '-created_at'; break;
      case 'oldest': filters.ordering = 'created_at'; break;
      case 'relevance': filters.ordering = '-rating'; break;
      case 'random': filters.random = true; break; // handle separately
    }

    return filters;
  }

  // Build a query string from filters + page
  function buildQuery(filters = {}, page = 1) {
    const params = new URLSearchParams();

    // Always include page_size so backend returns consistent pages
    params.set("page_size", PAGE_SIZE);
    if (page && page > 1) params.set("page", page);

    if (filters.location) params.set("location", filters.location);
    if (filters.categories && filters.categories.length) params.set("category", filters.categories.join(",")); // backend should accept comma list or you can change to multiple param keys
    if (filters.min_rate != null) params.set("min_rate", String(filters.min_rate));
    if (filters.max_rate != null) params.set("max_rate", String(filters.max_rate));

    // keywords -> use DRF `search` param (space-joined)
    if (filters.keywords && filters.keywords.length) params.set("search", filters.keywords.join(","));

    // skills -> comma separated
    if (filters.skills && filters.skills.length) params.set("skills", filters.skills.join(","));

    // ordering
    if (filters.ordering) {
      params.set("ordering", filters.ordering);
    }

    // random
    if (filters.random) {
      params.set("random", "true");
    }

    return params.toString();
  }

  // Fetch profiles using current filters & page
  async function loadProfiles(page = 1) {
    try {
      currentPage = page;
      const queryString = buildQuery(currentFilters, page);
      console.log(queryString);
      const url = queryString ? `${API_BASE}?${queryString}` : `${API_BASE}?page_size=${PAGE_SIZE}&page=${page}`;
      const resp = await fetch(url, { headers: { "Accept": "application/json" } });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const results = data.results || data; // if not paginated
      renderProfiles(results);
      renderPagination(data.count ?? results.length, data.next ?? null, data.previous ?? null, page);

      hideLoading();
    } catch (err) {
      console.error("Failed to load profiles:", err);
      container.innerHTML = `<div class="error">Failed to load profiles. Refresh the page and try again.</div>`;
      paginationUl.innerHTML = "";
    }
  }

  // Render a single card using the HTML structure you provided
  async function renderProfiles(profiles = []) {
    container.innerHTML = ""; // clear

    if (!profiles.length) {
      container.innerHTML = `<div class="no-results">No profiles found</div>`;
      return;
    }

    profiles.forEach(profile => {
      const card = document.createElement("div");
      card.className = "freelancer";

      // Map API fields to UI fields with safe fallbacks
      const name = profile.full_name || profile.name || (profile.user && (profile.user.first_name || profile.user.username)) || "Unnamed freelancer";
      const title = profile.tagline || profile.skill || profile.role || "";
      const PLACEHOLDER_AVATAR = "/static/images/user-avatar-placeholder.png";
      const avatar = profile.avatar || profile.avatar_url || PLACEHOLDER_AVATAR;
      const isVerified = profile.verified || profile.is_verified || false;
      const isPro = profile.is_pro || false;
      const rating = (profile.rating !== undefined && profile.rating !== null) ? parseFloat(profile.rating) : null;
      const location = profile.nationality || (profile.user && profile.user.location) || null;
      const rateNum = parseFloat(profile.hourly_rate);
      const rate = (!isNaN(rateNum) && rateNum > 0) ? rateNum : null;
      const jsNum = parseFloat(profile.job_success);
      const jobSuccess = (!isNaN(jsNum) && jsNum > 0) ? jsNum : null;
      const empty = '<span style="color:#b0b0b0;font-weight:400;">Not provided</span>';
      const countryName = profile.nationality || profile.country || (profile.user && profile.user.location) || null;
      const flagImg = countryName && typeof getFlagUrl === "function" ? getFlagUrl(countryName) : null;

      card.innerHTML = `
        <div class="freelancer-overview">
          <div class="freelancer-overview-inner">
            <span class="bookmark-icon" data-userprofile-id="${profile.id}"></span>
            <div class="freelancer-avatar">
              ${isVerified ? '<div class="verified-badge"></div>' : ''}
              <a href="/freelancer-profile/${profile.id}"><img src="${avatar}" alt="" onerror="this.onerror=null;this.src='${PLACEHOLDER_AVATAR}';"></a>
            </div>
            <div class="freelancer-name">
              <h4>
                <a href="/freelancer-profile/${profile.id}">
                  ${escapeHtml(name)}
                  ${isPro ? '<span class="pro-badge" title="Pro member">PRO</span>' : ''}
                  ${flagImg ? `<img class="flag" src="${flagImg}" alt="${countryName}" title="${countryName}" data-tippy-placement="top" onerror="this.style.display='none'">` : ''}
                </a>
              </h4>
              <span>${title ? escapeHtml(title) : '<span style="color:#b0b0b0;">No tagline yet</span>'}</span>
            </div>
            <div class="freelancer-rating">
              ${rating>0 ? `<div class="star-rating" data-rating="${rating}"></div>` : `<span class="company-not-rated margin-bottom-5">No ratings yet</span>`}
            </div>
          </div>
        </div>

        <div class="freelancer-details">
          <div class="freelancer-details-list">
            <ul>
              <li>Location <strong>${location ? `<i class="icon-material-outline-location-on"></i> ${escapeHtml(location)}` : empty}</strong></li>
              <li>Rate <strong>${rate ? `₦${escapeHtml(String(rate))} / hr` : empty}</strong></li>
              <li>Job Success <strong>${jobSuccess ? `${escapeHtml(String(jobSuccess))}%` : empty}</strong></li>
            </ul>
          </div>
          <a href="/freelancer-profile/${profile.id}" class="button button-sliding-icon ripple-effect">View Profile <i class="icon-material-outline-arrow-right-alt"></i></a>
        </div>
      `;

      container.appendChild(card);

      // attached bookmark handler
      const bookmarkIcon = card.querySelector(".bookmark-icon");

      disableButton(bookmarkIcon, "", profile.id);

      bookmarkIcon.addEventListener("click", async (e) => {
        const el = e.currentTarget;
        if (!await requireLogin()) return;

        const isBookmarked = el.classList.contains("bookmarked");
        el.style.pointerEvents = "none";
        const ok = await bookmarkHandling(isBookmarked ? "delete" : "create", "userprofile", el);
        el.style.pointerEvents = "";

        if (ok) el.classList.toggle("bookmarked", !isBookmarked);
      });
    });

    // optional: initialize star ratings or tooltips here if your page uses them
    // e.g. initStarRatings(); initTooltips();
    $('.star-rating').empty();
    starRating('.star-rating');

    // Cards are on screen; now mark which freelancers are already bookmarked
    // (runs after render so it never blocks or flashes an empty grid).
    const bookmarkMap = await getBookmarkedProfileMap();
    Object.keys(bookmarkMap).forEach(profileId => {
      const icon = container.querySelector(`.bookmark-icon[data-userprofile-id="${profileId}"]`);
      if (icon) {
        icon.classList.add("bookmarked");
        icon.setAttribute("data-bookmark-id", bookmarkMap[profileId]);
      }
    });
  }

  

  // Render pagination UI and attach click handlers
  function renderPagination(totalCount = 0, next = null, previous = null, current = 1) {
    paginationUl.innerHTML = "";

    const pageSize = PAGE_SIZE;
    const totalPages = Math.max(1, Math.ceil((totalCount || 0) / pageSize));
    const currentPageLocal = current || 1;

    // Prev arrow
    const prevLi = document.createElement("li");
    prevLi.className = "pagination-arrow";
    prevLi.innerHTML = `<a href="#" class="ripple-effect"><i class="icon-material-outline-keyboard-arrow-left"></i></a>`;
    if (previous) {
      prevLi.addEventListener("click", e => {
        e.preventDefault();
        // previous may be full url; parse page param if present
        const page = extractPageFromUrl(previous) || Math.max(1, currentPageLocal - 1);
        loadProfiles(page);
      });
    } else {
      prevLi.classList.add("disabled");
    }
    paginationUl.appendChild(prevLi);

    // Show a window of pages around the current page (for long lists)
    const maxButtons = 7;
    let start = Math.max(1, currentPageLocal - Math.floor(maxButtons / 2));
    let end = Math.min(totalPages, start + maxButtons - 1);
    if (end - start < maxButtons - 1) start = Math.max(1, end - maxButtons + 1);

    for (let i = start; i <= end; i++) {
      const li = document.createElement("li");
      li.innerHTML = `<a href="#" class="ripple-effect ${i === currentPageLocal ? "current-page" : ""}">${i}</a>`;
      if (i === currentPageLocal) {
        // no click
      } else {
        li.addEventListener("click", e => {
          e.preventDefault();
          loadProfiles(i);
        });
      }
      paginationUl.appendChild(li);
    }

    // Next arrow
    const nextLi = document.createElement("li");
    nextLi.className = "pagination-arrow";
    nextLi.innerHTML = `<a href="#" class="ripple-effect"><i class="icon-material-outline-keyboard-arrow-right"></i></a>`;
    if (next) {
      nextLi.addEventListener("click", e => {
        e.preventDefault();
        const page = extractPageFromUrl(next) || Math.min(totalPages, currentPageLocal + 1);
        loadProfiles(page);
      });
    } else {
      nextLi.classList.add("disabled");
    }
    paginationUl.appendChild(nextLi);
  }

  // Utility to extract page value from DRF next/previous full URL
  function extractPageFromUrl(url) {
    try {
      const u = new URL(url, window.location.origin);
      const p = parseInt(u.searchParams.get("page"), 10);
      return isNaN(p) ? null : p;
    } catch (e) {
      return null;
    }
  }

  // Very small HTML escaper
  function escapeHtml(str) {
    if (typeof str !== "string") return str;
    return str.replace(/[&<>"']/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[tag]));
  }

  function searchHandler(e) {
    e.preventDefault();
    currentFilters = getFiltersFromUI();
    showLoading();
    loadProfiles(1);
  }

  // Attach event listener to Search button
  if (searchButton) {
    searchButton.addEventListener("click", searchHandler);
  }

  // Attach event listener to sortSelect
  if (sortSelect) {
    sortSelect.addEventListener("change", searchHandler);
  }

  // Initial load (no filters)
  currentFilters = getFiltersFromUI(); // read defaults if any

  showLoading();
  loadProfiles(1);

})();
