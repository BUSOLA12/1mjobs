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
    const role = isFreelancer ? 'freelancer' : 'employer';

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
            hideLoading();
            appendError("Registration successful! Redirecting to log in.", "success");
            setTimeout(() => {
                window.location.href = "/login/";
            }, 2000);
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
