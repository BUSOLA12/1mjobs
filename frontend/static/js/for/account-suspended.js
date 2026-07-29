// The appeal page works in two modes:
//   password mode  - reached from the login flow; owner confirms with a password.
//   token mode     - reached from an emailed link (uid+token); used by Google /
//                    passwordless accounts that have no password to confirm.
const params = new URLSearchParams(window.location.search);
const uid = params.get('uid');
const token = params.get('token');
const tokenMode = !!(uid && token);

// Reason/context: sessionStorage (login flow) or URL params (email/redirect flow).
let info = JSON.parse(sessionStorage.getItem('suspensionInfo') || '{}');
if (!info.account_status && params.get('status')) {
    info = {
        email: info.email || params.get('email') || '',
        account_status: params.get('status'),
        reason: params.get('reason') || '',
        suspended_until: params.get('until') || null,
    };
}

// No context at all (e.g. direct visit): send back to login.
if (!info.email && !tokenMode) {
    window.location.href = '/login/';
}

const banned = info.account_status === 'banned';

document.getElementById('status-title').textContent = banned ? 'Account Banned' : 'Account Suspended';
document.getElementById('status-line').textContent = banned
    ? 'Your account has been banned.'
    : 'Your account has been suspended.';
document.getElementById('reason-text').textContent = info.reason
    ? 'Reason: ' + info.reason
    : 'No reason was provided.';

if (info.suspended_until) {
    const until = document.getElementById('until-text');
    until.style.display = 'block';
    until.textContent = 'Suspended until: ' + new Date(info.suspended_until).toLocaleString();
}

// In token mode the password field is meaningless; hide it and the Google prompt.
if (tokenMode) {
    const pwWrap = document.getElementById('appeal-password-wrap');
    pwWrap.style.display = 'none';
    document.getElementById('appeal-password').required = false;
} else {
    document.getElementById('google-appeal').style.display = 'block';
}

document.getElementById('appeal-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const message = document.getElementById('appeal-message').value;
    const errBox = document.getElementById('appeal-error');
    const okBox = document.getElementById('appeal-success');
    const submitBtn = document.getElementById('appeal-submit-btn');
    const submitText = document.getElementById('appeal-submit-text');

    // Loading state
    submitBtn.disabled = true;
    submitText.textContent = 'Submitting...';
    errBox.innerHTML = '';

    const url = tokenMode ? '/api/auth/appeal/token/' : '/api/auth/appeal/';
    const body = tokenMode
        ? { uid, token, message }
        : { email: info.email, password: document.getElementById('appeal-password').value, message };

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();

        if (res.ok) {
            document.getElementById('appeal-form').style.display = 'none';
            const gp = document.getElementById('google-appeal');
            if (gp) gp.style.display = 'none';
            errBox.innerHTML = '';
            okBox.style.display = 'block';
            okBox.textContent = data.detail;
            sessionStorage.removeItem('suspensionInfo');
        } else {
            errBox.innerHTML = '<div class="notification error"><p>' +
                (data.detail || 'Something went wrong.') + '</p></div>';
            submitBtn.disabled = false;
            submitText.textContent = 'Submit Appeal';
        }
    } catch (err) {
        errBox.innerHTML = '<div class="notification error"><p>Something went wrong.</p></div>';
        submitBtn.disabled = false;
        submitText.textContent = 'Submit Appeal';
    }
});

// Passwordless accounts: request an emailed appeal link.
const requestLinkBtn = document.getElementById('request-link-btn');
if (requestLinkBtn) {
    requestLinkBtn.addEventListener('click', async function (e) {
        e.preventDefault();
        const msgBox = document.getElementById('request-link-msg');
        requestLinkBtn.style.pointerEvents = 'none';
        msgBox.innerHTML = 'Sending...';
        try {
            const res = await fetch('/api/auth/appeal/request-link/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: info.email }),
            });
            const data = await res.json();
            msgBox.innerHTML = '<div class="notification success"><p>' +
                (data.detail || 'Check your email.') + '</p></div>';
        } catch (err) {
            msgBox.innerHTML = '<div class="notification error"><p>Something went wrong.</p></div>';
            requestLinkBtn.style.pointerEvents = 'auto';
        }
    });
}
