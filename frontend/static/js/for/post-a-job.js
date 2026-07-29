

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

	// Restrict the expiration date picker to future dates (tomorrow onward)
	const dateInput = document.querySelector('input[type="date"]');
	if (dateInput) {
		const tomorrow = new Date();
		tomorrow.setDate(tomorrow.getDate() + 1);
		dateInput.min = tomorrow.toISOString().split("T")[0];
	}

	// Allowed upload types and size cap (mirrors server-side validation)
	const ALLOWED_FILE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".doc", ".docx"];
	const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

	// Staged-file management: lets the user review and remove files before posting.
	// A FileList is read-only, so we mirror the selection in a DataTransfer and
	// re-assign it to the input whenever a file is added or removed.
	const uploadInput = document.querySelector("#upload");
	const stagedFilesList = document.querySelector("#staged-files");
	const stagedFiles = new DataTransfer();

	function humanFileSize(bytes) {
		if (bytes < 1024) return bytes + " B";
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
		return (bytes / (1024 * 1024)).toFixed(1) + " MB";
	}

	function renderStagedFiles() {
		if (!stagedFilesList) return;
		stagedFilesList.innerHTML = "";
		Array.from(stagedFiles.files).forEach((file, index) => {
			const li = document.createElement("li");

			const nameWrap = document.createElement("span");
			nameWrap.className = "staged-file-name";
			nameWrap.textContent = file.name; // textContent keeps filenames safe from markup
			const size = document.createElement("span");
			size.className = "staged-file-size";
			size.textContent = `(${humanFileSize(file.size)})`;
			nameWrap.appendChild(size);

			const removeBtn = document.createElement("button");
			removeBtn.type = "button";
			removeBtn.className = "remove-staged-file";
			removeBtn.setAttribute("aria-label", "Remove file");
			removeBtn.textContent = "×"; // ×
			removeBtn.addEventListener("click", () => removeStagedFile(index));

			li.appendChild(nameWrap);
			li.appendChild(removeBtn);
			stagedFilesList.appendChild(li);
		});
	}

	function removeStagedFile(indexToRemove) {
		const remaining = Array.from(stagedFiles.files).filter((_, i) => i !== indexToRemove);
		stagedFiles.items.clear();
		remaining.forEach(file => stagedFiles.items.add(file));
		if (uploadInput) uploadInput.files = stagedFiles.files;
		renderStagedFiles();
	}

	if (uploadInput) {
		uploadInput.addEventListener("change", function () {
			// Accumulate new picks; skip duplicates by name + size
			const existing = new Set(Array.from(stagedFiles.files).map(f => f.name + ":" + f.size));
			Array.from(this.files).forEach(file => {
				const key = file.name + ":" + file.size;
				if (!existing.has(key)) {
					stagedFiles.items.add(file);
					existing.add(key);
				}
			});
			this.files = stagedFiles.files;
			renderStagedFiles();
		});
	}

	// Reveal the "Feature this job" checkbox only for Pro employers. The
	// server enforces the quota regardless; this just avoids showing a control
	// free users can't use.
	(async function initFeatureToggle() {
		const wrap = document.getElementById("feature-job-wrap");
		if (!wrap) return;
		const me = await fetchUserId();
		if (me && me.is_pro) wrap.style.display = "";
	})();

	// Guard against rapid double-submit creating duplicate jobs
	let isSubmitting = false;

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
  const country = document.querySelector("select[title='Select Country']").value.trim();
  const salaryMin = document.querySelector("input[placeholder='Min']").value.trim();
  const salaryMax = document.querySelector("input[placeholder='Max']").value.trim();
  const description = document.querySelector("textarea").value.trim();
  const expirationDate = document.querySelector('input[type="date"]').value.trim();
  const files = document.querySelector("#upload").files;

  const rawTags = Array.from(document.querySelectorAll(".keywords-list .keyword-text"))
    .map(el => el.textContent.trim())
    .filter(tag => tag.length > 0);

  // De-duplicate tags case-insensitively while preserving order
  const seenTags = new Set();
  const tags = rawTags.filter(tag => {
    const key = tag.toLowerCase();
    if (seenTags.has(key)) return false;
    seenTags.add(key);
    return true;
  });

  // ✅ Field-by-field validation with specific messages
  if (!title) return showFieldError("Job title is required!");
  if (title.length > 255) return showFieldError("Job title cannot exceed 255 characters!");
  if (!jobType) return showFieldError("Please select a job type!");
  if (!category) return showFieldError("Please select a category!");
  if (!location) return showFieldError("Job location is required!");
  if (!salaryMin) return showFieldError("Minimum salary is required!");
  if (!salaryMax) return showFieldError("Maximum salary is required!");

  // ✅ Salary numeric, range and bound validation
  const salaryMinNum = parseFloat(salaryMin);
  const salaryMaxNum = parseFloat(salaryMax);
  if (isNaN(salaryMinNum)) return showFieldError("Minimum salary must be a number!");
  if (isNaN(salaryMaxNum)) return showFieldError("Maximum salary must be a number!");
  if (salaryMinNum < 0) return showFieldError("Minimum salary cannot be negative!");
  if (salaryMaxNum < 0) return showFieldError("Maximum salary cannot be negative!");
  if (salaryMaxNum > 99999999.99) return showFieldError("Salary cannot exceed 99,999,999.99!");
  if (salaryMinNum > salaryMaxNum) return showFieldError("Minimum salary cannot be greater than maximum salary!");
  if (!description) return showFieldError("Job description cannot be empty!");
  if (tags.length > 10) return showFieldError("You can add a maximum of 10 tags!");
  if (!expirationDate) return showFieldError("Please select an expiration date!");
  // Expiration must be a future calendar day (today resolves to midnight, already past)
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (new Date(expirationDate) <= today) return showFieldError("Expiration date must be in the future!");
  if (!city) return showFieldError("City is required!");
  if (!country) return showFieldError("Please select a country!");

  // ✅ Build form data
  const formData = new FormData();
  formData.append("user", userInfo.id);
  formData.append("title", title);
  formData.append("job_type", jobType);
  formData.append("category", category);
  formData.append("location", location);
  formData.append("salary_min", salaryMin);
  formData.append("salary_max", salaryMax);
  formData.append("tags", tags.join(", "));
  formData.append("description", description);
  formData.append("expiration_date", expirationDate);
  formData.append("city", city);
  formData.append("country", country);

  // Employer Pro perk: request a featured posting (server checks the quota).
  const featureCheckbox = document.getElementById("feature-job-checkbox");
  if (featureCheckbox && featureCheckbox.checked) {
    formData.append("featured", "true");
  }

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const dotIndex = file.name.lastIndexOf(".");
    const extension = dotIndex >= 0 ? file.name.slice(dotIndex).toLowerCase() : "";
    if (!ALLOWED_FILE_EXTENSIONS.includes(extension)) {
      return showFieldError(`File type "${extension || file.name}" is not allowed!`);
    }
    if (file.size > MAX_FILE_SIZE) {
      return showFieldError(`File "${file.name}" exceeds the 10 MB size limit!`);
    }
    formData.append("files", file);
  }

  // ✅ Prevent duplicate submissions from rapid clicks
  if (isSubmitting) return;
  isSubmitting = true;
  const postButton = document.querySelector(".button.ripple-effect.job-post");
  if (postButton) postButton.style.pointerEvents = "none";

  // ✅ Submit to backend
  fetchProtected("/api/jobs/create/", {
    method: "POST",
    body: formData,
  })
    .then(async response => {
      const result = await response.json();
      if (!response.ok) {
        // result is a DRF error object: { field: ["message", ...], ... }
        const firstKey = Object.keys(result)[0];
        const firstError = firstKey
          ? (Array.isArray(result[firstKey]) ? result[firstKey][0] : result[firstKey])
          : "Something went wrong!";
        throw new Error(firstError);
      }
      return result;
    })
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
        text: error.message || "Something went wrong!",
        pos: "bottom-center",
        showAction: true,
        actionText: "Dismiss",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#f80808ff",
      });
    })
    .finally(() => {
      isSubmitting = false;
      if (postButton) postButton.style.pointerEvents = "";
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