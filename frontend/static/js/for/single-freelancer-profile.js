function getUUID() {
    const pathSegments = window.location.pathname.split('/').filter(Boolean);

    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    let lastUuid = null;

    // Iterate backwards to find the first segment that matches the UUID pattern
    for (let i = pathSegments.length - 1; i >= 0; i--) {
        if (uuidRegex.test(pathSegments[i])) {
            lastUuid = pathSegments[i];
            break; // Stop after finding the first UUID (from the end)
        }
    }

    // Now you can use lastUuid
    if (lastUuid) {
        return lastUuid;
    } else {
        console.log("No UUID found in the URL path.");
        return null;
    }
}

const pathSegments = window.location.pathname.split('/').filter(Boolean);
const lastSegment = pathSegments[pathSegments.length - 1];

const profileId = parseInt(lastSegment);

async function loadWorkHistory(url) {
    const listContainer = document.querySelector(".boxed-list-ul#work-history-list");

    // Clear existing items
    listContainer.innerHTML = "";

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include" // include cookies/session if needed
        });

        if (!response.ok) {
            console.error("Failed to fetch work history");
            return;
        }


        const data = await response.json();

        if (data.length === 0) {
            const li = document.createElement("li");
            li.innerHTML = `
                <div class="boxed-list-item">
                    <div class="item-content">
                        <h4>No work history found</h4>
                    </div>
                </div>
            `;
            listContainer.appendChild(li);
            return;
        }

        data.forEach(item => {
            const li = document.createElement("li");

            li.innerHTML = `
                <div class="boxed-list-item">

                    <!-- Avatar (use default image) -->
                    <div class="item-image">
                        <img src="images/browse-companies-03.png" alt="">
                    </div>

                    <!-- Content -->
                    <div class="item-content">
                        <h4>${item.work_role}</h4>

                        <div class="item-details margin-top-7">
                            <div class="detail-item">
                                <a href="#"><i class="icon-material-outline-business"></i> ${item.company_name}</a>
                            </div>

                            <div class="detail-item">
                                <i class="icon-material-outline-date-range"></i> 
                                ${item.start_month_year} - ${item.end_month_year}
                            </div>
                        </div>

                        <div class="item-description">
                            <p>${item.responsibilities}</p>
                        </div>
                    </div>

                </div>
            `;

            listContainer.appendChild(li);
        });

    } catch (error) {
        console.error("Error loading work history:", error);
    }
}


const REVIEWS_PER_PAGE = 5;
let allUserReviews = [];

function renderReviewsPage(page) {
    const reviewsList = document.querySelector('#work-history-and-feedback-list');
    reviewsList.innerHTML = '';

    const start = (page - 1) * REVIEWS_PER_PAGE;
    const pageReviews = allUserReviews.slice(start, start + REVIEWS_PER_PAGE);

    pageReviews.forEach(review => {
        // Create a new list item element
        const li = document.createElement('li');
        li.innerHTML = `
        <div class="boxed-list-item">
          <div class="item-content">
            <h4>${review.object_title} <span>Rated as ${review.role}</span></h4>
            <div class="item-details margin-top-10">
              <div class="star-rating" data-rating="${review.rating}"></div>
              <div class="detail-item">
                <i class="icon-material-outline-date-range"></i> ${review.created_at}
              </div>
            </div>
            ${review.review_text ? `
              <div class="item-description">
                <p>${review.review_text}</p>
              </div>` : ''}
          </div>
        </div>
      `;
        reviewsList.appendChild(li);
    });

    // Optionally initialize star ratings if your template uses JS for them
    $('.star-rating').empty();
    starRating('.star-rating');

    renderReviewsPagination(page);
}

function renderReviewsPagination(currentPage) {
    const container = document.getElementById('reviews-pagination-container');
    const ul = document.getElementById('reviews-pagination');
    if (!container || !ul) return;

    const totalPages = Math.ceil(allUserReviews.length / REVIEWS_PER_PAGE);

    // Hide the pagination entirely when everything fits on a single page
    // (this also covers the empty / "No reviews found." case).
    if (totalPages <= 1) {
        container.style.display = 'none';
        ul.innerHTML = '';
        return;
    }

    ul.innerHTML = '';
    container.style.display = '';

    // Prev arrow
    if (currentPage > 1) {
        const prev = document.createElement('li');
        prev.className = 'pagination-arrow';
        prev.innerHTML = `<a href="#" class="ripple-effect"><i class="icon-material-outline-keyboard-arrow-left"></i></a>`;
        prev.addEventListener('click', e => { e.preventDefault(); renderReviewsPage(currentPage - 1); });
        ul.appendChild(prev);
    }

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.innerHTML = `<a href="#" class="ripple-effect ${i === currentPage ? 'current-page' : ''}">${i}</a>`;
        if (i !== currentPage) {
            li.addEventListener('click', e => { e.preventDefault(); renderReviewsPage(i); });
        }
        ul.appendChild(li);
    }

    // Next arrow
    if (currentPage < totalPages) {
        const next = document.createElement('li');
        next.className = 'pagination-arrow';
        next.innerHTML = `<a href="#" class="ripple-effect"><i class="icon-material-outline-keyboard-arrow-right"></i></a>`;
        next.addEventListener('click', e => { e.preventDefault(); renderReviewsPage(currentPage + 1); });
        ul.appendChild(next);
    }
}

async function loadUserReviews(userId) {
    const reviewsList = document.querySelector('#work-history-and-feedback-list');
    reviewsList.innerHTML = '<li><p>Loading reviews...</p></li>'; // Clear any existing content

    // Keep pagination hidden until we know how many reviews there are
    const paginationContainer = document.getElementById('reviews-pagination-container');
    if (paginationContainer) paginationContainer.style.display = 'none';

    try {
        const reviews = await getReviewsReceived(userId);

        if (!reviews.length) {
            reviewsList.innerHTML = `<li><p>No reviews found.</p></li>`;
            return;
        }

        allUserReviews = reviews;
        renderReviewsPage(1);

    } catch (error) {
        console.error('Error loading reviews:', error);
        reviewsList.innerHTML = `<li><p>Unable to load reviews at this time.</p></li>`;
    }
}

let profileUserId = null;

async function loadProfile(profileId) {
    try {
        // Fetch profile data from backend
        const response = await fetch(`/api/users/profiles/${profileId}/`);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const data = await response.json();

        profileUserId = await data.user_id;

        console.log("Profile data:", data);

        // ===== 1. Avatar & Name =====
        const profileAvatarEl = document.querySelector(".header-image img");
        profileAvatarEl.src = data.avatar || "/static/images/user-avatar-placeholder.png";
        profileAvatarEl.onerror = function () {
            this.onerror = null;
            this.src = "/static/images/user-avatar-placeholder.png";
        };
        const displayName = (data.full_name && data.full_name.trim()) ? data.full_name : "Unnamed freelancer";
        document.querySelector(".header-details h3").innerHTML = `
            ${displayName} <span>${data.tagline || "No tagline yet"}</span>
        `;

        // ===== 2. Rating =====
        const rating = parseFloat(data.rating) || 0;
        const ratingElement = document.querySelector(".star-rating");
        if (ratingElement) {
            if (rating > 0) {
                ratingElement.setAttribute("data-rating", rating);
                $('.star-rating').empty();
                starRating('.star-rating');
            } else {
                // No reviews: show a clean label instead of "0.0" + empty stars.
                ratingElement.removeAttribute("data-rating");
                ratingElement.classList.remove("star-rating");
                ratingElement.innerHTML = '<span style="color:#888;font-size:14px;">No ratings yet</span>';
            }
        }

        // ===== 3. Nationality =====
        const nationalityLi = document.querySelector(".header-details ul li:nth-child(2)");
        if (nationalityLi) {
            // Assuming flag images are based on nationality name or ISO code
            const flagUrl = typeof getFlagUrl === "function" ? getFlagUrl(data.nationality) : null;
            nationalityLi.innerHTML = `${flagUrl ? `<img class="flag" src="${flagUrl}" alt="${data.nationality}" onerror="this.style.display='none'"> ` : ''}${data.nationality}`;
        }

        // ===== 4. Verified Badge =====
        const verifiedLi = document.getElementById("verified-badge");
        if (data.verified) {
            verifiedLi.innerHTML = `<div class="verified-badge-with-title">Verified</div>`;
        } else {
            verifiedLi.innerHTML = "";
        }

        // ===== 5. Bio =====
        // create a loop that create a paragraph for every newline in data.bio
        const aboutSection = document.querySelector(".single-page-section");
        if (aboutSection) {
            aboutSection.innerHTML = `
                <h3 class="margin-bottom-25">About Me</h3>
            `;

            const bio = (data.bio || "").trim();
            if (bio) {
                bio.split("\n").forEach(paragraph => {
                    aboutSection.innerHTML += `<p>${paragraph}</p>`;
                });
            } else {
                aboutSection.innerHTML += `<p style="color:#888;">This freelancer hasn't added a bio yet.</p>`;
            }
        }

        // ===== 6. Overview =====
        document.getElementById("hourly_rate").textContent = parseInt(data.hourly_rate) || 0;
        document.getElementById("jobs_done").textContent = data.job_success || 0;
        document.getElementById("rehired").textContent = data.rehired || 0;

        // ===== 7. Skills =====
        const skillsContainer = document.querySelector(".task-tags");
        if (skillsContainer) {
            const skillsArray = data.skills ? data.skills.split(",").map(s => s.trim()).filter(Boolean) : [];
            if (skillsArray.length) {
                skillsContainer.innerHTML = skillsArray.map(skill => `<span>${skill}</span>`).join(' ');
            } else {
                skillsContainer.innerHTML = `<span style="color:#888;">No skills listed yet.</span>`;
            }

            if (window.refreshKeywordsUI) {
                window.refreshKeywordsUI();
            }
        }

        // handle Bookmark button
        const bookmarkButton = document.querySelector(".bookmark-button");
        initBookmarkButton(bookmarkButton, "userprofile", profileId);

        // ===== 8. Files / Attachments (CV files and/or a portfolio link) =====
        const attachmentsContainer = document.querySelector(".attachments-container");
        if (attachmentsContainer) {
            attachmentsContainer.innerHTML = "";
            const portfolioUrl = (data.portfolio_url || "").trim();
            const hasFiles = data.files && data.files.length > 0;

            if (portfolioUrl) {
                const link = document.createElement("a");
                link.href = portfolioUrl;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                link.className = "attachment-box ripple-effect";
                link.innerHTML = `<span>Portfolio</span><i>LINK</i>`;
                attachmentsContainer.appendChild(link);
            }

            if (hasFiles) {
                data.files.forEach(file => {
                    const fileName = file.split("/").pop();
                    const fileExt = fileName.split(".").pop().toUpperCase();
                    const a = document.createElement("a");
                    a.href = file;
                    a.className = "attachment-box ripple-effect";
                    a.innerHTML = `<span>${fileName}</span><i>${fileExt}</i>`;
                    attachmentsContainer.appendChild(a);
                });
            }

            if (!portfolioUrl && !hasFiles) {
                attachmentsContainer.innerHTML = "<p>No attachments</p>";
            }
        }

        // ===== 9. Work History =====
        await loadUserReviews(profileId);

        // Load Work History
        await loadWorkHistory(`/api/users/work-history/?id=${profileId}`);

        // 
        document.querySelector("#small-dialog .welcome-text h3").innerText = `Discuss your project with ${data.full_name.split(" ")[0] || "this freelancer"}`;


    } catch (error) {
        console.error("Error loading profile:", error);
    }

    hideLoading();
}

async function submitOffer(formId, fileInputId) {

    // Step 2: prepare form data
    const form = document.getElementById(formId);
    const fileInput = document.getElementById(fileInputId);
    const message = form.querySelector("textarea[name='textarea']").value;

    // Basic validation
    if (!message) {
        appendError("Message is a required field.", "error", "send-offer-error-container");
        console.error("Message is a required field.");
        return;
    }

    // Job/task link (optional). Warn if the employer sends without linking one.
    const linkSelect = document.getElementById("offer-link-select");
    const linkValue = linkSelect ? linkSelect.value : "";
    if (!linkValue) {
        const proceed = confirm(
            "This offer isn't linked to any of your jobs or tasks. " +
            "Linking it helps the freelancer know what it's about. Send it anyway?"
        );
        if (!proceed) return;
    }

    const formData = new FormData();
    formData.append("message", message);
    formData.append("receiver", profileUserId);

    // linkValue looks like "job:12" or "task:5".
    if (linkValue) {
        const [kind, id] = linkValue.split(":");
        if (kind === "job") formData.append("job", id);
        else if (kind === "task") formData.append("task", id);
    }

    // Attach multiple files
    if (fileInput && fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append("uploaded_files", fileInput.files[i]);
        }
    }

    // Step 3: send offer
    try {
        const response = await fetchProtected("/api/offers/create/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Offer submission failed:", errorData);
            const firstKey = Object.keys(errorData)[0];
            const msg = firstKey
                ? (Array.isArray(errorData[firstKey]) ? errorData[firstKey][0] : errorData[firstKey])
                : "Failed to send offer";
            appendError(msg, "error", "send-offer-error-container");
            return;
        }

        appendError("Offer sent successfully!", "success");
        $.magnificPopup.close();  // close modal if using MagnificPopup
        form.reset();

    } catch (error) {
        console.error("Offer submission error:", error);
        appendError("A network error occurred while sending the offer.");
    }
}

// Populate the offer's job/task selector with the current employer's own
// jobs and tasks so they can tie the offer to one.
async function loadOfferLinkOptions() {
    const select = document.getElementById("offer-link-select");
    if (!select) return;
    try {
        const [jobsRes, tasksRes] = await Promise.all([
            fetchProtected("/api/jobs/managelist/"),
            fetchProtected("/api/tasks/managelist/"),
        ]);
        const jobsData = jobsRes.ok ? await jobsRes.json() : {};
        const tasks = tasksRes.ok ? await tasksRes.json() : [];
        const jobs = Array.isArray(jobsData) ? jobsData : (jobsData.results || []);

        if (jobs.length) {
            const g = document.createElement("optgroup");
            g.label = "Jobs";
            jobs.forEach(j => {
                const o = document.createElement("option");
                o.value = `job:${j.id}`;
                o.textContent = j.title || `Job #${j.id}`;
                g.appendChild(o);
            });
            select.appendChild(g);
        }
        if (Array.isArray(tasks) && tasks.length) {
            const g = document.createElement("optgroup");
            g.label = "Tasks";
            tasks.forEach(t => {
                const o = document.createElement("option");
                o.value = `task:${t.id}`;
                o.textContent = t.project_name || `Task #${t.id}`;
                g.appendChild(o);
            });
            select.appendChild(g);
        }
    } catch (err) {
        console.error("Failed to load your jobs/tasks for the offer link:", err);
    }
}

showLoading()
loadProfile(profileId);

document.addEventListener("DOMContentLoaded", function () {

    loadOfferLinkOptions();

    initiateFeatureCheck("make-an-offer-btn", "offers", () => {
        submitOffer("make-an-offer-form", "upload");
    });

});
