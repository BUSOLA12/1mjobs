
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



    
    document.addEventListener("DOMContentLoaded", function () {
        // const urlParams = new URLSearchParams(window.location.search);
        // const jobId = urlParams.get("job_id");
        // Use Django template variable to get job_id
        const jobId = window.location.pathname.split("/").filter(Boolean).pop();
        showLoading("Loading");
        if (!jobId) {
            hideLoading();
            return;
        }
    
        // Pre-fill the form with existing job data
        fetchProtected(`/api/jobs/detail/${jobId}/`)
            .then(res => res.json())
            .then(job => {
                document.querySelector("input[placeholder='Job Title']").value = job.title;
                document.querySelector("#autocomplete-input").value = job.location;
                document.querySelector("input[placeholder='Min']").value = job.salary_min;
                document.querySelector("input[placeholder='Max']").value = job.salary_max;
                document.querySelector("textarea").value = job.description;
                hideLoading();
            }
        
        )
            .catch(err => {
                console.error("Error fetching job for edit:", err);
                Snackbar.show({
                text: "Unable to load job data for editing.",
                pos: "bottom-center",
                showAction: true,
                actionText: "Dismiss",
                duration: 3000,
                textColor: "#fff",
                backgroundColor: "#fa0418ff",
                });
            });
    
        // Handle form submission for updating the job
        document.querySelector("#update-job-btn").addEventListener("click", async function (e) {
            e.preventDefault();
            showLoading("Updating Job");
            const User = await fetchUserId();
            const user = User.id;

            const formData = new FormData();
            formData.append("user", user);
            if (document.querySelector("input[placeholder='Job Title']").value) {
                formData.append('title', document.querySelector("input[placeholder='Job Title']").value);
            }
            if (document.querySelector("select[title='Select Job Type']").value) {
            formData.append('job_type', document.querySelector("select[title='Select Job Type']").value);
            }
            if (document.querySelector("select[title='Select Category']").value) {
            formData.append('category', document.querySelector("select[title='Select Category']").value);
            }
            if (document.querySelector("#autocomplete-input").value) {
            formData.append('location', document.querySelector("#autocomplete-input").value);
            }

            if (document.querySelector(".with-border.city").value) {
            formData.append('city', document.querySelector(".with-border.city").value);
            }
            if (document.querySelector("input[placeholder='Min']").value) {
            formData.append('salary_min', document.querySelector("input[placeholder='Min']").value);
            }
            if (document.querySelector("input[placeholder='Max']").value) {
            formData.append('salary_max', document.querySelector("input[placeholder='Max']").value);
            }
            const tags = Array.from(document.querySelectorAll(".keywords-list .keyword-text"))
            .map(el => el.textContent.trim())
            .filter(tag => tag.length > 0);

            // if (tags.length === 0) {
            //     alert("Please add at least one skill before submitting!");
            //     return; // stop form submission
            // }
            if (tags.length !== 0) {
            formData.append("tags", tags.join(", "));
            }
            if (document.querySelector("textarea").value) {
            formData.append('description', document.querySelector("textarea").value);
            }
            const files = document.querySelector("#upload").files;
            if (files) {
            for (let i = 0; i < files.length; i++) {
                formData.append("files", files[i]);
            }
            }
            if (document.querySelector('input[type="date"]').value) {
            formData.append("expiration_date", document.querySelector('input[type="date"]').value);
            }
    
            
    
            fetchProtected(`/api/jobs/update/${jobId}/`, {
                method: "PUT",
                body: formData,
            })
                .then(res => {
                    if (!res.ok) {
                        throw new Error("Update failed");
                    }
                    return res.json();
                })
                .then(updated => {
                    hideLoading();
                    Snackbar.show({
                    text: "Job updated successfully!",
                    pos: "bottom-center",
                    showAction: true,
                    actionText: "Dismiss",
                    duration: 3000,
                    textColor: "#fff",
                    backgroundColor: "#04fa62ff",
                    });
                    window.location.href = `/dashboard/manage-jobs/`; 
                })
                .catch(err => {
                    console.error("Error updating job:", err);
                    Snackbar.show({
                    text: "Error updating job. Please check your input.",
                    pos: "bottom-center",
                    showAction: true,
                    actionText: "Dismiss",
                    duration: 3000,
                    textColor: "#fff",
                    backgroundColor: "#04fa62ff",
                    });
                });
        });
    });
    