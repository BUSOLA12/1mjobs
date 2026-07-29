function bindCloseButtons(container) {
    container.querySelectorAll('a.close').forEach(btn => {
        btn.removeAttribute('href');
        btn.addEventListener('click', function () {
            const notification = this.parentElement;
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => notification.remove(), 500);
        });
    });
}

let noError = true;
// Set from the /api/users/me/ load; used to route employers into company onboarding.
let currentUserId = null;
let errorStateList = {
  errors: [],
  success: [],
  addError: function (error) {
    this.errors.push(error);
    noError = false;
  },
  addSuccess: function (message) {
    this.success.push(message);
  }
};

function appendSuccess(message) {
  const errorContainer = document.getElementById('login-error');
  const successDiv = document.createElement('div');
  successDiv.innerHTML = `
    <div class="notification success closeable">
        <p>${message}</p>
        <a class="close" href="#"></a>
    </div>`;
  errorContainer.appendChild(successDiv);
}

// function to handle the getting of skills into comma-separated string
function getSkillListAsString() {
    const keywords = document.querySelectorAll('.keyword-text');
    if (keywords.length === 0) {
      return [];
    }
    const skills = Array.from(keywords).map(el => el.textContent.trim());
    return skills;
  }

  // Function to append new skills from a comma-separated string
function appendSkills(skillsString) {
    const skillList = document.querySelector('.keywords-list');
    const skills = skillsString.split(',').map(skill => skill.trim()).filter(skill => skill !== '');

    skills.forEach(skill => {
        const span = document.createElement('span');
        span.className = 'keyword';
        span.innerHTML = `
        <span class="keyword-remove"></span>
        <span class="keyword-text">${skill}</span>
        `;
        skillList.appendChild(span);
    });

    if (window.refreshKeywordsUI) {
        window.refreshKeywordsUI();
    }
}

  // Example usage:
//   const newSkills = "React, Node.js, Python";
//   appendSkills(newSkills);

async function handleImageUpload(endpointUrl) {
  const fileInput = document.querySelector('.file-upload');

    
  const file = fileInput.files[0];
  if (!file){
    console.log("No file selected for upload.");
    return;
  }
  const formData = new FormData();
  formData.append('avatar', file);

  try {
    const response = await fetchProtected(endpointUrl, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      errorStateList.addError('Image upload failed.');
      throw new Error(errorData || 'Upload failed');
    }

    const result = await response.json();
    errorStateList.addSuccess('Image uploaded successfully.');
    console.log('Image upload response:', result);
  } catch (error) {
    console.error('Image upload failed:', error);
  }
    
}

  // Call it like this:
//   handleImageUpload('/api/upload-avatar/');


async function submitPasswordUpdate(endpointUrl) {
  try {
  const [currentPasswordInput, newPasswordInput, repeatPasswordInput] =
    document.querySelectorAll('input[type="password"]');

  const currentPassword = currentPasswordInput.value.trim();
  const newPassword = newPasswordInput.value.trim();
  const repeatPassword = repeatPasswordInput.value.trim();

  // Ensure all password fields are filled
  if (!currentPassword || !newPassword || !repeatPassword) {

    let error = 'All password fields are required.';
    errorStateList.addError(error);
    
    console.log("Password was not changed");
    throw new Error(error);
  }

  // Ensure the new passwords match
  if (newPassword !== repeatPassword) {;
    let error = 'New password and confirmation do not match.';
    errorStateList.addError(error);
    
    throw new Error(error);
  }

  const data = {
    old_password: currentPassword,
    new_password: newPassword,
  };

  // update password via fetchProtected
  let res = await fetchProtected(endpointUrl, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })

  if (!res.ok) {
    const errorData = await res.json();
    let error = 'current password is incorrect.';
    errorStateList.addError(error);
    throw new Error(errorData);
  }

  let result = await res.json();
  errorStateList.addSuccess('Password updated successfully.');
  console.log('Password update response:', result);
  } catch (error) {
    noError = false;
    console.error('Error updating password:', error);
  }
}





async function submitProfileExtras(endpointUrl) {
  try {
    // Get the bidding amount (from data attribute or value)
    const biddingVal = document.getElementById("biddingVal");
    const hourlyRateValue = biddingVal.innerHTML;

    // Get the tagline
    const tagline = document.getElementById('tagline').value.trim();

    // Get the bio
    const bio = document.getElementById('bio-intro').value.trim();

    // Get selected nationality (only save if a real country option is selected)
    const select = document.getElementById('nationalityInput');
    const selectedOption = select.selectedIndex >= 0 ? select.options[select.selectedIndex] : null;
    const selectedCountry = (selectedOption && selectedOption.value) ? selectedOption.textContent.trim() : '';
    // Get user data
    const firstName = document.querySelector('#first-name').value;
    const lastName = document.querySelector('#last-name').value;
    const email = document.querySelector('#email').value;
    const accountType = document.querySelector('input[name="account-type-radio"]:checked').id.includes('freelancer') ? 'freelancer' : 'employer';

    // Two-factor authentication is managed by its own confirm/disable flow
    // (see the #two-step handler below), so it is intentionally not sent here.
    const userData = {
        first_name: firstName,
        last_name: lastName,
        email: email,
        role: accountType
    };

    // Get the address
    const addressEl = document.getElementById('autocomplete-input');
    const address = addressEl ? addressEl.value.trim() : '';

    // Get the portfolio link (optional alternative to an uploaded CV)
    const portfolioEl = document.getElementById('portfolio-url');
    const portfolioUrl = portfolioEl ? portfolioEl.value.trim() : '';

    // Construct JSON data
    let data = {
      hourly_rate: hourlyRateValue,
      tagline: tagline,
      nationality: selectedCountry,
      address: address,
      bio: bio,
      portfolio_url: portfolioUrl,
      user: userData
    };

    const skills = getSkillListAsString();

    if (skills.length > 0){
      data['skills'] = skills;
    }

    // Send to endpoint using fetchProtected
    let res = await fetchProtected(endpointUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })

    if (!res.ok) {
      const errorData = await res.json();
      errorStateList.addError('Profile update failed.');
      throw new Error(errorData || 'Profile update failed');
    }

    let result = await res.json();
    console.log("Data submitted successfully:", result);
    errorStateList.addSuccess('Profile updated successfully.');
  } catch (error) {
    noError = false;
    console.error("Error submitting profile extras:",error);
  }
}


async function loadAttachments() {
    const container = document.querySelector('.attachments-container');
    if (!container) return;

    try {
      const res = await fetchProtected('/api/users/profile/files/', {
        headers: {
          'Accept': 'application/json',
        },

      });

      if (!res.ok) throw new Error('Failed to fetch files');

      const files = await res.json();
      container.innerHTML = ''; // clear existing nodes

      files.forEach(f => {
        const box = document.createElement('div');
        box.className = 'attachment-box ripple-effect';
        box.innerHTML = `
          <span>${escapeHtml(f.name)}</span>
          <i>${escapeHtml(f.extension).toUpperCase()}</i>
          <button class="remove-attachment old-attachment" data-id="${f.id}" data-tippy-placement="top" title="Remove"></button>
        `;

        box.addEventListener('click', onRemoveAttachment, { once: true });
        container.appendChild(box);
      });
    } catch (e) {
      console.error(e);
    }
  }

  async function onRemoveAttachment(e) {
    const btn = e.target.closest('.remove-attachment.old-attachment');
    if (!btn) return;
    const id = btn.dataset.id;
    try {
      const res = await fetchProtected(`/api/users/profile/files/${id}/`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (res.status === 204 || res.ok) {
        console.log('File deleted successfully');
       btn.closest('.attachment-box').remove();
      } else {
        console.error('Delete failed', err);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }


  async function submitFiles() {
    const input = document.getElementById('upload');

    if (!input.files || input.files.length === 0) {
      console.log('No files to upload.');
      return;
    }

    const fd = new FormData();
    // IMPORTANT: backend expects `files` as a **list** field
    Array.from(input.files).forEach(file => fd.append('files', file));


    try {
      const res = await fetchProtected('/api/users/profile/files/upload/', {
        method: 'POST',
        body: fd,
        headers: {

        },
        
      });

      if (!res.ok) {
        const text = await res.text();
        errorStateList.addError('File upload failed.');
        throw new Error(text || 'Upload failed');
      }

      const uploaded = await res.json();
      errorStateList.addSuccess('Files uploaded successfully.');
      console.log('Uploaded:', uploaded);

      // Optional: clear the input + UI after successful upload
      clearFileInput(input);

      console.log('Uploaded successfully!');
    } catch (err) {
      console.error('File upload error:', err);
    }
  }

  function clearFileInput(inputEl) {
    // Replace with a fresh, empty DataTransfer
    const dt = new DataTransfer();
    inputEl.files = dt.files;
    renderStagedFiles();
  }

  // Render the files the user has selected but not yet uploaded ("staged"),
  // each with a remove control so they can drop one before hitting Save.
  function renderStagedFiles() {
    const container = document.querySelector('.attachments-container');
    const input = document.getElementById('upload');
    if (!container || !input) return;

    // Clear only the staged chips; leave already-uploaded attachments intact.
    container.querySelectorAll('.attachment-box.staged-attachment').forEach(el => el.remove());

    Array.from(input.files || []).forEach((file, index) => {
      const ext = (file.name.split('.').pop() || '').toUpperCase();
      const box = document.createElement('div');
      box.className = 'attachment-box staged-attachment';
      box.innerHTML = `
        <span>${escapeHtml(file.name)}</span>
        <i>${escapeHtml(ext)}</i>
        <button class="remove-attachment staged" data-index="${index}" data-tippy-placement="top" title="Remove"></button>
      `;
      box.querySelector('.remove-attachment.staged').addEventListener('click', onRemoveStagedFile);
      container.appendChild(box);
    });

    syncStagedFileName();
  }

  function onRemoveStagedFile(e) {
    const btn = e.target.closest('.remove-attachment.staged');
    if (!btn) return;
    const removeIndex = Number(btn.dataset.index);
    const input = document.getElementById('upload');
    if (!input) return;

    // FileList is read-only, so rebuild it via DataTransfer minus the removed file.
    const dt = new DataTransfer();
    Array.from(input.files).forEach((file, index) => {
      if (index !== removeIndex) dt.items.add(file);
    });
    input.files = dt.files;

    renderStagedFiles();
  }

  // Keep the upload button caption in sync with the remaining staged files.
  function syncStagedFileName() {
    const nameField = document.querySelector('.uploadButton-file-name');
    const input = document.getElementById('upload');
    if (!nameField || !input) return;

    const files = Array.from(input.files || []);
    nameField.innerHTML = files.length
      ? files.map(f => escapeHtml(f.name)).join('<br>')
      : 'Maximum file size: 10 MB';
  }

function appendAccountType(data) {
    // Determine which role should be checked
    const isFreelancer = data.user?.role === 'freelancer';
    const isEmployer = data.user?.role === 'employer';

    // Create the Freelancer radio
    const freelancerDiv = document.createElement("div");
    freelancerDiv.innerHTML = `
        <input type="radio" name="account-type-radio" id="freelancer-radio" class="account-type-radio" ${isFreelancer ? 'checked' : ''}/> 
        <label for="freelancer-radio"><i class="icon-material-outline-account-circle"></i> Freelancer</label>
    `;

    // Create the Employer radio
    const employerDiv = document.createElement("div");
    employerDiv.innerHTML = `
        <input type="radio" name="account-type-radio" id="employer-radio" class="account-type-radio" ${isEmployer ? 'checked' : ''}/>
        <label for="employer-radio"><i class="icon-material-outline-business-center"></i> Employer</label>
    `;

    // Append to wrapper
    const wrapper = document.getElementById("account-type");
    wrapper.innerHTML = "";
    wrapper.appendChild(freelancerDiv);
    wrapper.appendChild(employerDiv);
}

function appendBiddingWidget(data) {// Bidding value display
    const biddingValueDiv = document.getElementById("biddingVal");
    biddingValueDiv.innerHTML = data.hourly_rate || 0;
}

// ---- Onboarding completion bar ----
function photoIsSet() {
    const fileInput = document.querySelector('.file-upload');
    if (fileInput && fileInput.files && fileInput.files.length > 0) return true;
    const img = document.getElementById('user-avatar');
    return !!(img && img.src && img.src.indexOf('placeholder') === -1);
}

function isFreelancerSelected() {
    const r = document.querySelector('input[name="account-type-radio"]:checked');
    return r ? r.id.includes('freelancer') : true;
}

function nationalityIsSet() {
    const s = document.getElementById('nationalityInput');
    const opt = (s && s.selectedIndex >= 0) ? s.options[s.selectedIndex] : null;
    return !!(opt && opt.value);
}

function hourlyRateIsSet() {
    const raw = document.getElementById('biddingVal')?.innerHTML || '';
    const n = parseFloat(String(raw).replace(/[^\d.]/g, ''));
    return !isNaN(n) && n > 0;
}

function skillsAreSet() {
    return (typeof getSkillListAsString === 'function') && getSkillListAsString().length > 0;
}

// Required-field list for the settings-page progress bar. This MUST mirror the
// server-side check in users/models.py -> UserProfile.recompute_onboarding(),
// which is what the OnboardingRedirectMiddleware actually enforces. Keep the two
// in sync when changing what is required (same role-aware rule: employers need
// only the common fields; freelancers also need tagline/bio/hourly_rate/skills).
function getOnboardingReqs() {
    const val = (id) => (document.getElementById(id)?.value || '').trim() !== '';
    const reqs = {
        first_name: val('first-name'),
        last_name: val('last-name'),
        photo: photoIsSet(),
        address: val('autocomplete-input'),
        nationality: nationalityIsSet(),
    };
    // Freelancers must also complete their marketable profile.
    if (isFreelancerSelected()) {
        reqs.tagline = val('tagline');
        reqs.bio = val('bio-intro');
        reqs.hourly_rate = hourlyRateIsSet();
        reqs.skills = skillsAreSet();
    }
    return reqs;
}

const ONBOARDING_LABELS = {
    first_name: 'First name', last_name: 'Last name', photo: 'Profile photo',
    address: 'Address', nationality: 'Nationality', tagline: 'Tagline',
    bio: 'Bio', hourly_rate: 'Hourly rate', skills: 'Skills',
};

function isOnboardingComplete() {
    const reqs = getOnboardingReqs();
    return Object.keys(reqs).every(k => reqs[k]);
}

// Does this user already own a company? Used to decide whether an employer
// must still go through company onboarding.
async function companyExists(userId) {
    if (!userId) return false;
    try {
        const res = await fetchProtected(`/api/companies/exists/${userId}/`);
        if (!res.ok) return false;
        const data = await res.json();
        return !!(data && data.status === true);
    } catch (e) {
        console.error("Company existence check failed:", e);
        return false;
    }
}

function updateOnboardingProgress() {
    const wrap = document.getElementById('onboarding-progress');
    if (!wrap) return; // not shown once profile is complete

    const reqs = getOnboardingReqs();
    const keys = Object.keys(reqs);
    const done = keys.filter(k => reqs[k]).length;
    const pct = Math.round((done / keys.length) * 100);

    document.getElementById('onboarding-bar').style.width = pct + '%';
    document.getElementById('onboarding-percent').textContent = pct + '%';

    // Rebuild the checklist from the (role-aware) requirements so newly-added
    // fields always appear.
    const list = document.getElementById('onboarding-checklist');
    if (list) {
        list.innerHTML = keys.map(k => {
            const ok = reqs[k];
            return `<li data-req="${k}" style="display:flex;align-items:center;gap:8px;font-size:14px;color:${ok ? '#1f9d55' : '#999'};">
                <span class="ob-icon" style="font-weight:700;color:${ok ? '#1f9d55' : '#bbb'};">${ok ? '&#10003;' : '&#9675;'}</span> ${ONBOARDING_LABELS[k] || k}
            </li>`;
        }).join('');
    }
}
// expose so the Google autocomplete callback in the template can refresh it
window.updateOnboardingProgress = updateOnboardingProgress;

// Re-render the removable staged-file chips whenever the selection changes.
document.addEventListener('DOMContentLoaded', () => {
    const uploadInput = document.getElementById('upload');
    if (uploadInput) uploadInput.addEventListener('change', renderStagedFiles);
});

function wireOnboardingProgress() {
    if (!document.getElementById('onboarding-progress')) return;
    ['first-name', 'last-name', 'autocomplete-input', 'tagline', 'bio-intro', 'nationalityInput'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', updateOnboardingProgress);
            el.addEventListener('change', updateOnboardingProgress);
        }
    });
    const fileInput = document.querySelector('.file-upload');
    if (fileInput) fileInput.addEventListener('change', updateOnboardingProgress);
    // Account type decides which fields are required, refresh when it changes.
    document.querySelectorAll('input[name="account-type-radio"]').forEach(r =>
        r.addEventListener('change', updateOnboardingProgress));
    // Hourly-rate slider and skills chips change outside normal inputs; poll them.
    const rateSlider = document.querySelector('.bidding-slider');
    if (rateSlider) rateSlider.addEventListener('change', updateOnboardingProgress);
    const skillsBox = document.querySelector('.keywords-list');
    if (skillsBox) new MutationObserver(updateOnboardingProgress).observe(skillsBox, { childList: true });
    updateOnboardingProgress();
}

function updateNationalitySelect(data) {
    // Get the old select element
    const oldSelect = document.getElementById("nationalityInput");

    // Loop through existing options and select the one that matches
    Array.from(oldSelect.options).forEach(option => {
      let value = option.value;

      // Check if this matches the user's nationality
      if (option.textContent === data.nationality) {
          $('#nationalityInput').selectpicker('val', value || '');
      }
    });
}



// Add event listener to the button to trigger all functions
document.querySelector('.button.ripple-effect.big').addEventListener('click', async function (e) {
  e.preventDefault(); // Prevent default <a> behavior
  document.getElementById('submitOverlay').classList.add('active');
  errorStateList.errors = [];
  errorStateList.success = [];
  noError = true;

  // Was the profile still incomplete when this page loaded?
  const wasIncomplete = !!document.getElementById('onboarding-progress');

  try {

    // Call all previously defined functions with their respective endpoints
    await handleImageUpload('/api/users/avatar/');

    // Password is handled separately via the Change Password modal

    // Call the submitFiles function
    await submitFiles();

    // Call the submitProfileExtras function
    await submitProfileExtras('/api/users/profile/edit/');

    // take the screen back to top
    window.scrollTo(0, 0);

  } catch (error) {
    
    // scroll to top
    window.scrollTo(0, 0);
    console.error("Error during profile details submission:", error);
  }

  // Route the user to the next step once their basic profile is complete.
  if (noError && isOnboardingComplete()) {
    const checkedRadio = document.querySelector('input[name="account-type-radio"]:checked');
    const isEmployer = checkedRadio ? checkedRadio.id.includes('employer') : false;

    if (isEmployer) {
      // Employers must register a company before they can use the dashboard.
      const hasCompany = await companyExists(currentUserId);
      if (!hasCompany) {
        window.location.href = '/dashboard/post-a-company/';
        return;
      }
      // Already has a company: only first-time users see the welcome preview.
      if (wasIncomplete) {
        window.location.href = '/dashboard/my-profile/?welcome=1';
        return;
      }
    } else if (wasIncomplete) {
      // First-time freelancers go straight to the profile preview.
      window.location.href = '/dashboard/my-profile/?welcome=1';
      return;
    }
  }

  // reload the page if no error occurred
  if (noError) {
    window.location.reload();
  } else {
    // console.log(errorStateList.errors, errorStateList.success);
    document.getElementById('submitOverlay').classList.remove('active');
    errorStateList.errors.forEach(err => appendError(err));
    errorStateList.success.forEach(msg => appendSuccess(msg));
  }

  // hide error message after 5secs
  setTimeout(() => {
      document.getElementById('login-error').innerHTML = '';
  }, 8000);


});

// Main function to load user profile data
document.addEventListener("DOMContentLoaded", async function () {
  // showLoading();
  
    try {
        const response = await fetchProtected('/api/users/me/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error("Failed to fetch user data");
        }

        const data = await response.json();
        console.log("Getting user details...")
        console.log(data);

        // Remember the user id for the post-save employer routing.
        currentUserId = data.user?.id || null;

        // 1. Set bidding slider value
        appendBiddingWidget(data);

        // 2. Set user avatar
        document.getElementById('user-avatar').src = data.avatar;

        // Populate form fields
        let firstName = document.querySelector('#first-name');
        let lastName = document.querySelector('#last-name');
        let email = document.querySelector('#email');
        firstName.value = data.user?.first_name || '';
        lastName.value = data.user?.last_name || '';
        email.value = data.user?.email || '';

        // Set bio
        document.getElementById('bio-intro').value = data.bio || '';

        // Set tagline
        document.getElementById('tagline').value = data.tagline || '';

        // Set portfolio link
        const portfolioInput = document.getElementById('portfolio-url');
        if (portfolioInput) portfolioInput.value = data.portfolio_url || '';

        // Set address
        const addressInput = document.getElementById('autocomplete-input');
        if (addressInput) addressInput.value = data.address || '';

        // Set nationality
        updateNationalitySelect(data);

        // Set account type
        appendAccountType(data);

        // Reflect the saved two-factor authentication state
        const twoStepEl = document.getElementById('two-step');
        if (twoStepEl) twoStepEl.checked = !!data.user?.two_step_verification;

        // append skills
        appendSkills(data.skills || '');

        // Handle file Attachments upload
        loadAttachments()

        // update user status
        updateUserNavInfo()

        document.getElementById("mainBody").style.display = 'block'

        // Initialise the onboarding completion bar from the loaded values
        wireOnboardingProgress();

    } catch (error) {
        console.error("Error loading user profile:", error);
    }
    hideLoading();
});

// Adapt Change Password modal based on whether user has a usable password
let userHasUsablePassword = true;

document.addEventListener("DOMContentLoaded", async function () {
    try {
        const res = await fetchProtected('/api/users/me/', { method: 'GET', headers: { 'Content-Type': 'application/json' } });
        if (res.ok) {
            const data = await res.json();
            userHasUsablePassword = data.user?.has_usable_password !== false;
            if (!userHasUsablePassword) {
                // Hide current password field — not needed for Google accounts
                const currentField = document.getElementById('modal-current-password')?.closest('.submit-field');
                if (currentField) currentField.style.display = 'none';
                // Update modal title
                document.querySelector('#change-password-dialog h3').innerHTML =
                    '<i class="icon-material-outline-lock" style="margin-right:8px;"></i> Set a Password';
                // Update the trigger button text in settings page
                const triggerBtn = document.querySelector('a[href="#change-password-dialog"]');
                if (triggerBtn) triggerBtn.innerHTML = '<i class="icon-material-outline-lock"></i> Add Password';
            }
        }
    } catch (e) {}
});

// Change Password modal handler
document.getElementById('submit-password-btn').addEventListener('click', async function () {
    const btn = this;
    const currentPassword = document.getElementById('modal-current-password').value.trim();
    const newPassword = document.getElementById('modal-new-password').value.trim();
    const repeatPassword = document.getElementById('modal-repeat-password').value.trim();
    const errorContainer = document.getElementById('password-modal-error');
    errorContainer.innerHTML = '';

    if (userHasUsablePassword && !currentPassword) {
        errorContainer.innerHTML = '<div class="notification error closeable"><p>Please enter your current password.</p><a class="close" href="#"></a></div>';
        bindCloseButtons(errorContainer);
        return;
    }
    if (!newPassword || !repeatPassword) {
        errorContainer.innerHTML = '<div class="notification error closeable"><p>Please fill in the new password fields.</p><a class="close" href="#"></a></div>';
        bindCloseButtons(errorContainer);
        return;
    }
    if (newPassword !== repeatPassword) {
        errorContainer.innerHTML = '<div class="notification error closeable"><p>New passwords do not match.</p><a class="close" href="#"></a></div>';
        bindCloseButtons(errorContainer);
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Updating...';

    try {
        const body = { new_password: newPassword };
        if (userHasUsablePassword) body.old_password = currentPassword;

        const res = await fetchProtected('/api/auth/update-password/', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!res.ok) {
            const err = await res.json();
            let errorMsg;
            if (err.old_password) {
                errorMsg = `Current password is incorrect. Please try again.`;
            } else if (err.new_password) {
                errorMsg = `New password is invalid: ${err.new_password[0]}`;
            } else {
                errorMsg = err.detail || Object.values(err).flat()[0] || 'Failed to update password.';
            }
            errorContainer.innerHTML = `<div class="notification error closeable"><p>${errorMsg}</p><a class="close" href="#"></a></div>`;
            bindCloseButtons(errorContainer);
            btn.disabled = false;
            btn.textContent = 'Update Password';
            return;
        }

        $.magnificPopup.close();
        document.getElementById('modal-current-password').value = '';
        document.getElementById('modal-new-password').value = '';
        document.getElementById('modal-repeat-password').value = '';
        // After setting password, restore full change-password UI
        if (!userHasUsablePassword) {
            userHasUsablePassword = true;
            const currentField = document.getElementById('modal-current-password')?.closest('.submit-field');
            if (currentField) currentField.style.display = '';
            document.querySelector('#change-password-dialog h3').innerHTML =
                '<i class="icon-material-outline-lock" style="margin-right:8px;"></i> Change Password';
            const triggerBtn = document.querySelector('a[href="#change-password-dialog"]');
            if (triggerBtn) triggerBtn.innerHTML = '<i class="icon-material-outline-lock"></i> Change Password';
        }
        appendSuccess('Password updated successfully.');

    } catch (error) {
        errorContainer.innerHTML = '<div class="notification error closeable"><p>An error occurred. Please try again.</p><a class="close" href="#"></a></div>';
        bindCloseButtons(errorContainer);
        btn.disabled = false;
        btn.textContent = 'Update Password';
    }
});


// ---- Two-Factor Authentication toggle ----
// Enabling requires confirming a code emailed to the user; disabling is immediate.
(function () {
    const toggle = document.getElementById('two-step');
    if (!toggle) return;

    const errorBox = document.getElementById('two-factor-modal-error');
    const codeInput = document.getElementById('two-factor-code');
    const confirmBtn = document.getElementById('confirm-two-factor-btn');
    const resendLink = document.getElementById('resend-two-factor-code');

    // True once the code is confirmed, so closing the modal does not revert the toggle.
    let confirmed = false;

    function showModalError(msg) {
        if (!errorBox) return;
        errorBox.innerHTML = `<div class="notification error closeable"><p>${msg}</p><a class="close" href="#"></a></div>`;
        bindCloseButtons(errorBox);
    }

    function openConfirmDialog() {
        confirmed = false;
        if (errorBox) errorBox.innerHTML = '';
        if (codeInput) codeInput.value = '';
        $.magnificPopup.open({
            items: { src: '#two-factor-dialog' },
            type: 'inline',
            callbacks: {
                close: function () {
                    // If the user dismissed the dialog without confirming, revert the toggle.
                    if (!confirmed) toggle.checked = false;
                }
            }
        });
    }

    async function requestEnableCode() {
        return fetchProtected('/api/auth/two-factor/enable/request/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    }

    toggle.addEventListener('change', async function () {
        if (toggle.checked) {
            // Turning ON: request a code, then ask the user to confirm it.
            toggle.disabled = true;
            try {
                const res = await requestEnableCode();
                if (!res.ok) throw new Error('request failed');
                openConfirmDialog();
            } catch (e) {
                console.error('Failed to start two-factor setup:', e);
                toggle.checked = false;
                appendError('Could not send a confirmation code. Please try again.');
            } finally {
                toggle.disabled = false;
            }
        } else {
            // Turning OFF: disable immediately.
            toggle.disabled = true;
            try {
                const res = await fetchProtected('/api/auth/two-factor/disable/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                if (!res.ok) throw new Error('disable failed');
                appendSuccess('Two-factor authentication disabled.');
            } catch (e) {
                console.error('Failed to disable two-factor:', e);
                toggle.checked = true; // revert
                appendError('Could not disable two-factor authentication. Please try again.');
            } finally {
                toggle.disabled = false;
            }
        }
    });

    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function () {
            const code = (codeInput?.value || '').trim();
            if (errorBox) errorBox.innerHTML = '';
            if (code.length !== 6 || !/^\d+$/.test(code)) {
                showModalError('Please enter the 6-digit code from your email.');
                return;
            }
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Confirming...';
            try {
                const res = await fetchProtected('/api/auth/two-factor/enable/confirm/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                if (res.ok) {
                    confirmed = true;
                    toggle.checked = true;
                    $.magnificPopup.close();
                    appendSuccess('Two-factor authentication enabled.');
                } else {
                    const err = await res.json().catch(() => ({}));
                    showModalError(err.detail || 'Invalid or expired code. Please try again.');
                }
            } catch (e) {
                console.error('Failed to confirm two-factor:', e);
                showModalError('An error occurred. Please try again.');
            } finally {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = 'Confirm &amp; Enable';
            }
        });
    }

    if (resendLink) {
        resendLink.addEventListener('click', async function (e) {
            e.preventDefault();
            if (errorBox) errorBox.innerHTML = '';
            try {
                const res = await requestEnableCode();
                if (!res.ok) throw new Error('resend failed');
                showModalError('A new code has been sent to your email.');
            } catch (err) {
                showModalError('Could not resend the code. Please try again.');
            }
        });
    }
})();
