let accessToken = null; // in-memory only
let userInfo = null;     // in-memory decoded user data (email, role, etc.)

async function sendBrowserAccessToken(email, password) {
    console.log("Initializing browser access token login");

    try {
        const res = await fetch("/api/auth/token/", {
            method: 'POST',
            credentials: 'include',  // allow backend to set refresh token cookie
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        if (res.ok) {
            const data = await res.json();
            accessToken = data.access;
            userInfo = decodeJwtPayload(accessToken);  // ✅ store decoded data
            console.log("Logged in as:", userInfo);
            return true;
        } else {
            const err = await res.json();
            alert(err.detail || 'Browser login failed');
            return false;
        }
    } catch (error) {
        console.error('Browser login error:', error);
        return false;
    }
}

    
// Silent refresh on every page (can go in a common base file like main.js)
function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiry = payload.exp;
        const now = Math.floor(Date.now() / 1000); // current time in seconds is 
        return expiry < now; //
    } catch (err) {
        return true;  // treat malformed token as expired
    }
}

let refreshing = false;

async function getAccessToken() {
    // Prevent multiple refresh requests running at the same time
    if (refreshing) {
    return new Promise(resolve => {
        document.addEventListener("data-ready", () => resolve(accessToken), { once: true });
    });
    }

    if (!accessToken || isTokenExpired(accessToken)) {
        refreshing = true;
        try {
            const res = await fetch('/api/auth/token/refresh', {
                method: 'POST',
                credentials: 'include',
            });

            if (!res.ok) {
                console.warn("Refresh token invalid or expired");
                throw new Error(`Refresh failed (${res.status})`);
            }

            const data = await res.json();
            accessToken = data.access;
            userInfo = decodeJwtPayload(accessToken);
            document.dispatchEvent(new Event("data-ready"));
            console.log("Access token refreshed:", accessToken);

        } catch (err) {
            console.error("Token refresh error:", err);

            // Optional: differentiate between network and auth failure
            if (err.name === "TypeError") {
                alert("Network issue — please check your connection.");
            } else {
                // Redirect only if refresh truly fails (not network)
                alert("Token invalid or expired, please log in again.");
                //get current page url and add as query parameter to redirect
                const currentUrl = window.location.href;
                // remove the domain and path, leaving the query string
                const queryString = currentUrl.split('/').slice(3).join('/');

                const newUrl = "/login" + '?redirect=/' + queryString;
                window.location.href = newUrl;
            }

        } finally {
            refreshing = false;
        }
    } else {
        try {
            userInfo = decodeJwtPayload(accessToken);
            document.dispatchEvent(new Event("data-ready"));
        } catch (err) {
            console.error("Error decoding token:", err);
            alert("Error decoding token:", err);
        }
    }

    return accessToken;
}


async function fetchProtected(url, options = {}, retries = 3, delay = 1000) {
  const authenticated = await isAuthenticated();
  if (!authenticated) {
    appendError("You must be logged in.");
    return;
  }

  try {
    const token = await getAccessToken();
    const headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    };

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
      window.location.href = "/login/";
      return;
    }

    // Handle 500 errors and retries
    if (res.status >= 500) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
        // Pass the updated retries and delay back into the function
        return fetchProtected(url, options, retries - 1, delay * 2);
      }
      // If we reach here, we've exhausted retries
      return res; 
    }

    return res;

  } catch (err) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchProtected(url, options, retries - 1, delay * 2);
    }
    throw err; // Rethrow so the caller knows the request failed
  }
}


// async function fetchProtected(url, options = {}) {
//   console.log("FetchProtected called with URL:", url);

//   const authenticated = await isAuthenticated();
//   if (!authenticated) {
//     appendError("You must be logged in to access this resource.");
//     return;
//   }

//   const retries = 3;
//   const delay = 1000;
//   try {
//     const token = await getAccessToken();
//     if (!token) throw new Error("Missing token, please log in again.");

//     const headers = {
//       ...(options.headers || {}),
//       Authorization: `Bearer ${token}`,
//     };

//     // If body is FormData, don’t manually set Content-Type
//     if (!(options.body instanceof FormData)) {
//       headers['Content-Type'] = headers['Content-Type'] || 'application/json';
//     }

//     const res = await fetch(url, { ...options, headers });

//     // Handle authentication issues
//     if (res.status === 401) {
//       console.warn("Token invalid or expired, redirecting to login...");
//       alert("Token invalid or expired, please log in again.");
//       window.location.href = "/login/";
//       return;
//     }

//     // Handle server errors (500+)
//     if (res.status >= 500) {
//       console.error(`Server error (${res.status}) on ${url}`);

//       // If the failing request is for the current page, just reload
//       if (window.location.pathname === new URL(url, window.location.origin).pathname) {
//         console.warn("Reloading page due to server error on current page.");
//         window.location.reload();
//         return;
//       }

//       // Retry logic (exponential backoff)
//       if (retries > 0) {
//         console.warn(`Retrying (${4 - retries}/3)... waiting ${delay}ms`);
//         await new Promise(resolve => setTimeout(resolve, delay));
//         return fetchProtected(url, options, retries - 1, delay * 2);
//       }

//       alert("A server error occurred after multiple attempts. Please try again later.");
//       return res;
//     }

//     return res;

//   } catch (err) {
//     console.error("Request failed:", err);

//     // Retry on network errors
//     if (retries > 0) {
//       console.warn(`Network error: retrying (${4 - retries}/3)...`);
//       await new Promise(resolve => setTimeout(resolve, delay));
//       return fetchProtected(url, options, retries - 1, delay * 2);
//     }

//     alert("Network or authentication error. Please try again later.");
//   }
// }



async function logout() {
    console.log("Logout initiated");

    try {
        const res = await fetchProtected('/api/auth/token/delete/', {
            method: 'POST',
            credentials: 'include', // IMPORTANT: send cookies
        });

        if (res.ok) {
            console.log("Logged out successfully");
            accessToken = null;  // clear in-memory token
            window.location.href = "/login";
        } else {
            const data = await res.json();
            console.error("Logout failed:", data.detail || data);
        }
    } catch (err) {
        console.error("Logout error:", err);
    }
}

// Helper to decode JWT payload
function decodeJwtPayload(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return {
            id: payload.user_id,
            email: payload.email,
            role: payload.role,
            status: payload.status,
            exp: payload.exp,
            avatar_url: payload.avatar_url,
            first_name: payload.first_name,
            last_name: payload.last_name,
            full_name: `${payload.first_name} ${payload.last_name}`.trim(),
        };
    } catch (err) {
        console.error("Invalid JWT:", err);
        return null;
    }
}
