async function setCountryFromOnline() {
  try {
    // 1. Fetch location data from IP API
    const response = await fetch("https://ipapi.co/json/");
    const data = await response.json();

    // 2. Extract country name and country code
    const countryName = data.country_name; // e.g. "Nigeria"
    const countryCode = data.country_code.toLowerCase(); // e.g. "ng"

	console.log(`Country updated: ${countryName}`);
    return countryName;
    

    
  } catch (error) {
    console.error("Error fetching country info:", error);
  }
}


async function getCompanyDetails(empId) {

const res = await fetch(`/api/companies/get/${empId}/`);

if (res.ok) {
	data = await res.json();
	console.log("Company Details data:", data);
	return data;
} else {
  data = await res.json();
  throw new Error(data.error);
	Snackbar.show({
          text: data.error,
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fa0404ff",
        });
        
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

// Fetch similar jobs from backend and populate HTML
async function fetchSimilarJobs(jobId) {
  try {
    // Fetch similar jobs from backend
    const response = await fetch(`/api/jobs/similar/${jobId}/`);
    
    
    if (!response.ok) {
      throw new Error("Failed to fetch similar jobs");
    }

    if (response.status === 204) {
        console.log("Backend returned 204 No Content. No jobs to display.");
        document.getElementById("similar-jobs").innerHTML = `<p>No similar jobs found.</p>`;
        return;
    }

    const jobs = await response.json();

	  console.log("Similar jobs data:", jobs);

    // Get container
    const container = document.getElementById("similar-jobs");
    container.innerHTML = ""; 
    // Show only first 3 similar jobs
    jobs.slice(0, 3).forEach((job) => {
      console.log("files url:", job.files);
      // Create job listing HTML
      const jobHTML = `
        <a href="/job-page/${job.id || ""}/" class="job-listing">
          <!-- Job Listing Details -->
          <div class="job-listing-details">
            <!-- Logo is here ooooooooooooo. It is here ooooooooo. Add it here oooooooo-->
             <div class="job-listing-company-logo" style="width: 50px; height: 50px; overflow: hidden;">
              <img src="${job.company_info !== null ? job.company_info.logo_url : ""}" style="max-width: 100%; height: 100%;" alt="">
            </div>

            <!-- Details -->
            <div class="job-listing-description">
              <h4 class="job-listing-company">
                <span>Web79</span>
                ${job.verified ? `<span class="verified-badge" title="Verified Employer" data-tippy-placement="top"></span>` : ""}
              </h4>
              <h3 class="job-listing-title">${job.title || ""}</h3>
            </div>
          </div>

          <!-- Job Listing Footer -->
          <div class="job-listing-footer">
            <ul>
              <li>
                <i class="icon-material-outline-location-on"></i>
                ${job.location || "Not specified"}
              </li>
              <li>
                <i class="icon-material-outline-business-center"></i>
                ${job.job_type || "N/A"}
              </li>
              <li>
                <i class="icon-material-outline-account-balance-wallet"></i>
                $${job.salary_min || ""} - $${job.salary_max || ""}
              </li>
              <li>
                <i class="icon-material-outline-access-time"></i>
                ${formatDate(job.created_at)}
              </li>
            </ul>
          </div>
        </a>
      `;

      // Append to container
      container.insertAdjacentHTML("beforeend", jobHTML);
    });
  } catch (error) {
    console.error("Error fetching similar jobs:", error);
    document.getElementById("similar-jobs").innerHTML = `<p>No similar jobs found.</p>`;
  }
}

// Helper: Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "1 day ago";
  return `${diffDays} days ago`;
}

// Call function on page load





	document.addEventListener("DOMContentLoaded", async function () {
		// const jobId = new URLSearchParams(window.location.search).get("id");
		const jobId = window.location.pathname.split("/").filter(Boolean).pop();
    showLoading();
    updateUserNavInfo();

    // handle Bookmark button
    const bookmarkButton = document.querySelector(".bookmark-button");

		bookmarkButton.setAttribute("data-job-id", jobId);
		if (bookmarkButton) {
			bookmarkButton.addEventListener("click", () => {
				console.log("Bookmark button got clicked")
				if (bookmarkButton.classList.contains("bookmarked")) {
					bookmarkHandling("delete", "job", bookmarkButton);

				} else {
					bookmarkHandling("create", "job", bookmarkButton);
				}
			});
		}
		
		countryName = await setCountryFromOnline();
		if (jobId) {
    		await fetchSimilarJobs(jobId);
 		}


		if (jobId) {
      try {

			  const response = await fetch(`/api/jobs/detail/${jobId}/`)
			
				if (!response.ok) {
          Snackbar.show({
          text: "Job not found",
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fc0707ff",
        });
        hideLoading();
        return;
        }
				const data = await response.json();
				
			
			
        console.log(data);
        const exist_data = await companyCreated(data.user);
        console.log("Exist status:", exist_data);

      //Check if company exist for the creator of the job
      if (exist_data == true) {
        const comp_data = await getCompanyDetails(data.user);
				console.log("Company data:", comp_data);
				
        document.querySelector(".header-image img").src = comp_data.logo_url;

				document.querySelector("#country-name").textContent = comp_data.company_country; 
				document.querySelector("#company-name").textContent = comp_data.company_name; 

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





        document.querySelector("h3").textContent = data.title;
        const container = document.querySelector(".attachments-container");

				// Check if there’s a file
				if (data.files) {
					// Create the attachment box
					const attachment = document.createElement("a");
					attachment.href = "#";
					attachment.className = "attachment-box ripple-effect";
					attachment.dataset.fileUrl = data.files; // Store file URL in dataset
					attachment.innerHTML = `<span>${data.title} File</span><i>${data.files.split('.').pop().toUpperCase()}</i>`;

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








				//salary
				document.querySelector(".salary-amount").textContent = `$${data.salary_min} - $${data.salary_max}`;
				document.querySelector(".job-overview li:nth-child(3) h5").textContent = `$${data.salary_min} - $${data.salary_max}`;

				// Location
				document.querySelector(".job-overview li:nth-child(1) h5").textContent = data.location;

				// Job Type
				document.querySelector(".job-overview li:nth-child(2) h5").textContent = data.job_type;

				// Description
				document.querySelector(".single-page-section p").textContent = data.description;

				// Date posted
				const datePosted = new Date(data.created_at).toLocaleDateString();
				document.querySelector(".job-overview li:nth-child(4) h5").textContent = datePosted;

        hideLoading();
      
		
      } catch (error) {
        Snackbar.show({
          text: `Job could not be loaded: ${error.message}`,
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fc0707ff",
        });
        hideLoading();
				console.error(error);
			}
		}
	});


	document.querySelector('#message-employer-btn').addEventListener('click', async function () {
    try {
        const jobId = window.location.pathname.split("/").filter(Boolean).pop();


		const job_response = await fetch(`/api/jobs/detail/${jobId}/`);
		const job_data = await job_response.json();
		const EmpId = job_data.user;
		console.log(EmpId);

        // Await the fetch request
        const response = await fetchProtected(`/api/users/currentuser/`);
        const User_data = await response.json();
        console.log(User_data);
		const UserId = User_data.id;

		
		const data = {
			participants: [UserId, EmpId],
			job_id: jobId
		};

		// Send the POST request to create a conversation
		const createConvResponse = await fetchProtected(`/api/messaging/jobconversationcreate/`, {
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



document.querySelector('#apply-now-button').addEventListener('click', async function() {
    try {
        const jobId = window.location.pathname.split("/").filter(Boolean).pop();
        showLoading("Sending Application");
        if (!userInfo) {
          Snackbar.show({
          text: "Failed to fetch user info!",
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fc0707ff",
        });
          hideLoading();
          return;
        }
		
		    
        const formData = new FormData();
        formData.append("user", userInfo.id);
        formData.append('job', jobId);
        formData.append('name', document.getElementById('name').value);
        formData.append('email', document.getElementById('emailaddress').value);
        const files = document.querySelector("#upload-cv").files;
        for (let i = 0; i < files.length; i++) {
          formData.append("files", files[i]);
        }

        const response = await fetchProtected('/api/jobs/application/', {
          method: 'POST',
          body: formData,
        });

        console.log('Response status:', response.status);
        if (response.ok) {
          const result = await response.json();
          console.log('Application submitted successfully:', result);
          
          
          Snackbar.show({
          text: 'Application submitted successfully!',
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#04fa2dff",
        });
          hideLoading();
          
        } else {
          const errorData = await response.json();
          console.error('Error submitting application:', errorData);
          //alert('Error submitting application. Please try again.');
          Snackbar.show({
          text: 'Error submitting application. Please try again.',
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#f70707ff",
        });
        hideLoading();
        }
      } catch (error) {
        console.error('Error preparing application data:', error);
        return;
      }
  });