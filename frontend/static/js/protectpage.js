let userValidated = false;  // track validation status

// Helper: fetch with retry for server errors
async function fetchWithRetry(url, options = {}, retries = 3, delay = 1000) {
    try {
        const res = await fetch(url, options);

        // Retry on server errors (500+)
        if (res.status >= 500 && retries > 0) {
            console.warn(`Server error ${res.status}. Retrying in ${delay}ms...`);
            await new Promise(r => setTimeout(r, delay));
            return fetchWithRetry(url, options, retries - 1, delay);
        }

        return res;
    } catch (err) {
        // Network errors
        if (retries > 0) {
            console.warn(`Network error. Retrying in ${delay}ms...`, err);
            await new Promise(r => setTimeout(r, delay));
            return fetchWithRetry(url, options, retries - 1, delay);
        }
        throw err;
    }
}

// Check if user is authenticated
let _protectPageAuthPromise = null;
async function isAuthenticated(retries = 3) {
    if (typeof accessToken !== "undefined" && accessToken && typeof isTokenExpired === "function" && !isTokenExpired(accessToken)) {
        return true;
    }
    if (_protectPageAuthPromise) return _protectPageAuthPromise;
    _protectPageAuthPromise = (async () => {
        try {
            const res = await fetchWithRetry('/api/auth/token/refresh/', {
                method: 'POST',
                credentials: 'include'
            }, retries);
            if (res.ok) {
                const data = await res.json();
                accessToken = data.access;
                return true;
            }
            return false;
        } catch (err) {
            console.error("Authentication check failed:", err);
            return false;
        } finally {
            _protectPageAuthPromise = null;
        }
    })();
    return _protectPageAuthPromise;
}

// Protect the page
async function protectPage() {
    const isAuth = await isAuthenticated();
    if (!isAuth) {
        console.log("You are not logged in. Redirecting...");
        alert("You must be logged in to access this page.");
        window.location.href = "/login/";
    } else {
        userValidated = true;
        console.log("User is authenticated. Access granted.");
        const mainBody = document.getElementById("mainBody");
        if (mainBody) mainBody.style.display = "block";
    }
}

protectPage();

function showContent() {
    // Show page only after validation
    if (!userValidated) return;
    const mainBody = document.getElementById("mainBody");
    if (mainBody) mainBody.style.display = "block";
}

// Run protectPage on DOMContentLoaded
// document.addEventListener("DOMContentLoaded", showContent);
