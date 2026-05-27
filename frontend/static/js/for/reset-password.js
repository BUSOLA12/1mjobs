const form = document.getElementById("resetForm")

// Extract UID and Token from URL
const pathParts = window.location.pathname.split("/")

const uid = pathParts[pathParts.length - 3]
const token = pathParts[pathParts.length - 2]

form.addEventListener("submit", async function (e) {

    e.preventDefault()

    const newPassword = document.getElementById("new_password").value
    const confirmPassword = document.getElementById("confirm_password").value

    // Check passwords match
    if (newPassword !== confirmPassword) {
        console.error("Passwords do not match")
        appendError("Passwords do not match.")
        return
    }

    const payload = {
        uidb64: uid,
        token: token,
        new_password: newPassword
    }

    try {

        const response = await fetch("/api/auth/reset-password/confirm/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })

        const data = await response.json()

        if (response.ok) {
            console.log("Password reset successful:", data)
            appendError(data.details + " Redirecting to login...", "success")
            // redirect to login after 3 seconds
            setTimeout(() => {
                window.location.href = "/login"
            }, 3000)

        } else {
            appendError("Failed to reset password.")
            console.error("Error:", data)

        }

    } catch (error) {
        console.error("Request failed:", error)

    }

})