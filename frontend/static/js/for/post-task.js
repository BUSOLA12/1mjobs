
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


document.querySelector(".button.ripple-effect.big").addEventListener("click", async function (e) {
  e.preventDefault();
  showLoading("Posting Task");

  // Get current user info
  const userInfo = await fetchUserId();
  if (!userInfo) {
    hideLoading();
    Snackbar.show({
      text: "Failed to fetch user info!",
      pos: "bottom-center",
      showAction: true,
      actionText: "Dismiss",
      duration: 3000,
      textColor: "#fff",
      backgroundColor: "#fa0404ff",
    });
    return;
  }

  // Get field values
  const projectName = document.querySelector("input[placeholder='e.g. build me a website']").value.trim();
  const category = document.querySelector("select[title='Select Category']").value.trim();
  const location = document.querySelector("#autocomplete-input").value.trim();
  const budgetMin = document.querySelector("input[placeholder='Minimum']").value.trim();
  const budgetMax = document.querySelector("input[placeholder='Maximum']").value.trim();
  const description = document.querySelector("textarea.with-border").value.trim();
  const expirationDate = document.querySelector('input[type="date"]').value.trim();
  const projectType = document.querySelector("#radio-1").checked ? "fixed" : "hourly";

  const skills = Array.from(document.querySelectorAll(".keywords-list .keyword-text"))
    .map(el => el.textContent.trim())
    .filter(skill => skill.length > 0);

  const files = document.querySelector("#upload").files;

  // ✅ Field-by-field validation with specific feedback
  if (!projectName) return showFieldError("Project name is required!");
  if (!category) return showFieldError("Please select a category!");
  if (!location) return showFieldError("Location is required!");
  if (!budgetMin) return showFieldError("Minimum budget is required!");
  if (!budgetMax) return showFieldError("Maximum budget is required!");
  if (!description) return showFieldError("Project description cannot be empty!");
  if (skills.length === 0) return showFieldError("Please add at least one skill!");
  if (!expirationDate) return showFieldError("Please select an expiration date!");

  // ✅ Build FormData
  const formData = new FormData();
  formData.append("user", userInfo.id);
  formData.append("project_name", projectName);
  formData.append("category", category);
  formData.append("location", location);
  formData.append("budget_min", budgetMin);
  formData.append("budget_max", budgetMax);
  formData.append("project_type", projectType);
  formData.append("skills", skills.join(", "));
  formData.append("description", description);
  formData.append("expiration_date", expirationDate);

  // Append files
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  // ✅ Submit the form
  try {
    const response = await fetchProtected("/api/tasks/create/", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      hideLoading();
      Snackbar.show({
        text: "Task creation failed!",
        pos: "bottom-center",
        showAction: true,
        actionText: "Dismiss",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#fa0404ff",
      });
      return;
    }

    const result = await response.json();
    hideLoading();
    Snackbar.show({
      text: "Task posted successfully!",
      pos: "bottom-center",
      showAction: true,
      actionText: "Dismiss",
      duration: 3000,
      textColor: "#fff",
      backgroundColor: "#04fa10ff",
    });

    console.log(result);
    window.location.href = `/task-page/${result.data.id}/`;

  } catch (error) {
    hideLoading();
    console.error("Error:", error);
    Snackbar.show({
      text: "Something went wrong!",
      pos: "bottom-center",
      showAction: true,
      actionText: "Dismiss",
      duration: 3000,
      textColor: "#fff",
      backgroundColor: "#fa0404ff",
    });
  }
});

// ✅ Helper for showing specific field error messages
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
