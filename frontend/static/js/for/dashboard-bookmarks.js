// ========== CONFIG ==========
const BASE_URL = "/api/bookmarks";

// ========== GET ALL BOOKMARKS ==========
async function getAllBookmarks() {
  try {
    const res = await fetchProtected(`${BASE_URL}/`, {
      method: "GET",
    });
    const data = await res.json();
    console.log("User Bookmarks:", data);
    return data;
  } catch (err) {
    console.error("Error Fetching Bookmarks:", err);
  }
}

  // Test creating different bookmarks
  // await createBookmark("job", 1);
  // await createBookmark("task", 2);
  // await createBookmark("userprofile", 3);



  // Function to dynamically render bookmarks
  async function renderBookmarks() {
    const data = await getAllBookmarks();

    const jobsContainer = document.querySelector(".bookmarked-jobs-list");
    const tasksContainer = document.querySelector(".bookmarked-tasks-list");
    const freelancersContainer = document.querySelector(".bookmarked-freelancers-list");

    // Render Bookmarked Jobs
    if (data.jobs.length !== 0) {
      jobsContainer.innerHTML = ""; // Clear previous content
      data.jobs.forEach((job) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <div class="job-listing">
            <div class="job-listing-details">
              <a href="/job-page/${job.job_id}/" class="job-listing-company-logo">
                <img src="${job.logo || 'https://placeholder.pics/svg/300'}}" alt="logo">
              </a>
              <div class="job-listing-description">
                <h3 class="job-listing-title"><a href="/job-page/${job.job_id}/">${job.title}</a></h3>
                <div class="job-listing-footer">
                  <ul>
                    <li><i class="icon-material-outline-business"></i> ${job.company || "N/A"}</li>
                    <li><i class="icon-material-outline-location-on"></i> ${job.location}</li>
                    <li><i class="icon-material-outline-business-center"></i> ${job.job_type}</li>
                    <li><i class="icon-material-outline-access-time"></i> ${timeSince(job.created_at)}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <div class="buttons-to-right">
            <a href="#" class="button red ripple-effect ico" title="Remove" data-tippy-placement="left" onclick="removeBookmark(this, ${job.id})">
              <i class="icon-feather-trash-2"></i>
            </a>
          </div>
        `;
        jobsContainer.appendChild(li);
      });
    }

    // Render Bookmarked Tasks
    if (data.tasks.length !== 0) {
      tasksContainer.innerHTML = ""; // Clear previous content
      data.tasks.forEach((task) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <div class="job-listing">
            <div class="job-listing-details">
              <a href="/task-page/${task.task_id}/" class="job-listing-company-logo">
                <img src="${task.logo || 'https://placeholder.pics/svg/300'}}" alt="logo">
              </a>
              <div class="job-listing-description">
                <h3 class="job-listing-title"><a href="/task-page/${task.task_id}/">${task.project_name}</a></h3>
                <div class="job-listing-footer">
                  <ul>
                    <li><i class="icon-material-outline-business"></i> ${task.company || "N/A"}</li>
                    <li><i class="icon-material-outline-location-on"></i> ${task.location}</li>
                    <li><i class="icon-material-outline-business-center"></i> ${task.project_type}</li>
                    <li><i class="icon-material-outline-access-time"></i> ${timeSince(task.created_at)}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <div class="buttons-to-right">
            <a href="#" class="button red ripple-effect ico" title="Remove" data-tippy-placement="left" onclick="removeBookmark(this, ${task.id})">
              <i class="icon-feather-trash-2"></i>
            </a>
          </div>
        `;
        tasksContainer.appendChild(li);
      });
    }

    // Render Bookmarked Freelancers (userprofiles)
    if (data.userprofiles.length !== 0) {
      freelancersContainer.innerHTML = ""; // Clear previous content
      data.userprofiles.forEach((user) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <div class="freelancer-overview">
            <div class="freelancer-overview-inner">
              <div class="freelancer-avatar">
                <div class="verified-badge"></div>
                <a href="/freelancer-profile/${user.profile_id}/"><img src="${user.avatar || '/static/images/user-avatar-placeholder.png'}" alt="" onerror="this.onerror=null;this.src='/static/images/user-avatar-placeholder.png';"></a>
              </div>
              <div class="freelancer-name">
                <h4><a href="/freelancer-profile/${user.profile_id}/">${user.full_name} <img class="flag" src="${user.country_flag || ""}" alt=""></a></h4>
                <span>${user.tagline}</span>
                <div class="freelancer-rating">
                  <div class="star-rating" data-rating="${user.rating}"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="buttons-to-right">
            <a href="#" class="button red ripple-effect ico" title="Remove" data-tippy-placement="left" onclick="removeBookmark(this, ${user.id})">
              <i class="icon-feather-trash-2"></i>
            </a>
          </div>
        `;
        freelancersContainer.appendChild(li);
      });

      starRating('.star-rating');
    }

    hideLoading();
  }

  function removeBookmark(element, id) {
    element.closest("li").remove();
    deleteBookmark(id);
  }

  // Run when page loads
  document.addEventListener("DOMContentLoaded", function () {
    renderBookmarks();
    updateUserNavInfo();

  });
