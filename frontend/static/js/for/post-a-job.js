

document.addEventListener('DOMContentLoaded', function() {
	async function fetchUserId() {
    try {
        const response = await fetchProtected(`/api/users/currentuser/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching user ID:', error);
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

	document.querySelector(".button.ripple-effect.job-post").addEventListener("click", async function (e) {
  e.preventDefault();
  console.log("I'm Here oooooo");
  showLoading("Posting Job");
  //console.log("I'm Here oooooo");
  const userInfo = await fetchUserId();
  //console.log("I'm Here oooooo");
  if (!userInfo) {
    hideLoading();
    Snackbar.show({
      text: "Failed to fetch user info!",
      pos: "bottom-center",
      showAction: true,
      actionText: "Dismiss",
      duration: 3000,
      textColor: "#fff",
      backgroundColor: "#fa0418ff",
    });
    return;
  }

  //console.log("I'm Here oooooo");
  // Get field values
  const title = document.querySelector("input[placeholder='Job Title']").value.trim();
  const jobType = document.querySelector("select[title='Select Job Type']").value.trim();
  const category = document.querySelector("select[title='Select Category']").value.trim();
  const location = document.querySelector("#autocomplete-input").value.trim();
  const city = document.querySelector(".with-border.city").value.trim();
  const salaryMin = document.querySelector("input[placeholder='Min']").value.trim();
  const salaryMax = document.querySelector("input[placeholder='Max']").value.trim();
  const description = document.querySelector("textarea").value.trim();
  const expirationDate = document.querySelector('input[type="date"]').value.trim();
  const files = document.querySelector("#upload").files;

  const tags = Array.from(document.querySelectorAll(".keywords-list .keyword-text"))
    .map(el => el.textContent.trim())
    .filter(tag => tag.length > 0);

  // ✅ Field-by-field validation with specific messages
  if (!title) return showFieldError("Job title is required!");
  if (!jobType) return showFieldError("Please select a job type!");
  if (!category) return showFieldError("Please select a category!");
  if (!location) return showFieldError("Job location is required!");
  if (!salaryMin) return showFieldError("Minimum salary is required!");
  if (!salaryMax) return showFieldError("Maximum salary is required!");
  if (!description) return showFieldError("Job description cannot be empty!");
  if (tags.length === 0) return showFieldError("Please add at least one skill!");
  if (!expirationDate) return showFieldError("Please select an expiration date!");
  if (!city) return showFieldError("City is required!");

  // ✅ Build form data
  const formData = new FormData();
  formData.append("user", userInfo.id);
  formData.append("title", title);
  formData.append("job_type", jobType.toLowerCase().replace(" ", "-"));
  formData.append("category", category);
  formData.append("location", location);
  formData.append("salary_min", salaryMin);
  formData.append("salary_max", salaryMax);
  formData.append("tags", tags.join(", "));
  formData.append("description", description);
  formData.append("expiration_date", expirationDate);
  formData.append("city", city);

  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  // ✅ Submit to backend
  fetchProtected("/api/jobs/create/", {
    method: "POST",
    body: formData,
  })
    .then(response => response.json())
    .then(result => {
      hideLoading();
      Snackbar.show({
        text: "Job posted successfully!",
        pos: "bottom-center",
        showAction: true,
        actionText: "Dismiss",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#08f81cff",
      });

      const Job_id = result.data.id;
      window.location.href = `/job-page/${Job_id}/`;
    })
    .catch(error => {
      hideLoading();
      console.error({ "Error": error });
      Snackbar.show({
        text: "Something went wrong!",
        pos: "bottom-center",
        showAction: true,
        actionText: "Dismiss",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#f80808ff",
      });
    });
});
 

// ✅ Helper function for showing specific field error
function showFieldError(message) {
  hideLoading();
  Snackbar.show({
    text: message,
    pos: "bottom-center",
    showAction: true,
    actionText: "Dismiss",
    duration: 3000,
    textColor: "#fff",
    backgroundColor: "#fa8c04ff",
  });
}
 });