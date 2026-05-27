
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






document.addEventListener("DOMContentLoaded", async function () {
    const taskId = window.location.pathname.split("/").filter(Boolean).pop();
    showLoading("Loading");
    if (!taskId) {
        hideLoading();
        return;
    }
    // Pre-fill the form
    try {
        const res = await fetchProtected(`/api/tasks/detail/${taskId}/`)
        const task = await res.json()
        
        document.querySelector("input[placeholder='e.g. build me a website']").value = task.project_name;
        document.querySelector("#autocomplete-input").value = task.location;
        document.querySelector("input[placeholder='Minimum']").value = task.budget_min;
        document.querySelector("input[placeholder='Maximum']").value = task.budget_max;
        document.querySelector("textarea.with-border").value = task.description;
        document.querySelector('input[type="date"]').value = task.expiration_date;
        hideLoading();
    } catch (error) {
            console.error("Error fetching task for edit:", error);
            Snackbar.show({
          text: "Unable to load task data for editing.",
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fa0404ff",
        });
        }

    // Handle update submission
    document.querySelector("#update-task-btn").addEventListener("click", async function (e) {
        e.preventDefault();
        showLoading("Updating Task");
        const User = await fetchUserId();
        const user = User.id;

        // Create FormData to handle files
        const formData = new FormData();
        formData.append("user", user);
        if (document.querySelector("input[placeholder='e.g. build me a website']").value) {
        formData.append("project_name", document.querySelector("input[placeholder='e.g. build me a website']").value);
        }
        if (document.querySelector("select[title='Select Category']").value) {
        formData.append("category", document.querySelector("select[title='Select Category']").value);
        }
        if (document.querySelector("#autocomplete-input").value) {
        formData.append("location", document.querySelector("#autocomplete-input").value);
        }
        if (document.querySelector("input[placeholder='Minimum']").value) {
        formData.append("budget_min", document.querySelector("input[placeholder='Minimum']").value);
        }
        if (document.querySelector("input[placeholder='Maximum']").value) {
        formData.append("budget_max", document.querySelector("input[placeholder='Maximum']").value);
        }
        if (document.querySelector("#radio-1").checked) {
        formData.append("project_type", "fixed");
        }
        if (document.querySelector("#radio-2").checked) {
        formData.append("project_type", "hourly");
        }
        const skills = Array.from(document.querySelectorAll(".keywords-list .keyword-text"))
            .map(el => el.textContent.trim())
            .filter(skill => skill.length > 0)
        if (skills.length !== 0) {
        formData.append("skills", skills.join(", "));
        }
        if (document.querySelector("textarea.with-border").value) {
        formData.append("description", document.querySelector("textarea.with-border").value);
        }
        if (document.querySelector('input[type="date"]').value) {
        formData.append("expiration_date", document.querySelector('input[type="date"]').value);
        }
        // Handle multiple file uploads
        const files = document.querySelector("#upload").files;
        if (files) {
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }
    }

        try {
            const response = await fetchProtected(`/api/tasks/update/${taskId}/`, {
                method: "PUT",
                body: formData 
            });

            if (!response.ok) {
                Snackbar.show({
          text: "Update failed",
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fa0404ff",
        });
            }

            const updated = await response.json();
            hideLoading();
            Snackbar.show({
          text: "Task updated successfully!",
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#04fa39ff",
        });
            window.location.href = `/dashboard/manage-tasks/`;
        } catch (err) {
            console.error("Error updating Task:", err);
            Snackbar.show({
          text: "Error updating Task. Please check your input.",
          pos: "bottom-center",
          showAction: true,
          actionText: "Dismiss",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fa0404ff",
        });
        }
    });
});
