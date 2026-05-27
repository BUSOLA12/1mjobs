document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('right-side-nav').querySelectorAll('.header-widget').forEach(widget => {
    widget.remove();
    })
}); 

document.getElementById('register-account-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = document.getElementById('emailaddress-register').value;
    const password = document.getElementById('password-register').value;
    const confirmPassword = document.getElementById('password-repeat-register').value;

    // Check if passwords match
    if (password !== confirmPassword) {
        appendError("Passwords do not match!");
        return;
    }

    showLoading();

    // Check which account type is selected
    const isFreelancer = document.getElementById('freelancer-radio').checked;
    const role = isFreelancer ? 'freelancer' : 'employer';  // adjust to match backend expectation
    const submitTokenBtn = document.getElementById('submitTokenBtn');
    const tokenInput = document.getElementById('tokenInput');

    try {
        const response = await fetch('/api/auth/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password,
                role: role
            })
        });

        if (response.ok) {
            console.log("Registration successful! confirm email...");
            showTokenOverlay();
            hideLoading();
            submitTokenBtn.addEventListener('click', async () => {
                showLoading();
                const code = tokenInput.value.trim();

                if (code.length !== 6 || !/^\d+$/.test(code)) {
                    hideLoading();
                    appendError("Please enter a valid 6-digit code.");
                    return;
                }

                try {
                    const res = await fetch("/api/auth/verify-email-otp/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, code })
                    });

                    const data = await res.json();

                    if (res.ok) {
                        console.log("token verification successful, redirecting to login page...");
                        appendError("Email verified successfully, redirecting to log in.", "success");
                        setTimeout(() => {
                            window.location.href = "/login/";
                        }, 4000);
                    } else {
                        appendError("Invalid code entered");
                        console.log("Invalid code entered: " + (data.detail || JSON.stringify(data)));
                    }
                } catch (err) {
                    hideLoading();
                    appendError("An error occurred while verifying the code.");
                    console.error("An error occurred: " + err.message);
                }
            }); 
        } else {
            hideLoading();
            const errorData = await response.json();
            const loginError = document.getElementById('login-error');

            if (errorData.email) {
                appendError('Email already exists');
            } else if (errorData.password) {
                appendError('Password does not meet requirements');
            }

            console.log('Registration failed. Please try again.', errorData);
        }
    } catch (err) {
        console.error('Registration error:', err);
        appendError('An error occurred while registering.');
    }
});
