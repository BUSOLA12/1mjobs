	// Build the five star spans for a numeric rating using the theme's star classes.
	function buildStars(rating) {
		let html = '';
		for (let i = 1; i <= 5; i++) {
			if (rating >= i) html += '<span class="star"></span>';
			else if (rating >= i - 0.5) html += '<span class="star half"></span>';
			else html += '<span class="star empty"></span>';
		}
		return html;
	}

	// Render the employer's real aggregate rating (or "No ratings yet").
	function renderEmployerRating(rating) {
		const wrap = document.getElementById('employer-rating-wrap');
		const starsEl = document.getElementById('employer-rating');
		const textEl = document.getElementById('employer-rating-text');
		if (!wrap || !starsEl || !textEl) return;

		const count = rating && rating.count ? rating.count : 0;
		if (!count) {
			// Hide the star container so the theme's star-renderer can't leave a
			// stray glyph next to the "No ratings yet" label.
			starsEl.innerHTML = '';
			starsEl.style.display = 'none';
			textEl.textContent = 'No ratings yet';
		} else {
			const avg = rating.avg || 0;
			starsEl.style.display = '';
			starsEl.innerHTML = buildStars(avg);
			textEl.textContent = `${avg.toFixed(1)} (${count})`;
		}
		wrap.style.display = 'inline-block';
	}

	function updateCountdown(expirationDate) {
		const now = new Date();
		const diffMs = expirationDate - now;
		console.log("Difference in ms:", diffMs);
		console.log("Expiration Date:", expirationDate);
		console.log("Current Date:", now);
		const countdownDiv = document.getElementById("task-countdown");

		if (diffMs <= 0) {
        countdownDiv.textContent = "Expired";
        countdownDiv.classList.remove("green");
        countdownDiv.classList.add("red");
        return;
    }

		const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
		const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
		countdownDiv.textContent = `${days} days, ${hours} hours left`;


	}

async function getCountryFlag(countryName) {
  try {
    const response = await fetch(`https://restcountries.com/v3.1/name/${countryName}?fullText=true`);
    if (!response.ok) throw new Error("Country not found");
    
    const data = await response.json();
    const flagUrl = data[0].flags.png; // or .svg
    return flagUrl;
  } catch (error) {
    console.error("Error fetching flag:", error);
    return null;
  }
}

async function fetchcurrentuserDetails(userId) {
    try {
        const response = await fetchProtected(`/api/users/currentuser/${userId}/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user ID:', error);
        return null;
    }
}
	
async function setCountryFromOnline() {
  try {
    const response = await fetch("http://ip-api.com/json/");
    const data = await response.json();
    
    if (data.status === "success") {
      const countryName = data.country;
      const countryCode = data.countryCode.toLowerCase();
      console.log(`Country updated: ${countryName}`);
      return countryName;
    }
    throw new Error("Failed to get location");
  } catch (error) {
    console.error("Error fetching country info:", error);
    return null;
  }
}

function showLoading(message = null) {
    document.getElementById('loadingOverlay').classList.add('active');
    if (message !== null) {
      document.getElementById('my-pop-up').textContent = message;
    }
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

async function getCompanyDetails(empId) {

const res = await fetch(`/api/companies/get/${empId}/`);

if (res.ok) {
	data = await res.json();
	console.log("Company Details data:", data);
	return data;
} else {
	data = await res.json();
	Snackbar.show({
          text: data.error,
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fa0404ff",
        });
		return;
}
}

async function companyCreated(empId) {
  const res = await fetch(`/api/companies/exists/${empId}/`);
  if (res.ok) {
    const data = await res.json();
    return data.status;
  } else {
    const data = await res.json();
    throw new Error(data.error);
  }
}
	
	document.addEventListener("DOMContentLoaded", async function () {
		// const taskId = new URLSearchParams(window.location.search).get("id");
        const taskId = window.location.pathname.split("/").filter(Boolean).pop();
		showLoading("Loading Task Details");

		// Bookmark button handling
		const bookmarkButton = document.querySelector(".bookmark-button");
		initBookmarkButton(bookmarkButton, "task", taskId);



		countryName = await setCountryFromOnline();

		if (taskId) {

			try {
				const task_res = await fetch(`/api/tasks/detail/${taskId}/`)
			
				if (!task_res.ok) throw new Error("Task not found");
				const data = await task_res.json();
				
			
			
				console.log(data);

				const exist_data = await companyCreated(data.user);

				// Employer meta elements
				const compNameEl = document.getElementById("company-name");
				const countryLi = document.getElementById("country-li");
				const verifiedLi = document.getElementById("verified-li");
				const logoImg = document.getElementById("company-logo");
				const logoPlaceholder = document.getElementById("company-logo-placeholder");

				// Rating is the employer's (user) aggregate — show it even when
				// there is no company profile.
				renderEmployerRating(data.employer_rating);

				if (exist_data == true) {
					const comp_data = await getCompanyDetails(data.user);

					// Company name, with a neutral fallback
					compNameEl.textContent = comp_data.company_name || "Employer";

					// Logo, falling back to a placeholder icon
					if (comp_data.logo_url) {
						logoImg.src = comp_data.logo_url;
						logoImg.style.display = "";
						logoPlaceholder.style.display = "none";
					} else {
						logoImg.style.display = "none";
						logoPlaceholder.style.display = "";
					}

					// Country + flag, only when available
					if (comp_data.company_country) {
						countryLi.style.display = "";
						document.querySelector("#country-name").textContent = comp_data.company_country;
						getCountryFlag(comp_data.company_country).then(flagUrl => {
							const flagImg = document.querySelector(".flag");
							if (flagUrl) {
								flagImg.src = flagUrl;
								flagImg.style.display = "";
							} else {
								flagImg.style.display = "none";
							}
						});
					} else {
						countryLi.style.display = "none";
					}

					// Verified badge only if the company is verified
					verifiedLi.style.display = comp_data.verified ? "" : "none";
				} else {
					// No company registered — show empty states instead of blanks
					compNameEl.textContent = "Employer";
					logoImg.style.display = "none";
					logoPlaceholder.style.display = "";
					countryLi.style.display = "none";
					verifiedLi.style.display = "none";

					if (userInfo && userInfo.role == "freelancer") {
					Snackbar.show({
									text: "Cannot load company details. Please Contact Job Owner!",
									pos: "bottom-center",
									showAction: true,
									actionText: "Dismiss",
									duration: 3000,
									textColor: "#fff",
									backgroundColor: "#fa0404ff",
									});
					}

					else if (userInfo && userInfo.id === data.user) {
						Snackbar.show({
									text: "Cannot load company details. Please Post Your Company in Profiles settings page",
									pos: "bottom-center",
									showAction: true,
									actionText: "Dismiss",
									duration: 3000,
									textColor: "#fff",
									backgroundColor: "#fa0404ff",
									});
					} else {
						Snackbar.show({
									text: "Cannot load company details. Please Contact Job Owner!",
									pos: "bottom-center",
									showAction: true,
									actionText: "Dismiss",
									duration: 3000,
									textColor: "#fff",
									backgroundColor: "#fa0404ff",
									});
					}
				}


				document.querySelector(".project-name").textContent = data.project_name;
				//salary
				document.querySelector(".budget-amount").textContent = `₦${data.budget_min} - ₦${data.budget_max}`;

				// skills
				document.querySelector(".task-skills").textContent = data.skills;

				// Description
				document.querySelector(".task-description-text").textContent = data.description;
				
				const container = document.querySelector(".attachments-container");

				// Check if there’s a file
				if (data.files) {
					// Create the attachment box
					const attachment = document.createElement("a");
					attachment.href = "#";
					attachment.className = "attachment-box ripple-effect";
					attachment.dataset.fileUrl = data.files; // Store file URL in dataset
					attachment.innerHTML = `<span>${data.project_name} File</span><i>${data.files.split('.').pop().toUpperCase()}</i>`;

					// Add to container
					container.appendChild(attachment);

					// Add click listener for download
					attachment.addEventListener("click", function (e) {
					e.preventDefault();

					const fileUrl = this.dataset.fileUrl;

					if (!fileUrl) {
						Snackbar.show({
						text: "No file found to download!",
						pos: "bottom-center",
						showAction: true,
						actionText: "Dismiss",
						duration: 3000,
						textColor: "#fff",
						backgroundColor: "#fa0404ff",
						});
						return;
					}

					// Create a temporary hidden <a> tag for download
					const link = document.createElement("a");
					link.href = fileUrl;
					link.download = fileUrl.split("/").pop(); // Suggests a filename
					document.body.appendChild(link);
					link.click();
					document.body.removeChild(link);
					});
				} else {
					container.innerHTML = "<p>No attachments found.</p>";
				}

				const expirationDate = new Date(data.expiration_date);
				
				updateCountdown(expirationDate);
				
				hideLoading();


			
			} catch (error) {
				alert("Task could not be loaded.");
				console.error(error);
			}
		}
	});


	document.querySelector('#message-employer-btn').addEventListener('click', async function () {
		if (!await requireLogin()) return;
		try {
			const taskId = window.location.pathname.split("/").filter(Boolean).pop();


			const task_response = await fetchProtected(`/api/tasks/detail/${taskId}/`);
			const task_data = await task_response.json();
			const EmpId = task_data.user;
			console.log("Employer Id", EmpId);

			

			const response = await fetchProtected(`/api/users/currentuser/`);
			const User_data = await response.json();
			console.log(User_data);
			const UserId = User_data.id;

			const data = {
			participants: [UserId, EmpId],
			task_id: taskId
		};
		
		const createConvResponse = await fetchProtected(`/api/messaging/taskconversationcreate/`, {
			method: 'POST',
			body: JSON.stringify(data),
		});

		if (!createConvResponse.ok) {
			throw new Error('Failed to create conversation');
		};
		const createConvData = await createConvResponse.json();
		console.log(createConvData);
		convId = createConvData.id;
		window.location.href = `/dashboard/messages/?conv_id=${convId}&UserId=${UserId}&EmpId=${EmpId}`;
		} catch (error) {
        console.error('Error fetching user data:', error);
    }
});


document.querySelector("#snackbar-place-bid").addEventListener("click", async () => {
if (!await requireLogin()) return;

const taskId = window.location.pathname.split("/").filter(Boolean).pop();
showLoading("Placing Bidding");
minimal_rate = document.querySelector(".bidding-slider").value;
console.log("minimal_rate:",  minimal_rate);
day_number = document.querySelector("#day-number").value;
let delivery_time = day_number.toString();
time_type = document.querySelector(".bidding-field .selectpicker.default").value;
let time_chosen = delivery_time + " " + time_type;
console.log("time_chosen:", time_chosen);

const response = await fetchProtected(`/api/users/currentuser/`);
const User_data = await response.json();
console.log(User_data);
const UserId = User_data.id;

const data = {
	"bid_amount": minimal_rate,
	"delivery_time": time_chosen,
	"task": taskId,
	"freelancer": UserId
}

const bid_response = await fetchProtected(`/api/tasks/createbidding/`, {
	method: "POST",
	body: JSON.stringify(data),
});

if (bid_response.ok) {
	const bid_data = await bid_response.json();
	console.log("Bids data:", bid_data);
	hideLoading();
	Snackbar.show({
          text: 'Bidding Placed successfully!',
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#04fa2dff",
        });
		location.reload();

} else {
	const err_data = await bid_response.json();
	hideLoading();
	Snackbar.show({
	      text: err_data.error || "Could not place bid. Please try again.",
	      pos: "bottom-center",
	      showAction: true,
	      actionText: "Dismiss",
	      duration: 3000,
	      textColor: "#fff",
	      backgroundColor: "#e74c3c",
	    });
}



});

document.addEventListener("DOMContentLoaded", async () => {
	const taskId = window.location.pathname.split("/").filter(Boolean).pop();
	if (taskId) {
		
		//Get Task biddings
		const taskDiddingsRes = await fetch(`/api/tasks/task-bidings/${taskId}/`, {
			method: "GET"
		});
		const taskDiddings = await taskDiddingsRes.json();
		console.log("Task detail bids:", taskDiddings);
		const bidsContainer = document.querySelector(".boxed-list-ul");

		if (!bidsContainer) {
			hideLoading();
			alert("Container is null");
			return;
		}
		

		for (const bids of taskDiddings) {
			const info = bids.freelancer_info || {};

			// Real rating: theme widget (number badge + stars) when rated,
			// otherwise a "No ratings yet" label instead of a misleading 0.0.
			const r = parseFloat(info.rating) || 0;
			const ratingHtml = r > 0
				? `<div class="star-rating" data-rating="${r.toFixed(1)}"></div>`
				: `<span class="bid-no-rating">No ratings yet</span>`;

			// Real nationality flag, or nothing when unknown.
			let flagHtml = '';
			if (info.nationality) {
				try {
					const flagUrl = await getCountryFlag(info.nationality);
					if (flagUrl) {
						flagHtml = `<img class="flag" src="${flagUrl}" alt="" title="${info.nationality}" data-tippy-placement="top">`;
					}
				} catch (e) { /* ignore flag lookup failures */ }
			}

			const bidsItem = `
			<li>
					<div class="bid">
						<!-- Avatar -->
						<div class="bids-avatar">
							<div class="freelancer-avatar">
								<div class="verified-badge"></div>
								<a href="#"><img src="${info.avatar || '/static/images/user-avatar-placeholder.png'}" alt="" onerror="this.onerror=null;this.src='/static/images/user-avatar-placeholder.png';"></a>
							</div>
						</div>

						<!-- Content -->
						<div class="bids-content">
							<!-- Name -->
							<div class="freelancer-name">
								<h4><a href="#">${info.full_name} ${flagHtml}</a></h4>
								${ratingHtml}
							</div>
						</div>

						<!-- Bid -->
						<div class="bids-bid">
							<div class="bid-rate">
								<div class="rate">₦${bids.bid_amount}</div>
								<span>in ${bids.delivery_time}</span>
							</div>
						</div>
					</div>
				</li>
			`;

			bidsContainer.insertAdjacentHTML('beforeend', bidsItem);
		}

		// Scope to the bids list so this cannot wipe the employer rating above.
		$('.boxed-list-ul .star-rating').empty();
		starRating('.boxed-list-ul .star-rating');
	}
});

