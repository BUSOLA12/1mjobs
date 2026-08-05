// reviews_api.js

// Replace with your JWT token
const token = "YOUR_JWT_TOKEN_HERE";
const baseURL = "/api/reviews/";
const PAGE_SIZE = 5;

// Helper function parse page
function renderPagination(totalCount = 0, next = null, previous = null, current = 1, type = "pending") {
  let paginationUl = null;
  if (type === "pending") {
    paginationUl = document.querySelector("#pagination2 ul");
  } else {
    paginationUl = document.querySelector("#pagination1 ul");
  }
    
    paginationUl.innerHTML = "";

    const pageSize = PAGE_SIZE;
    const totalPages = Math.max(1, Math.ceil((totalCount || 0) / pageSize));
    const currentPageLocal = current || 1;

    // Prev arrow
    const prevLi = document.createElement("li");
    prevLi.className = "pagination-arrow";
    prevLi.innerHTML = `<a href="#" class="ripple-effect"><i class="icon-material-outline-keyboard-arrow-left"></i></a>`;
    if (previous) {
      prevLi.addEventListener("click", e => {
        e.preventDefault();
        // previous may be full url; parse page param if present
        const page = Math.max(1, currentPageLocal - 1);
        if (type === "pending") {
            getPendingReviews(page)
          } else {
            getMyReviews(page);
          }
      });
    } else {
      prevLi.classList.add("disabled");
    }
    paginationUl.appendChild(prevLi);

    // Show a window of pages around the current page (for long lists)
    const maxButtons = 7;
    let start = Math.max(1, currentPageLocal - Math.floor(maxButtons / 2));
    let end = Math.min(totalPages, start + maxButtons - 1);
    if (end - start < maxButtons - 1) start = Math.max(1, end - maxButtons + 1);

    for (let i = start; i <= end; i++) {
      const li = document.createElement("li");
      li.innerHTML = `<a href="#" class="ripple-effect ${i === currentPageLocal ? "current-page" : ""}">${i}</a>`;
      if (i === currentPageLocal) {
        // no click
      } else {
        li.addEventListener("click", e => {
          e.preventDefault();
          if (type === "pending") {
            getPendingReviews(i)
          } else {
            getMyReviews(i);
          }
        });
      }
      paginationUl.appendChild(li);
    }

    // Next arrow
    const nextLi = document.createElement("li");
    nextLi.className = "pagination-arrow";
    nextLi.innerHTML = `<a href="#" class="ripple-effect"><i class="icon-material-outline-keyboard-arrow-right"></i></a>`;
    if (next) {
      nextLi.addEventListener("click", e => {
        e.preventDefault();
        const page = Math.min(totalPages, currentPageLocal + 1);
        loadProfiles(page);
      });
    } else {
      nextLi.classList.add("disabled");
    }
    paginationUl.appendChild(nextLi);
  }


// 1. Create a review
async function createReview(payload) {
  console.log("Create Review was called...");
  try {
    const res = await fetchProtected(`${baseURL}create/`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    console.log("Create Review:", data);
    return 'ok';
  } catch (err) {
    console.error("Error creating review:", err);
  }
}

// 2. Update a review
async function updateReview(reviewId, payload) {

  try {
    const res = await fetchProtected(`${baseURL}${reviewId}/update/`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    console.log("Update Review:", data);
    return 'ok';
  } catch (err) {
    console.error("Error updating review:", err);
  }
}

// 4. Get reviews for a specific object (job/task)
async function getReviewsByObject(modelType, objectId) {
  try {
    const res = await fetch(`${baseURL}object/${modelType}/${objectId}/`, {
      headers: getHeaders()
    });
    const data = await res.json();
    console.log(`Reviews for ${modelType} ${objectId}:`, data);
    return data;
  } catch (err) {
    console.error("Error fetching reviews by object:", err);
  }
}

// 5. Get pending reviews for authenticated user
async function getPendingReviews(page = 1) {
  try {
    const res = await fetchProtected(`${baseURL}pending/?page_size=${PAGE_SIZE}&page=${page}`, {});
    const data = await res.json();
    console.log("Pending Reviews:", data);

    const results = data.results || data;
    renderPagination(data.count ?? results.length, data.next ?? null, data.previous ?? null, page);
    return results;
  } catch (err) {
    console.error("Error fetching pending reviews:", err);
  }
}

// 6. Get authenticated user’s submitted reviews
async function getMyReviews(page = 1) {
  try {
    const res = await fetchProtected(`${baseURL}mine/?page_size=${PAGE_SIZE}&page=${page}`, {});
    const data = await res.json();
    console.log("My Reviews:", data);

    const results = data.results || data;
    renderPagination(data.count ?? results.length, data.next ?? null, data.previous ?? null, page, "my-reviews");
    return results;
  } catch (err) {
    console.error("Error fetching my reviews:", err);
  }
}


// Function to create list items
// Remove skeleton rows and, when empty, reveal the empty-state message.
function clearReviewSkeletons(listContainer) {
  if (listContainer) listContainer.querySelectorAll('.rv-skeleton').forEach(el => el.remove());
}
function showReviewEmpty(listContainer) {
  if (!listContainer) return;
  const empty = listContainer.querySelector('.rv-empty');
  if (empty) empty.style.display = '';
}

function populatePendingReviews(pending) {
  const listContainer = document.querySelector('.dashboard-box-list.pending-reviews-list');

  clearReviewSkeletons(listContainer);
  if (!pending || pending.length === 0) {
      showReviewEmpty(listContainer);
      return;
  }
    listContainer.innerHTML = ''; // Clear existing list
    pending.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="boxed-list-item">
                <div class="item-content">
                    <h4>${item.title}</h4>
                    <span class="company-not-rated margin-bottom-5">Not Rated</span>
                </div>
            </div>
            <a href="#small-dialog-2" class="popup-with-zoom-anim button ripple-effect margin-top-5 margin-bottom-10">
                <i class="icon-material-outline-thumb-up"></i> Leave a Review
            </a>
        `;

        // Add click event to the button
        const button = li.querySelector('a');
        button.addEventListener('click', () => openReviewPopup(item));

        listContainer.appendChild(li);
    });
}


function populateOtherReviews(reviewList) {
  const listContainer = document.querySelector('.dashboard-box-list.reviews-list');
  clearReviewSkeletons(listContainer);
  if (!reviewList || reviewList.length === 0) {
      showReviewEmpty(listContainer);
      return;
  }
  listContainer.innerHTML = ''; // Clear existing list
  reviewList.forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = `
        <div class="boxed-list-item">
          <!-- Content -->
          <div class="item-content">
            <h4>${item.object_title}</h4>
            <div class="item-details margin-top-10">
              <div class="star-rating" data-rating="${item.rating}"></div>
              <div class="detail-item"><i class="icon-material-outline-date-range"></i> May 2019</div>
            </div>
            <div class="item-description">
              <p>${item.review_text}</p>
            </div>
          </div>
        </div>
        <a href="#small-dialog-1" class="popup-with-zoom-anim button gray ripple-effect margin-top-5 margin-bottom-10"><i class="icon-feather-edit"></i> Edit Review</a>
    `;

    // Add click event to the button
    const button = li.querySelector('a');
    button.addEventListener('click', () => openReviewPopup(item, 'change'));

    listContainer.appendChild(li);
  });
  $('.star-rating').empty();
  starRating('.star-rating');
}

// Global variable to keep track of the currently reviewed item
let currentReviewItem = null;

// Update the popup when opening
function openReviewPopup(item, operation='create') {
    currentReviewItem = item; // store the item for submission

    if (operation === 'create'){
      const popup = document.getElementById('small-dialog-2');
      const welcomeText = popup.querySelector('.welcome-text span');
      welcomeText.innerHTML = `Rate <a href="/freelancer-profile/${item.other_user_id}/">${item.other_user_name}</a> for the project <a href="${item.object_type == 'job' ? `/job-page/${item.object_id}/` : `/task-page/${item.object_id}/`}">${item.title}</a>`;
       
      const form = popup.querySelector('#leave-review-form');
      // Attach event listener to the form submit button
      form.addEventListener('submit', function(event) {
        submitReviewForm(event, 'create');
      });
      form.reset();
    } else {
      const popup = document.getElementById('small-dialog-1');
      const welcomeText = popup.querySelector('.welcome-text span');
      welcomeText.innerHTML = `Rate <a href="/freelancer-profile/${item.reviewee.id}/">${item.reviewee.name}</a> for the project <a href="${item.object_type == 'job' ? `/job-page/${item.object_id}/` : `/task-page/${item.object_id}/`}">${item.object_title}</a>`;
      
      const form = popup.querySelector('#change-review-form');
      form.innerHTML = `
          <div class="feedback-yes-no">
						<strong>Was this delivered on budget?</strong>
						<div class="radio">
							<input id="radio-rating-1" name="radio" type="radio" ${item.on_budget ? 'checked' : ''}>
							<label for="radio-rating-1"><span class="radio-label"></span> Yes</label>
						</div>

						<div class="radio">
							<input id="radio-rating-2" name="radio" type="radio" ${!item.on_budget ? 'checked' : ''}>
							<label for="radio-rating-2"><span class="radio-label"></span> No</label>
						</div>
					</div>

					<div class="feedback-yes-no">
						<strong>Was this delivered on time?</strong>
						<div class="radio">
							<input id="radio-rating-3" name="radio2" type="radio" ${item.on_time ? 'checked' : ''}>
							<label for="radio-rating-3"><span class="radio-label"></span> Yes</label>
						</div>

						<div class="radio">
							<input id="radio-rating-4" name="radio2" type="radio" ${!item.on_time ? 'checked' : ''}>
							<label for="radio-rating-4"><span class="radio-label"></span> No</label>
						</div>
					</div>

					<div class="feedback-yes-no">
						<strong>Your Rating</strong>
						<div class="leave-rating">
							<input type="radio" name="rating" id="rating-1" value="1"/>
							<label for="rating-1" class="icon-material-outline-star"></label>
							<input type="radio" name="rating" id="rating-2" value="2"/>
							<label for="rating-2" class="icon-material-outline-star"></label>
							<input type="radio" name="rating" id="rating-3" value="3"/>
							<label for="rating-3" class="icon-material-outline-star"></label>
							<input type="radio" name="rating" id="rating-4" value="4"/>
							<label for="rating-4" class="icon-material-outline-star"></label>
							<input type="radio" name="rating" id="rating-5" value="5"/>
							<label for="rating-5" class="icon-material-outline-star"></label>
						</div><div class="clearfix"></div>
					</div>

          <textarea class="with-border" placeholder="Comment" name="message" id="message" cols="7" required>${item.review_text}</textarea>
      `
      form.querySelector(`#rating-${item.rating}`).setAttribute('checked', true);

      // Attach event listener to the form submit button
      form.addEventListener('submit', function(event) {
        submitReviewForm(event, 'change');
      });
      form.reset();
    }
}

// Submit function
async function submitReviewForm(event, operation) {
  event.preventDefault();
  console.log('Submitting review...');
    if (!currentReviewItem) {
        console.error("No review item selected");
        return;
    }

    let form = null;
    if (operation === 'create') {
      form = document.getElementById('leave-review-form');
    } else {
      form = document.getElementById('change-review-form');
    }

    // Collect values
    const message = form.querySelector('[id*="message"]').value;
    let rating = form.querySelector('input[name="rating"]:checked')?.value;
    // const ratingEl = form.querySelectorAll('input[name="rating"]').forEach( el => {
    //   console.log(el);    });
    
    const onBudget = form.querySelector('input[name="radio"]:checked')?.value === 'on' ? true : false;
    const onTime = form.querySelector('input[name="radio2"]:checked')?.value === 'on' ? true : false;

    console.log('rating', rating)

    // Construct payload
    const payload = {
        model_type: currentReviewItem.object_type,
        object_id: currentReviewItem.object_id,
        rating: rating,
        review_text: message,
        on_budget: onBudget,
        on_time: onTime
    };

    console.log('payload', payload);


    let res = null;
    if (operation === 'create') {
      res = await createReview(payload);
    } else {
      res = await updateReview(currentReviewItem.id, payload);
    }
    

    if (res === 'ok') {
        // reload the page
        window.location.reload();
    }


    // console.log('Review submitted successfully!', data);
    
    // Optionally, close the popup
    currentReviewItem = null;
    form.reset();

}

(async () => {
  updateUserNavInfo();
  showLoading();

  // Update a review
  // await updateReview(1, 4, "Updated review text");

  // Get reviews received by user 2
//   await getReviewsReceived(2);

  // Get reviews for job 1
  // await getReviewsByObject("job", 1);

  // Get pending reviews for current user
  const pendingReviews = await getPendingReviews();
  populatePendingReviews(pendingReviews);


  // Get my submitted reviews
  const reviewList = await getMyReviews();
  populateOtherReviews(reviewList);

  hideLoading();
})();