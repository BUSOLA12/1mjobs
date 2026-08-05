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
  // Remove the skeleton placeholders from a list once loading is done.
  function clearSkeletons(container) {
    if (container) container.querySelectorAll(".bm-skeleton").forEach((el) => el.remove());
  }
  // Show the (hidden) empty-state row for a list that has no items.
  function showEmpty(container) {
    if (!container) return;
    const empty = container.querySelector(".bm-empty");
    if (empty) empty.style.display = "";
  }

  async function renderBookmarks() {
    let data = await getAllBookmarks();
    // On failure, fall back to empty so skeletons are replaced by empty states.
    if (!data) data = { jobs: [], tasks: [], userprofiles: [] };
    data.jobs = data.jobs || [];
    data.tasks = data.tasks || [];
    data.userprofiles = data.userprofiles || [];

    const jobsContainer = document.querySelector(".bookmarked-jobs-list");
    const tasksContainer = document.querySelector(".bookmarked-tasks-list");
    const freelancersContainer = document.querySelector(".bookmarked-freelancers-list");

    // Render Bookmarked Jobs
    clearSkeletons(jobsContainer);
    if (data.jobs.length === 0) {
      showEmpty(jobsContainer);
    } else {
      const emp = jobsContainer.querySelector(".bm-empty"); if (emp) emp.remove();
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
    clearSkeletons(tasksContainer);
    if (data.tasks.length === 0) {
      showEmpty(tasksContainer);
    } else {
      const emp = tasksContainer.querySelector(".bm-empty"); if (emp) emp.remove();
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
    clearSkeletons(freelancersContainer);
    if (data.userprofiles.length === 0) {
      showEmpty(freelancersContainer);
    } else {
      const emp = freelancersContainer.querySelector(".bm-empty"); if (emp) emp.remove();
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
