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
    // Hide the star container so the theme's star-renderer can't leave a stray
    // glyph next to the "No ratings yet" label.
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
  const countryCode = getCountryCode(countryName);
  return countryCode ? `https://flagcdn.com/w20/${countryCode}.png` : null;
}

const FLAG_COUNTRY_CODES = [
  "ad", "ae", "af", "ag", "ai", "al", "am", "ao", "aq", "ar", "as", "at", "au", "aw", "ax", "az",
  "ba", "bb", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bl", "bm", "bn", "bo", "bq", "br", "bs",
  "bt", "bv", "bw", "by", "bz", "ca", "cc", "cd", "cf", "cg", "ch", "ci", "ck", "cl", "cm", "cn",
  "co", "cr", "cu", "cv", "cw", "cx", "cy", "cz", "de", "dj", "dk", "dm", "do", "dz", "ec", "ee",
  "eg", "eh", "er", "es", "et", "fi", "fj", "fk", "fm", "fo", "fr", "ga", "gb", "gd", "ge", "gf",
  "gg", "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr", "gs", "gt", "gu", "gw", "gy", "hk", "hm",
  "hn", "hr", "ht", "hu", "id", "ie", "il", "im", "in", "io", "iq", "ir", "is", "it", "je", "jm",
  "jo", "jp", "ke", "kg", "kh", "ki", "km", "kn", "kp", "kr", "kw", "ky", "kz", "la", "lb", "lc",
  "li", "lk", "lr", "ls", "lt", "lu", "lv", "ly", "ma", "mc", "md", "me", "mf", "mg", "mh", "mk",
  "ml", "mm", "mn", "mo", "mp", "mq", "mr", "ms", "mt", "mu", "mv", "mw", "mx", "my", "mz", "na",
  "nc", "ne", "nf", "ng", "ni", "nl", "no", "np", "nr", "nu", "nz", "om", "pa", "pe", "pf", "pg",
  "ph", "pk", "pl", "pm", "pn", "pr", "ps", "pt", "pw", "py", "qa", "re", "ro", "rs", "ru", "rw",
  "sa", "sb", "sc", "sd", "se", "sg", "sh", "si", "sj", "sk", "sl", "sm", "sn", "so", "sr", "ss",
  "st", "sv", "sx", "sy", "sz", "tc", "td", "tf", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to",
  "tr", "tt", "tv", "tw", "tz", "ua", "ug", "um", "us", "uy", "uz", "va", "vc", "ve", "vg", "vi",
  "vn", "vu", "wf", "ws", "xk", "ye", "yt", "za", "zm", "zw"
];

const COUNTRY_CODE_ALIASES = {
  "america": "us",
  "britain": "gb",
  "burma": "mm",
  "cape verde": "cv",
  "congo brazzaville": "cg",
  "congo kinshasa": "cd",
  "cote d ivoire": "ci",
  "czech republic": "cz",
  "czechia": "cz",
  "democratic republic of the congo": "cd",
  "dr congo": "cd",
  "england": "gb",
  "great britain": "gb",
  "ivory coast": "ci",
  "macedonia": "mk",
  "north korea": "kp",
  "north macedonia": "mk",
  "palestine": "ps",
  "republic of korea": "kr",
  "republic of the congo": "cg",
  "russia": "ru",
  "scotland": "gb",
  "south korea": "kr",
  "swaziland": "sz",
  "syria": "sy",
  "tanzania": "tz",
  "uae": "ae",
  "uk": "gb",
  "united kingdom": "gb",
  "united states": "us",
  "united states of america": "us",
  "us": "us",
  "usa": "us",
  "vietnam": "vn",
  "viet nam": "vn",
  "wales": "gb"
};

let regionDisplayNames = null;

function normalizeCountryName(countryName) {
  return String(countryName || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function getRegionDisplayNames() {
  if (regionDisplayNames !== null) return regionDisplayNames;

  regionDisplayNames = typeof Intl !== "undefined" && Intl.DisplayNames
    ? new Intl.DisplayNames(["en"], { type: "region" })
    : false;

  return regionDisplayNames;
}

function getCountryCode(countryName) {
  const normalizedCountryName = normalizeCountryName(countryName);
  if (!normalizedCountryName) return null;

  if (/^[a-z]{2}$/.test(normalizedCountryName) && FLAG_COUNTRY_CODES.includes(normalizedCountryName)) {
    return normalizedCountryName;
  }

  if (COUNTRY_CODE_ALIASES[normalizedCountryName]) {
    return COUNTRY_CODE_ALIASES[normalizedCountryName];
  }

  const displayNames = getRegionDisplayNames();
  if (!displayNames) return null;

  return FLAG_COUNTRY_CODES.find((countryCode) => {
    try {
      return normalizeCountryName(displayNames.of(countryCode.toUpperCase())) === normalizedCountryName;
    } catch (error) {
      return false;
    }
  }) || null;
}

function setCountryFlag(flagUrl, countryName) {
  const flagImg = document.getElementById("country-flag");
  const placeholder = document.getElementById("country-flag-placeholder");

  if (!flagImg || !placeholder) return;

  if (flagUrl) {
    flagImg.onerror = () => {
      flagImg.onerror = null;
      setCountryFlag(null, countryName);
    };
    flagImg.src = flagUrl;
    flagImg.alt = `${countryName} flag`;
    flagImg.style.display = "inline-block";
    placeholder.style.display = "none";
  } else {
    flagImg.onerror = null;
    flagImg.removeAttribute("src");
    flagImg.alt = "";
    flagImg.style.display = "none";
    placeholder.style.display = countryName ? "inline-block" : "none";
  }
}

function setCompanyLogo(logoUrl) {
  const logoImg = document.getElementById("company-logo");
  const placeholder = document.getElementById("company-logo-placeholder");

  if (!logoImg || !placeholder) return;

  if (logoUrl) {
    logoImg.src = logoUrl;
    logoImg.style.display = "block";
    placeholder.style.display = "none";
  } else {
    logoImg.removeAttribute("src");
    logoImg.style.display = "none";
    placeholder.style.display = "flex";
  }
}

let jobLocationMap = null;
let jobLocationMarker = null;
let jobLocationPanorama = null;
let googleMapsAuthFailed = false;

function normalizeLocationPart(value) {
  return String(value || "").trim();
}

function buildJobLocationAddress(job) {
  const parts = [job.location, job.city, job.country]
    .map(normalizeLocationPart)
    .filter(Boolean);

  return parts
    .filter((part, index) => {
      const normalizedPart = part.toLowerCase();
      return parts.findIndex((candidate) => candidate.toLowerCase() === normalizedPart) === index;
    })
    .join(", ");
}

function showLocationSnackbar(message) {
  if (window.Snackbar) {
    Snackbar.show({
      text: message,
      pos: "bottom-center",
      showAction: true,
      actionText: "Dismiss",
      duration: 3000,
      textColor: "#fff",
      backgroundColor: "#fa0404ff",
    });
    return;
  }

  console.warn(message);
}

function setStreetViewButtonState(enabled) {
  const streetViewButton = document.getElementById("streetView");
  if (!streetViewButton) return;

  streetViewButton.setAttribute("aria-disabled", enabled ? "false" : "true");
}

function googleMapsAvailable() {
  if (googleMapsAuthFailed) return false;

  return Boolean(
    window.google &&
    google.maps &&
    google.maps.Map &&
    google.maps.Geocoder &&
    google.maps.StreetViewService
  );
}

function geocodeJobAddress(address) {
  return new Promise((resolve, reject) => {
    const geocoder = new google.maps.Geocoder();

    geocoder.geocode({ address }, (results, status) => {
      if (status === "OK" && results && results[0]) {
        resolve(results[0]);
        return;
      }

      reject(new Error("Could not find this job location on Google Maps."));
    });
  });
}

function bindUnavailableStreetView(message) {
  const streetViewButton = document.getElementById("streetView");
  if (!streetViewButton) return;

  setStreetViewButtonState(false);
  streetViewButton.onclick = (event) => {
    event.preventDefault();
    showLocationSnackbar(message);
  };
}

async function initJobLocationMap(job) {
  const mapElement = document.getElementById("singleListingMap");
  const streetViewButton = document.getElementById("streetView");
  const address = buildJobLocationAddress(job);

  if (!mapElement || !streetViewButton) return;

  if (!address) {
    bindUnavailableStreetView("Job location is not available.");
    return;
  }

  if (googleMapsAuthFailed) {
    bindUnavailableStreetView("Google Maps API key is not authorized for this site URL.");
    return;
  }

  if (!googleMapsAvailable()) {
    bindUnavailableStreetView("Google Maps is not available right now.");
    return;
  }

  try {
    const geocodeResult = await geocodeJobAddress(address);
    const position = geocodeResult.geometry.location;

    mapElement.dataset.latitude = position.lat();
    mapElement.dataset.longitude = position.lng();

    jobLocationMap = new google.maps.Map(mapElement, {
      zoom: 15,
      center: position,
      scrollwheel: false,
      streetViewControl: true,
      mapTypeControl: false,
      fullscreenControl: true,
      gestureHandling: "cooperative",
    });

    jobLocationMarker = new google.maps.Marker({
      position,
      map: jobLocationMap,
      title: address,
    });

    jobLocationPanorama = jobLocationMap.getStreetView();
    const streetViewService = new google.maps.StreetViewService();

    setStreetViewButtonState(true);
    streetViewButton.onclick = (event) => {
      event.preventDefault();

      streetViewService.getPanorama(
        {
          location: position,
          radius: 1000,
          source: google.maps.StreetViewSource.OUTDOOR,
        },
        (panoramaData, status) => {
          if (status === "OK" && panoramaData && panoramaData.location && panoramaData.location.latLng) {
            jobLocationPanorama.setPosition(panoramaData.location.latLng);
            jobLocationPanorama.setPov({ heading: 0, pitch: 0 });
            jobLocationPanorama.setVisible(true);
            return;
          }

          showLocationSnackbar("Street View is not available for this job location.");
        }
      );
    };
  } catch (error) {
    console.error(error);
    bindUnavailableStreetView(error.message);
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
    if (!Array.isArray(jobs) || jobs.length === 0) {
      container.innerHTML = `<p>No similar jobs found.</p>`;
      return;
    }
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
                  <span>${job.company_info && job.company_info.company_name ? job.company_info.company_name : "Company"}</span>
                  ${job.company_info && job.company_info.verified ? `<span class="verified-badge" title="Verified Employer" data-tippy-placement="top"></span>` : ""}
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
                ₦${job.salary_min || ""} - ₦${job.salary_max || ""}
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





window.addEventListener("google-maps-auth-failure", () => {
  googleMapsAuthFailed = true;
  bindUnavailableStreetView("Google Maps API key is not authorized for this site URL.");
});

	document.addEventListener("DOMContentLoaded", async function () {
		// const jobId = new URLSearchParams(window.location.search).get("id");
		const jobId = window.location.pathname.split("/").filter(Boolean).pop();
    showLoading();
    updateUserNavInfo();

    // handle Bookmark button
    const bookmarkButton = document.querySelector(".bookmark-button");
    initBookmarkButton(bookmarkButton, "job", jobId);
		
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
				
        if (comp_data.company_country) {
            setCompanyLogo(comp_data.logo_url);
            document.querySelector("#country-name").textContent = comp_data.company_country; 
            document.querySelector("#company-name").textContent = comp_data.company_name; 
            const flagUrl = await getCountryFlag(comp_data.company_country);
            setCountryFlag(flagUrl, comp_data.company_country);
document.querySelector("#company-profile-link").href = `/single/company-profile/${data.user}/`;
             document.querySelector("#company-name-container").style.display = "block";
             renderEmployerRating(data.employer_rating);
             
             // Show verified badge only if company is verified
             const verifiedBadgeLi = document.querySelector("#company-name-container").parentElement.querySelector("li:last-child .verified-badge-with-title");
             if (comp_data.verified) {
                 verifiedBadgeLi.style.display = "block";
             } else {
                 verifiedBadgeLi.style.display = "none";
             }
         } else {
             document.querySelector("#company-name-container").style.display = "none";
         }

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

				// Build a downloadable attachment box (text set safely, no innerHTML)
				function addAttachment(fileUrl, label) {
					const attachment = document.createElement("a");
					attachment.href = "#";
					attachment.className = "attachment-box ripple-effect";
					attachment.dataset.fileUrl = fileUrl;

					const labelSpan = document.createElement("span");
					labelSpan.textContent = label;
					const extTag = document.createElement("i");
					extTag.textContent = fileUrl.split("?")[0].split(".").pop().toUpperCase();
					attachment.appendChild(labelSpan);
					attachment.appendChild(extTag);

					container.appendChild(attachment);

					attachment.addEventListener("click", function (e) {
						e.preventDefault();

						const url = this.dataset.fileUrl;
						if (!url) {
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

						const link = document.createElement("a");
						link.href = url;
						link.download = url.split("/").pop();
						document.body.appendChild(link);
						link.click();
						document.body.removeChild(link);
					});
				}

				// Prefer the multiple-file list; fall back to the legacy single file
				const uploadedFiles = Array.isArray(data.uploaded_files) ? data.uploaded_files : [];
				if (uploadedFiles.length > 0) {
					uploadedFiles.forEach((f, idx) => addAttachment(f.url, `${data.title} File ${idx + 1}`));
				} else if (data.files) {
					addAttachment(data.files, `${data.title} File`);
				} else {
					container.innerHTML = "<p>No attachments found.</p>";
				}








				//salary
				document.querySelector(".salary-amount").textContent = `₦${data.salary_min} - ₦${data.salary_max}`;
				document.querySelector(".job-overview li:nth-child(3) h5").textContent = `₦${data.salary_min} - ₦${data.salary_max}`;

				// Location
				document.querySelector(".job-overview li:nth-child(1) h5").textContent = data.location;
        initJobLocationMap(data);

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
    if (!await requireLogin()) return;
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

		window.location.href = `/dashboard/messages/?conv_id=${convId}&UserId=${UserId}&EmpId=${EmpId}`;

    } catch (error) {
        console.error('Error fetching user data:', error);
    }
});



document.querySelector('#apply-now-button').addEventListener('click', async function() {
    if (!await requireLogin()) return;
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
		
		    
        const proposal = document.getElementById('proposal').value.trim();
        const bidAmount = document.getElementById('bid_amount').value;
        if (!proposal) {
          Snackbar.show({
            text: "Please write a proposal before applying.",
            pos: "bottom-center", showAction: true, actionText: "Dismiss",
            duration: 3000, textColor: "#fff", backgroundColor: "#fc0707ff",
          });
          hideLoading();
          return;
        }

        const formData = new FormData();
        // The applicant's email is never collected here; the server derives it
        // from the logged-in account and keeps it hidden from the employer.
        formData.append('job', jobId);
        formData.append('name', document.getElementById('name').value);
        formData.append('proposal', proposal);
        formData.append('bid_amount', bidAmount);
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
