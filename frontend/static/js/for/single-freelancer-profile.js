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


async function loadUserReviews(userId) {
    const reviewsList = document.querySelector('#work-history-and-feedback-list');
    reviewsList.innerHTML = '<li><p>Loading reviews...</p></li>'; // Clear any existing content

    try {
        const reviews = await getReviewsReceived(userId);

        if (!reviews.length) {
            reviewsList.innerHTML = `<li><p>No reviews found.</p></li>`;
            return;
        }

        reviews.forEach(review => {
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
        document.querySelector(".header-image img").src = data.avatar;
        document.querySelector(".header-details h3").innerHTML = `
            ${data.full_name} <span>${data.tagline || ""}</span>
        `;

        // ===== 2. Rating =====
        const ratingElement = document.querySelector(".star-rating");
        if (ratingElement) {
            ratingElement.setAttribute("data-rating", data.rating || "0");
            $('.star-rating').empty();
            starRating('.star-rating');

        }

        // ===== 3. Nationality =====
        const nationalityLi = document.querySelector(".header-details ul li:nth-child(2)");
        if (nationalityLi) {
            // Assuming flag images are based on nationality name or ISO code
            nationalityLi.innerHTML = `<img class="flag" src="images/flags/${data.nationality.toLowerCase().slice(0, 2)}.svg" alt=""> ${data.nationality}`;
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

            const paragraphs = data.bio.split("\n");
            paragraphs.forEach(paragraph => {
                aboutSection.innerHTML += `
                    <p>${paragraph}</p>
                `;
            });
        }

        // ===== 6. Overview =====
        document.getElementById("hourly_rate").textContent = parseInt(data.hourly_rate) || 0;
        document.getElementById("jobs_done").textContent = data.job_success || 0;
        document.getElementById("rehired").textContent = data.rehired || 0;

        // ===== 7. Skills =====
        const skillsContainer = document.querySelector(".task-tags");
        if (skillsContainer) {
            skillsContainer.innerHTML = "";
            const skillsArray = data.skills ? data.skills.split(",").map(s => s.trim()) : [];
            skillsArray.forEach(skill => {
                // Join with a space ' ' to mimic the original HTML formatting
                skillsContainer.innerHTML = skillsArray
                .map(skill => `<span>${skill}</span>`)
                .join(' '); 
            });

            if (window.refreshKeywordsUI) {
                window.refreshKeywordsUI();
            }
        }

        // handle Bookmark button
        const bookmarkButton = document.querySelector(".bookmark-button");
        bookmarkButton.setAttribute("data-userprofile-id", profileId);
        if (bookmarkButton) {
            bookmarkButton.addEventListener("click", () => {
                if (bookmarkButton.classList.contains("bookmarked")) {
                    bookmarkHandling("create", "userprofile", bookmarkButton);

                } else {
                    bookmarkHandling("delete", "userprofile", bookmarkButton);
                }
            });
        }

        // ===== 8. Files / Attachments =====
        const attachmentsContainer = document.querySelector(".attachments-container");
        if (attachmentsContainer) {
            attachmentsContainer.innerHTML = "";
            if (data.files && data.files.length > 0) {
                data.files.forEach(file => {
                    const fileName = file.split("/").pop();
                    const fileExt = fileName.split(".").pop().toUpperCase();
                    const a = document.createElement("a");
                    a.href = file;
                    a.className = "attachment-box ripple-effect";
                    a.innerHTML = `<span>${fileName}</span><i>${fileExt}</i>`;
                    attachmentsContainer.appendChild(a);
                });
            } else {
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

    const formData = new FormData();
    formData.append("message", message);
    formData.append("receiver", profileUserId);

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
            appendError("Failed to send offer");
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

showLoading()
loadProfile(profileId);

document.addEventListener("DOMContentLoaded", function () {

    initiateFeatureCheck("make-an-offer-btn", "offers", () => {
        submitOffer("make-an-offer-form", "upload");
    });

});
