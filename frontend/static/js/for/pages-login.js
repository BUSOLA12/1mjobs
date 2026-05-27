
accessToken = null;

// get the query parameter in the URL
const urlParams = new URLSearchParams(window.location.search);
const redirect = urlParams.get('redirect');

document.getElementById('login-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    showLoading();

    const email = document.getElementById('emailaddress').value;
    const password = document.getElementById('password').value;
    const submitTokenBtn = document.getElementById('submitTokenBtn');
    const tokenInput = document.getElementById('tokenInput');

    const loginError = document.getElementById('login-error');

    try {
        const res = await fetch("/api/auth/login/", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })

        });

        if (res.ok) {
            const data = await res.json();

            // If two-factor is required
            if (data.two_factor_required === true) {
                const overlay = document.getElementById('overlayToken');
                const messageBox = document.getElementById('messageTokenBox');
                
                // Request two-factor token
                const twoFactorRes = await fetch("/api/auth/two-factor/request/", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email })
                });

                if (twoFactorRes.ok) {
                    // Show overlay message
                    // displayOverlay('Check your email for a login link.');
                    hideLoading();
                    showTokenOverlay();
                    submitTokenBtn.addEventListener('click', async () => {
                        showLoading();
                        const code = tokenInput.value.trim();

                        if (code.length !== 6 || !/^\d+$/.test(code)) {
                            hideLoading();
                            appendError("Please enter a valid 6-digit code.");
                            return;
                        }

                        try {
                            const res = await fetch("/api/auth/two-factor/verify/", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ email, code })
                            });

                            const data = await res.json();

                            if (res.ok) {
                                accessToken = data.access; // store token as needed
                                hideTokenOverlay();
                                const loginSuccess = await sendBrowserAccessToken(email, password);

                                if (loginSuccess) {
                                    console.log("Login successful, redirecting...");

                                    if (redirect) {
                                        window.location.href = redirect;
                                    } else {
                                        window.location.href = "/dashboard/";
                                    }
                                } else {
                                    appendError("Login failed, please try again.");
                                    console.log("Login failed, please try again.");
                                    hideLoading();
                                }
                            } else {
                                appendError("Invalid code entered");
                                console.log("Invalid code entered: " + (data.detail || JSON.stringify(data)));
                                hideLoading();
                            }
                        } catch (err) {
                            console.error("An error occurred: " + err.message);
                        }
                    });
                } else {
                    hideLoading();
                    err = await twoFactorRes.json();
                    console.error("Two-factor request failed: " + (err.detail || JSON.stringify(err)));
                    displayOverlay("Failed to initiate two-factor authentication.");
                }
            } else {
                accessToken = data.access;
                const loginSuccess = await sendBrowserAccessToken(email, password);

                if (loginSuccess) {
                    console.log("Login successful, redirecting...");

                    if (redirect) {
                        window.location.href = redirect;
                    } else {
                        window.location.href = "/dashboard/";
                    }
                } else {
                    appendError("Login failed, please try again.");
                    hideLoading();
                }
            }

        } else {
            const err = await res.json();
            appendError(err.detail);
            console.error("Login failed: " + err);
            hideLoading();

            // popup for email verification if email not verified user1@gmail.com
            if (err.detail[0] === "Email not verified.") {
                setTimeout(() => {
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
                                hideTokenOverlay();
                                hideLoading();
                                console.log("token verification successful");
                                appendError("Email verified successfully", "success");
                            } else {
                                hideLoading();
                                appendError("Invalid code entered");
                                console.log("Invalid code entered: " + (data.detail || JSON.stringify(data)));
                            }
                        } catch (err) {
                            console.error("An error occurred: " + err.message);
                        }
                    });
                }, 3000);
            }
        }

    } catch (error) {
        console.error('Login error:', error);
        appendError('Something went wrong.');
        hideLoading();
    }
});