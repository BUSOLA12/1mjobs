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
		bookmarkButton.setAttribute("data-task-id", taskId);
		if (await isAuthenticated() && bookmarkButton) {
			bookmarkButton.addEventListener("click", () => {
				console.log("Bookmark button got clicked")
				if (bookmarkButton.classList.contains("bookmarked")) {
					bookmarkHandling("create", "task", bookmarkButton);

				} else {
					bookmarkHandling("delete", "task", bookmarkButton);
				}
			});
		}



		countryName = await setCountryFromOnline();

		if (taskId) {

			try {
				const task_res = await fetch(`/api/tasks/detail/${taskId}/`)
			
				if (!task_res.ok) throw new Error("Task not found");
				const data = await task_res.json();
				
			
			
				console.log(data);

				const exist_data = await companyCreated(data.user);

				if (exist_data == true) {
					const comp_data = await getCompanyDetails(data.user);
					
					
					document.querySelector(".header-image img").src = comp_data.logo_url;
					document.getElementById("company-name").textContent = comp_data.company_name;
					document.querySelector("#country-name").textContent = comp_data.company_country;

					const flagImg = document.querySelector(".flag");

					getCountryFlag(comp_data.company_country).then(flagUrl => {
					if (flagUrl) {
						flagImg.src = flagUrl;
					} else {
						flagImg.alt = "Flag not available";
					}
					});
				} else {
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
				document.querySelector(".budget-amount").textContent = `$${data.budget_min} - $${data.budget_max}`;

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
		window.location.href = `/dashboard/dashboard-messages/?conv_id=${convId}&UserId=${UserId}&EmpId=${EmpId}`;
		} catch (error) {
        console.error('Error fetching user data:', error);
    }
});


document.querySelector("#snackbar-place-bid").addEventListener("click", async () => {
if (!await isAuthenticated()) {
	appendError("You must be logged in to place a bid.");
	return;
}
	
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
			//const uD = await fetchcurrentuserDetails(bids.freelancer);
			//console.log("User details in bibbing:", uD);
			const bidsItem = `
			<li>
					<div class="bid">
						<!-- Avatar -->
						<div class="bids-avatar">
							<div class="freelancer-avatar">
								<div class="verified-badge"></div>
								<a href="#"><img src="${bids.freelancer_info.avatar}" alt=""></a>
							</div>
						</div>
						
						<!-- Content -->
						<div class="bids-content">
							<!-- Name -->
							<div class="freelancer-name">
								<h4><a href="#">${bids.freelancer_info.full_name} <img class="flag" src="images/flags/gb.svg" alt="" title="United Kingdom" data-tippy-placement="top"></a></h4>
								<div class="star-rating" data-rating="${bids.freelancer_info.rating}"></div>
							</div>
						</div>
						
						<!-- Bid -->
						<div class="bids-bid">
							<div class="bid-rate">
								<div class="rate">$${bids.bid_amount}</div>
								<span>in ${bids.delivery_time}</span>
							</div>
						</div>
					</div>
				</li>
			`;

			bidsContainer.insertAdjacentHTML('beforeend', bidsItem);
		}

		$('.star-rating').empty();
        starRating('.star-rating');
	}
});

