let noError = true;
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

    // Get selected country/job type
    const select = document.getElementById('nationalityInput');
    const selectedOption = select.options[select.selectedIndex];
    const selectedCountry = selectedOption.textContent || '';
    // Get user data
    const firstName = document.querySelector('#first-name').value;
    const lastName = document.querySelector('#last-name').value;
    const email = document.querySelector('#email').value;
    const accountType = document.querySelector('input[name="account-type-radio"]:checked').id.includes('freelancer') ? 'freelancer' : 'employer';
    const twoStepCheckbox = document.getElementById('two-step').checked;

    const userData = {
        first_name: firstName,
        last_name: lastName,
        email: email,
        role: accountType,
        two_step_verification: twoStepCheckbox
    };

    // Construct JSON data
    let data = {
      hourly_rate: hourlyRateValue,
      tagline: tagline,
      nationality: selectedCountry,
      bio: bio,
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

  try {

    // Call all previously defined functions with their respective endpoints
    await handleImageUpload('/api/users/avatar/');

    // Call the submitPasswordUpdate function only if any password field is filled
    const [currentPassword, newPassword, repeatPassword] = 
      Array.from(document.querySelectorAll('input[type="password"]')).map(
        input => input.value.trim()
      );
    if (currentPassword || newPassword || repeatPassword) {
      await submitPasswordUpdate('/api/auth/update-password/');
    }

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

        // 1. Set bidding slider value
        appendBiddingWidget(data);

        // 2. Set user avatar
        document.getElementById('user-avatar').src = data.avatar;

        // Populate form fields
        let firstName = document.querySelector('#first-name');
        let lastName = document.querySelector('#last-name');
        let email = document.querySelector('#email');
        let twoStepCheckbox = document.getElementById('two-step');

        firstName.value = data.user?.first_name || '';
        lastName.value = data.user?.last_name || '';
        email.value = data.user?.email || '';
        
        console.log("setting two set verification....");
        if (data.user?.two_step_verification){
          twoStepCheckbox.checked = true;
        } else {
          twoStepCheckbox.checked = false;
        }

        // Set bio
        document.getElementById('bio-intro').value = data.bio || '';

        // Set tagline
        document.getElementById('tagline').value = data.tagline || '';

        // Set nationality
        updateNationalitySelect(data);

        // Set account type
        appendAccountType(data);

        // append skills
        appendSkills(data.skills || '');

        // Handle file Attachments upload
        loadAttachments()

        // update user status
        updateUserNavInfo()

        document.getElementById("mainBody").style.display = 'block'

    } catch (error) {
        console.error("Error loading user profile:", error);
    }
    hideLoading();
});
