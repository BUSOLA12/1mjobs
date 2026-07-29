
// Show loading overlay
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

// Fetch current user (optional)
async function fetchUserId() {
  try {
    const response = await fetchProtected(`/api/users/currentuser/`);
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error('Error fetching user ID:', error);
    return null;
  }
}

// Validate input fields
function validateInputs(fields) {
  let isValid = true;

  fields.forEach(({ selector, name }) => {
    const input = document.querySelector(selector);
    const value = input ? input.value.trim() : "";

    // Remove any previous error styles
    input?.classList.remove("input-error");

    if (!value) {
      isValid = false;
      input?.classList.add("input-error");
      Snackbar.show({
        text: `Please enter ${name}.`,
        pos: "bottom-center",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#fa0404ff",
      });
    }
  });

  return isValid;
}

// Handle submit
document.querySelector(".button.ripple-effect.big.margin-top-30").addEventListener("click", async function (e) {
  e.preventDefault();

  showLoading("Posting Company...");

  // List of required fields
  const requiredFields = [
    { selector: "input[placeholder='Enter Company Name']", name: "Company Name" },
    { selector: "select[title='Select Industry']", name: "Industry" },
    { selector: "textarea[placeholder='Describe the company, services, or products']", name: "Description" },
    { selector: "input[placeholder='Enter Registration Number']", name: "Registration Number" },
    { selector: "input[placeholder='Enter Tax ID']", name: "Tax ID" },
    { selector: "input[type='date'][name='established_date']", name: "Established Date" },
    { selector: "select[title='Select Size']", name: "Company Size" },
    { selector: "input[placeholder='Type Address']", name: "Headquarters Address" },
    { selector: "input[placeholder='Enter Company Country']", name: "Company Country" },
    { selector: "input[placeholder='+234 800 000 0000']", name: "Primary Phone" },
    { selector: "input[placeholder='company@example.com']", name: "Email" },
    { selector: "input[placeholder='https://companywebsite.com']", name: "Website" },
  ];

  // Run validation
  if (!validateInputs(requiredFields)) {
    hideLoading();
    return; // stop submission
  }

  // Get logged-in user (optional)
  // const userInfo = await fetchUserId();
  // if (!userInfo) {
  //   alert("Failed to fetch user info!");
  //   hideLoading();
  //   return;
  // }

  const formData = new FormData();

  // formData.append("created_by", userInfo.id);
  formData.append("company_name", document.querySelector("input[placeholder='Enter Company Name']").value);
  formData.append("brand_name", document.querySelector("input[placeholder='If different from Company Name']").value);
  formData.append("industry", document.querySelector("select[title='Select Industry']").value);
  formData.append("description", document.querySelector("textarea[placeholder='Describe the company, services, or products']").value);

  // Registration details
  formData.append("registration_number", document.querySelector("input[placeholder='Enter Registration Number']").value);
  formData.append("tin", document.querySelector("input[placeholder='Enter Tax ID']").value);
  formData.append("established_date", document.querySelector("input[type='date'][name='established_date']").value);
  formData.append("company_size", document.querySelector("select[title='Select Size']").value);

  // Location & address
  formData.append("headquarters_address", document.querySelector("input[placeholder='Type Address']").value);
  formData.append("company_country", document.querySelector("input[placeholder='Enter Company Country']").value);

  // Contact info
  formData.append("primary_phone", document.querySelector("input[placeholder='+234 800 000 0000']").value);
  formData.append("secondary_phone", document.querySelector("input[placeholder='+234 800 000 0001']").value);
  formData.append("email", document.querySelector("input[placeholder='company@example.com']").value);
  formData.append("website", document.querySelector("input[placeholder='https://companywebsite.com']").value);

  // Social links
  formData.append("facebook", document.querySelector("input[placeholder='https://facebook.com/yourpage']").value);
  formData.append("linkedin", document.querySelector("input[placeholder='https://linkedin.com/company/yourpage']").value);

  // Logo
  const logoFile = document.querySelector("#company-logo").files[0];
  if (logoFile) {
    formData.append("logo", logoFile);
  }

  // Documents
  const docs = document.querySelector("#upload").files;
  for (let i = 0; i < docs.length; i++) {
    formData.append("documents", docs[i]);
  }

  // Submit to backend
  try {
    const response = await fetchProtected("/api/companies/create/", {
      method: "POST",
      body: formData,
    });

    
    hideLoading();

    if (response.ok) {
      Snackbar.show({
        text: "Company posted successfully!",
        pos: "bottom-center",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#04fa2dff",
      });
      const result = await response.json();
      console.log(result);
      // Company created: take the employer to their profile preview
      // (shows profile + company) with the "Go to Dashboard" prompt.
      window.location.href = '/dashboard/my-profile/?welcome=1';
      return;
    } else {
      const result = await response.json();
      console.log(result);
      Snackbar.show({
        text: JSON.stringify(result.Message),
        pos: "bottom-center",
        duration: 3000,
        textColor: "#fff",
        backgroundColor: "#fa0404ff",
      });
    }
  } catch (error) {
    hideLoading();
    console.error("Error:", error);
    Snackbar.show({
      text: "Something went wrong!",
      pos: "bottom-center",
      duration: 3000,
      textColor: "#fff",
      backgroundColor: "#fa0404ff",
    });
  }
});

// Optional CSS for error highlight
const style = document.createElement("style");
style.textContent = `
  .input-error {
    border: 2px solid red !important;
    background-color: #ffe6e6 !important;
  }
`;
document.head.appendChild(style);

// Back out: a user who changed their mind reverts to a freelancer account.
(function setupRoleBackout() {
  const btn = document.getElementById("switch-to-freelancer-btn");
  if (!btn) return;
  btn.addEventListener("click", async function () {
    btn.disabled = true;
    try {
      const res = await fetchProtected("/api/users/role/", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: "freelancer" }),
      });
      if (!res.ok) throw new Error("Role update failed");
      // Now a freelancer: the onboarding middleware no longer blocks the dashboard.
      window.location.href = "/dashboard/";
    } catch (error) {
      console.error("Failed to switch role:", error);
      btn.disabled = false;
      if (window.Snackbar) {
        Snackbar.show({
          text: "Could not switch back. Please try again.",
          pos: "bottom-center",
          duration: 3000,
          textColor: "#fff",
          backgroundColor: "#fa0404ff",
        });
      }
    }
  });
})();

// Let users remove staged files before submitting.
(function setupStagedFileRemoval() {
  function chip(name, onRemove) {
    const c = document.createElement("span");
    c.style.cssText = "display:inline-flex;align-items:center;gap:6px;background:#eef0f4;border-radius:6px;padding:4px 10px;margin:6px 6px 0 0;font-size:13px;color:#333;";
    const label = document.createElement("span");
    label.textContent = name;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", "Remove " + name);
    remove.style.cssText = "border:none;background:transparent;cursor:pointer;font-size:16px;line-height:1;color:#e74c3c;padding:0;";
    remove.addEventListener("click", onRemove);
    c.appendChild(label);
    c.appendChild(remove);
    return c;
  }

  // --- Supporting documents (multiple) ---
  const docInput = document.getElementById("upload");
  const docNameField = document.querySelector(".uploadButton-file-name");
  if (docInput && docNameField && window.DataTransfer) {
    const defaultHint = docNameField.textContent;
    const dt = new DataTransfer();

    function renderDocs() {
      if (dt.items.length === 0) {
        docNameField.textContent = defaultHint;
        return;
      }
      docNameField.innerHTML = "";
      Array.from(dt.files).forEach((file, idx) => {
        docNameField.appendChild(chip(file.name, function () {
          dt.items.remove(idx);
          docInput.files = dt.files;
          renderDocs();
        }));
      });
    }

    docInput.addEventListener("change", function () {
      // Accumulate across selections, de-duped by name+size.
      Array.from(docInput.files).forEach(f => {
        const dup = Array.from(dt.files).some(x => x.name === f.name && x.size === f.size);
        if (!dup) dt.items.add(f);
      });
      docInput.files = dt.files;
      // Run after the theme's own change handler so our chips win.
      setTimeout(renderDocs, 0);
    });
  }

  // --- Company logo (single) ---
  const logoInput = document.getElementById("company-logo");
  const logoNameField = document.getElementById("logo-file-name");
  if (logoInput && logoNameField) {
    logoInput.addEventListener("change", function () {
      setTimeout(function () {
        logoNameField.innerHTML = "";
        const file = logoInput.files[0];
        if (!file) return;
        logoNameField.appendChild(chip(file.name, function () {
          logoInput.value = "";
          logoNameField.innerHTML = "";
        }));
      }, 0);
    });
  }
})();

// Re-entry guard: if this employer already has a company, skip straight to
// the profile preview instead of showing the "already posted" dead-end.
document.addEventListener("DOMContentLoaded", async function () {
  try {
    const user = await fetchUserId();
    if (!user || !user.id) return;
    const res = await fetchProtected(`/api/companies/exists/${user.id}/`);
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.status === true) {
      window.location.href = '/dashboard/my-profile/';
    }
  } catch (error) {
    console.error("Company existence check failed:", error);
  }
});

