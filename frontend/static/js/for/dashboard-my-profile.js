function addAvatarBadge(wrapper) {
    if (!wrapper || wrapper.querySelector(".avatar-edit-badge")) return;
    const badge = document.createElement("a");
    badge.href = "/dashboard/settings/";
    badge.className = "avatar-edit-badge";
    badge.title = "Add profile photo";
    badge.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>`;
    wrapper.appendChild(badge);
}

const EMPTY_ICONS = {
    thumbsUp: `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>`,
    briefcase: `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`,
    user: `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
    tag: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>`,
    paperclip: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>`,
};

async function loadMyProfileWorkHistory(userId) {
    const listContainer = document.querySelector("#work-history-list");
    listContainer.innerHTML = "";

    try {
        const response = await fetch(`/api/users/work-history/?id=${userId}`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
            credentials: "include"
        });

        if (!response.ok) {
            console.error("Failed to fetch work history");
            return;
        }

        const data = await response.json();

        if (!data.length) {
            listContainer.innerHTML = `
                <li>
                    <div class="empty-state">
                        <div class="empty-state-icon">${EMPTY_ICONS.briefcase}</div>
                        <h4>No Employment History Yet</h4>
                        <p>Add your past jobs and roles to help clients understand your professional background.</p>
                        <a href="/dashboard/settings/" class="button ripple-effect">Add Employment History</a>
                    </div>
                </li>`;
            return;
        }

        data.forEach(item => {
            const li = document.createElement("li");
            li.innerHTML = `
                <div class="boxed-list-item">
                    <div class="item-image">
                        <img src="/static/images/browse-companies-03.png" alt="">
                    </div>
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
        console.error("Error loading employment history:", error);
    }
}

async function loadMyProfileReviews(profileId) {
    const reviewsList = document.querySelector("#work-history-and-feedback-list");
    reviewsList.innerHTML = "<li><p>Loading reviews...</p></li>";

    try {
        const reviews = await getReviewsReceived(profileId);

        if (!reviews.length) {
            reviewsList.innerHTML = `
                <li>
                    <div class="empty-state">
                        <div class="empty-state-icon">${EMPTY_ICONS.thumbsUp}</div>
                        <h4>No Feedback Yet</h4>
                        <p>Complete your first job to start receiving feedback and reviews from clients.</p>
                    </div>
                </li>`;
            return;
        }

        reviewsList.innerHTML = "";
        reviews.forEach(review => {
            const li = document.createElement("li");
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
                        ${review.review_text ? `<div class="item-description"><p>${review.review_text}</p></div>` : ""}
                    </div>
                </div>
            `;
            reviewsList.appendChild(li);
        });

        if (typeof starRating === "function") {
            $(".star-rating").empty();
            starRating(".star-rating");
        }

    } catch (error) {
        console.error("Error loading reviews:", error);
        reviewsList.innerHTML = `<li><p>Unable to load reviews at this time.</p></li>`;
    }
}

async function loadMyProfile() {
    try {
        const meResponse = await fetchProtected("/api/users/me/", {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        if (!meResponse.ok) throw new Error("Failed to fetch profile");

        const me = await meResponse.json();

        const profileId = me.id;
        const userId = me.user?.id;

        const detailResponse = await fetch(`/api/users/profiles/${profileId}/`);
        if (!detailResponse.ok) throw new Error("Failed to fetch profile detail");
        const detail = await detailResponse.json();

        // Avatar
        const avatarEl = document.getElementById("profile-avatar");
        const avatarWrapper = document.querySelector(".profile-avatar-wrapper");
        if (avatarEl) {
            if (me.avatar) {
                avatarEl.src = me.avatar;
                avatarEl.onerror = function () {
                    this.src = "/static/images/user-avatar-placeholder.png";
                    avatarWrapper && avatarWrapper.classList.add("avatar-empty");
                    addAvatarBadge(avatarWrapper);
                };
            } else {
                avatarEl.src = "/static/images/user-avatar-placeholder.png";
                if (avatarWrapper) {
                    avatarWrapper.classList.add("avatar-empty");
                    addAvatarBadge(avatarWrapper);
                }
            }
        }

        // Full name
        const firstName = me.user?.first_name || "";
        const lastName = me.user?.last_name || "";
        const fullName = `${firstName} ${lastName}`.trim();
        const nameEl = document.getElementById("profile-fullname");
        if (nameEl) {
            if (fullName) {
                nameEl.textContent = fullName;
            } else {
                nameEl.innerHTML = `<span class="name-placeholder">Add your name</span>
                    <a href="/dashboard/settings/" class="name-edit-link" title="Edit Profile">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </a>`;
            }
        }

        // Star rating
        const ratingEl = document.getElementById("profile-star-rating");
        if (ratingEl) {
            ratingEl.setAttribute("data-rating", detail.rating || "0");
            if (typeof starRating === "function") {
                $(".star-rating").empty();
                starRating(".star-rating");
            }
        }

        // Account type (freelancer / employer)
        const accountTypeEl = document.getElementById("profile-account-type");
        if (accountTypeEl) {
            const role = (me.user?.role || "").toLowerCase();
            if (role === "freelancer") {
                accountTypeEl.innerHTML = `<i class="icon-material-outline-account-circle"></i> Freelancer`;
            } else if (role === "employer") {
                accountTypeEl.innerHTML = `<i class="icon-material-outline-business-center"></i> Employer`;
            } else {
                accountTypeEl.innerHTML = "";
            }
        }

        // Nationality (skip placeholder values saved by old bug)
        const nationalityEl = document.getElementById("profile-nationality");
        const nationality = me.nationality || "";
        const isValidNationality = nationality && !nationality.toLowerCase().startsWith("select");
        if (nationalityEl && isValidNationality) {
            const code = nationality.toLowerCase().slice(0, 2);
            nationalityEl.innerHTML = `<img class="flag" src="/static/images/flags/${code}.svg" alt=""> ${nationality}`;
        }

        // Verified badge
        const verifiedEl = document.getElementById("verified-badge");
        if (verifiedEl) {
            verifiedEl.innerHTML = detail.verified
                ? `<div class="verified-badge-with-title">Verified</div>`
                : "";
        }

        // Employers don't have a marketable freelancer profile, so hide the
        // freelancer-only sections (bio, hourly rate, skills, attachments and
        // employment history). Mirrors the freelancer-only fields hidden on the
        // settings page. Company Profile and Feedback stay visible for them.
        const isEmployer = (me.user?.role || "").toLowerCase() === "employer";
        if (isEmployer) {
            [
                "about-section",
                "hourly-rate-overview",
                "jobs-done-overview",
                "rehired-overview",
                "freelancer-indicators-widget",
                "skills-widget",
                "attachments-widget",
                "employment-history-box",
            ].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = "none";
            });

            // Show employer activity metrics in place of the hidden tiles.
            const jobsPostedEl = document.getElementById("jobs_posted");
            const hiresEl = document.getElementById("hires");
            if (jobsPostedEl) jobsPostedEl.textContent = detail.jobs_posted ?? 0;
            if (hiresEl) hiresEl.textContent = detail.hires ?? 0;
            const jobsPostedTile = document.getElementById("jobs-posted-overview");
            const hiresTile = document.getElementById("hires-overview");
            if (jobsPostedTile) jobsPostedTile.style.display = "";
            if (hiresTile) hiresTile.style.display = "";
        }

        // Bio / About Me
        const aboutSection = document.getElementById("about-section");
        if (aboutSection) {
            if (me.bio && me.bio.trim()) {
                aboutSection.innerHTML = `<h3 class="margin-bottom-25">About Me</h3>`;
                me.bio.split("\n").forEach(paragraph => {
                    aboutSection.innerHTML += `<p>${paragraph}</p>`;
                });
            } else {
                aboutSection.innerHTML = `
                    <h3 class="margin-bottom-25">About Me</h3>
                    <div class="about-empty-state">
                        <div class="about-empty-state-icon">${EMPTY_ICONS.user}</div>
                        <h4>No Bio Added Yet</h4>
                        <p>Tell clients about yourself — your skills, experience, and what makes you stand out.</p>
                        <a href="/dashboard/settings/" class="button ripple-effect">Add Your Bio</a>
                    </div>`;
            }
        }

        // Hourly rate
        document.getElementById("hourly_rate").textContent = parseInt(me.hourly_rate) || 0;

        // Overview tiles: jobs done & rehired
        const jobsDoneEl = document.getElementById("jobs_done");
        if (jobsDoneEl) jobsDoneEl.textContent = detail.jobs_done || 0;
        const rehiredEl = document.getElementById("rehired");
        if (rehiredEl) rehiredEl.textContent = detail.rehired || 0;

        // Performance indicators: set the number and fill the progress bar.
        const setIndicator = (id, pct) => {
            pct = Math.max(0, Math.min(100, Math.round(Number(pct) || 0)));
            const strong = document.getElementById(id);
            if (!strong) return;
            strong.textContent = pct + "%";
            const bar = strong.closest(".indicator")?.querySelector(".indicator-bar span");
            if (bar) bar.style.width = pct + "%";
        };
        setIndicator("job_success", detail.job_success);
        setIndicator("recommendation", detail.recommendation);
        setIndicator("on_time", detail.on_time);
        setIndicator("on_budget", detail.on_budget);

        // Skills
        const skillsContainer = document.getElementById("skills-container");
        if (skillsContainer) {
            const skillsStr = me.skills || "";
            const skillsArray = skillsStr ? skillsStr.split(",").map(s => s.trim()).filter(Boolean) : [];
            if (skillsArray.length) {
                skillsContainer.innerHTML = skillsArray.map(s => `<span>${s}</span>`).join(" ");
            } else {
                skillsContainer.innerHTML = `
                    <div class="sidebar-empty-state">
                        <div class="sidebar-empty-icon">${EMPTY_ICONS.tag}</div>
                        <span>No skills added yet</span>
                        <a href="/dashboard/settings/">+ Add Skills</a>
                    </div>`;
            }
        }

        // Attachments (uploaded CV files and/or an external portfolio link)
        const attachmentsContainer = document.getElementById("attachments-container");
        if (attachmentsContainer) {
            const hasFiles = detail.files && detail.files.length;
            const portfolioUrl = (detail.portfolio_url || "").trim();

            if (hasFiles || portfolioUrl) {
                attachmentsContainer.innerHTML = "";

                if (portfolioUrl) {
                    const link = document.createElement("a");
                    link.href = portfolioUrl;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.className = "attachment-box ripple-effect";
                    link.innerHTML = `<span>Portfolio</span><i>LINK</i>`;
                    attachmentsContainer.appendChild(link);
                }

                (detail.files || []).forEach(file => {
                    const fileName = file.split("/").pop();
                    const fileExt = fileName.split(".").pop().toUpperCase();
                    const a = document.createElement("a");
                    a.href = file;
                    a.className = "attachment-box ripple-effect";
                    a.innerHTML = `<span>${fileName}</span><i>${fileExt}</i>`;
                    attachmentsContainer.appendChild(a);
                });
            } else {
                attachmentsContainer.innerHTML = `
                    <div class="sidebar-empty-state">
                        <div class="sidebar-empty-icon">${EMPTY_ICONS.paperclip}</div>
                        <span>No CV or portfolio added</span>
                        <a href="/dashboard/settings/">+ Add CV / Portfolio</a>
                    </div>`;
            }
        }

        // Reviews and work history
        await loadMyProfileReviews(profileId);
        await loadMyProfileWorkHistory(userId);

        // Company profile (employers only)
        if ((me.user?.role || "").toLowerCase() === "employer") {
            await loadCompanyProfile(userId);
        }

        updateUserNavInfo();

    } catch (error) {
        console.error("Error loading my profile:", error);
    }

    document.getElementById("mainBody").style.display = "block";
}

// Load and render the employer's company profile into #company-section.
async function loadCompanyProfile(userId) {
    const section = document.getElementById("company-section");
    const body = document.getElementById("company-section-body");
    if (!section || !body || !userId) return;

    const esc = (v) => {
        const d = document.createElement("div");
        d.textContent = v == null ? "" : String(v);
        return d.innerHTML;
    };

    try {
        const res = await fetch(`/api/companies/get/${userId}/`);

        if (res.status === 404) {
            section.style.display = "";
            body.innerHTML = `
                <div class="about-empty-state">
                    <div class="about-empty-state-icon">${EMPTY_ICONS.user}</div>
                    <h4>No Company Added Yet</h4>
                    <p>Register your company so clients know who they are working with.</p>
                    <a href="/dashboard/post-a-company/" class="button ripple-effect">Add Your Company</a>
                </div>`;
            return;
        }

        if (!res.ok) return;

        const c = await res.json();

        const logo = c.logo_url || "/static/images/company-logo-placeholder.png";
        const metaParts = [];
        if (c.industry) metaParts.push(esc(c.industry));
        if (c.company_country) metaParts.push(esc(c.company_country));
        if (c.company_size) metaParts.push(`${esc(c.company_size)} employees`);

        const rows = [];
        if (c.headquarters_address) rows.push(`<li><i class="icon-material-outline-location-on"></i> ${esc(c.headquarters_address)}</li>`);
        if (c.primary_phone) rows.push(`<li><i class="icon-material-outline-phone"></i> ${esc(c.primary_phone)}</li>`);
        if (c.email) rows.push(`<li><i class="icon-material-outline-email"></i> ${esc(c.email)}</li>`);
        if (c.website) {
            // Only render as a link for http(s) URLs; otherwise show as plain text
            // so a "javascript:" style value cannot become a clickable scheme.
            const safeUrl = /^https?:\/\//i.test(c.website);
            rows.push(safeUrl
                ? `<li><i class="icon-material-outline-public"></i> <a href="${esc(c.website)}" target="_blank" rel="noopener">${esc(c.website)}</a></li>`
                : `<li><i class="icon-material-outline-public"></i> ${esc(c.website)}</li>`);
        }

        body.innerHTML = `
            <div style="display:flex;gap:18px;align-items:center;margin-bottom:18px;">
                <img src="${esc(logo)}" alt=""
                     style="width:72px;height:72px;border-radius:8px;object-fit:cover;border:1px solid #e6e8ec;"
                     onerror="this.src='/static/images/company-logo-placeholder.png'">
                <div>
                    <h4 style="margin:0;font-size:18px;">${esc(c.company_name || c.brand_name || "")}</h4>
                    <span style="color:#808691;font-size:14px;">${metaParts.join(" &middot; ")}</span>
                </div>
            </div>
            ${c.description ? `<p style="margin:0 0 16px;">${esc(c.description)}</p>` : ""}
            ${rows.length ? `<ul class="company-contact-list" style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;color:#666;font-size:14px;">${rows.join("")}</ul>` : ""}
        `;
        section.style.display = "";
    } catch (error) {
        console.error("Error loading company profile:", error);
    }
}

document.addEventListener("DOMContentLoaded", loadMyProfile);
