


async function fetchcurrentuserId(senderId) {
    try {
        const response = await fetchProtected(`/api/users/currentuser/${senderId}/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user ID:', error);
        return null;
    }
}

async function fetchUserId() {
    try {
        const response = await fetchProtected(`/api/users/currentuser/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user ID:', error);
        return null;
    }
}




const messageList = document.querySelector('.message-box-list');

function renderItem(notificationData) {
    const li = document.createElement('li');
    li.dataset.id = notificationData.message_id;
    li.className = "notifications-not-read";
    const convId = notificationData.conversation_id;
    const senderId = notificationData.sender_id;


    li.innerHTML = `
        <a href="/dashboard/messages/?conv_id=${convId}&sender_id=${senderId}">
            <span class="notification-avatar status-online"><img src="{% static 'images/user-avatar-small-03.jpg' %}" alt=""></span>
            <div class="notification-text">
                <strong>${notificationData.sender}</strong>
                <p class="notification-msg-text">${notificationData.message}</p>
                <span class="color">${timeAgo(notificationData.timestamp)}</span>
            </div>
        </a>
    `;
    messageList.prepend(li);
}


async function loadUnread() {
    try {
        const res = await fetchProtected(`/api/messaging/unread-notifications/`);
        if (!res.ok) {
                throw new Error('Network response was not ok');
            }
        const data = await res.json();
        return data;
    } catch (error) {
        console.error('Error fetching user ID:', error);
        return null;
    }
}

function timeAgo(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000); // difference in seconds

  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} days ago`;
  
  return date.toLocaleDateString(); // fallback to normal date
}


// Count only real notifications, ignoring the empty-state placeholder.
function unreadItemCount() {
    return messageList
        ? messageList.querySelectorAll('li:not(.notifications-empty)').length
        : 0;
}

// Show a placeholder when the dropdown has no messages, remove it otherwise.
function refreshEmptyState() {
    if (!messageList) return;
    let empty = messageList.querySelector('.notifications-empty');
    if (unreadItemCount() === 0) {
        if (!empty) {
            empty = document.createElement('li');
            empty.className = 'notifications-empty notif-empty';
            empty.innerHTML =
                '<span class="notif-empty-icon"><i class="icon-feather-mail"></i></span>' +
                '<span class="notif-empty-text">No new messages.</span>';
            messageList.appendChild(empty);
        }
    } else if (empty) {
        empty.remove();
    }
}

async function renderUnread() {
    const data = await loadUnread();
    const nl = data.notifications; 
    
    
    const userId_ = await fetchUserId();
    console.log("User details 2:", userId_);
    const userId = userId_.id;
    
    // Clear old notifications to avoid duplicates
    messageList.innerHTML = '';

    for (const n of nl) {
        
        const li = document.createElement('li');
        li.className = "notifications-not-read";
        li.dataset.id = n.notification_id;

        const convId = n.conversation_id;
        const senderId = n.sender_id;
        li.dataset.conversationId = convId;
        

        li.innerHTML = `
        <a href="/dashboard/messages/?conv_id=${convId}&sender_id=${senderId}">
            <span class="notification-avatar status-online"><img src=${n.user_avatar} alt=""></span>
            <div class="notification-text">
                <strong>${n.sender}</strong> <br>
                <p class="notification-msg-text">${n.message}</p> <br>
                <span class="color">${timeAgo(n.timestamp)}</span>
            </div>
        </a>
        `;

        if (senderId !== userId && userId === n.recipient) {
            messageList.prepend(li);
        }
        // Handle mark-as-read click
        // li.querySelector('.mark-read').addEventListener('click', async function (e) {
        //     e.preventDefault();
        //     const notificationId = this.dataset.id;
        //     console.log("Notification ID to mark as read:", notificationId);

        //     try {
        //         await fetchProtected(`http://127.0.0.1:8000/api/messaging/mark-one-read/${notificationId}/`, {method: "PUT",});
                
        //         li.remove();
        //     } catch (error) {
        //         console.error("Error marking as read:", error);
        //     }
        // });
    }

    const notCount = document.getElementById("notification-count");
    if (notCount) {
        // Always show the badge (including "0"), to match the notification bell.
        notCount.textContent = unreadItemCount();
        notCount.style.display = "";
    }
    refreshEmptyState();
}

// Remove the dropdown notification items for a conversation that's just been
// read and re-sync the header badge to the remaining count. Keeps the badge and
// the dropdown list consistent (the badge is derived from the list length).
function clearConversationNotifications(conversationId) {
    if (!messageList) return;
    messageList
        .querySelectorAll(`li[data-conversation-id="${conversationId}"]`)
        .forEach(li => li.remove());
    const notCount = document.getElementById("notification-count");
    if (notCount) {
        notCount.textContent = unreadItemCount();
        notCount.style.display = "";
    }
    refreshEmptyState();
}

const markAllReadBtn = document.querySelector('#mark-all-read');

if (markAllReadBtn) {
    markAllReadBtn.addEventListener('click', async function (e) {
        e.preventDefault();
        console.log("Mark all as read clicked");

        try {
            const response = await fetchProtected(
                `/api/messaging/mark-all-read/`,
                { method: "PUT" }
            );

            if (response.ok) {
                const data = await response.json();
                console.log(data.message);

                if (window.Snackbar) Snackbar.show({
                    text: "All messages marked as read.", pos: "bottom-center",
                    showAction: false, duration: 2500, backgroundColor: "#38b653", textColor: "#fff"
                });

                // ✅ Re-render notifications list to reflect changes
                await renderUnread();

                // ✅ Update notification count badge to 0
                const countElement = document.getElementById("notification-count");
                if (countElement) {
                    countElement.textContent = "0";
                    countElement.style.display = ""; // Keep badge visible, showing "0"
                }
            } else {
                console.error("Failed to mark all notifications as read.");
                alert("Error marking notifications as read!");
            }
        } catch (error) {
            console.error("An error occurred:", error);
            alert("Something went wrong!");
        }
    });
}

// ---- Live header message badge (all pages except the Messages page) --------
// The full message-list WebSocket is only opened on the Messages page. On every
// other page we open a slim connection here so the header message badge updates
// the moment a new message arrives: on Message create the server pushes a
// 'send_notification' event to the recipient's user_<id> channel group
// (see Messaging/signals.py). Without this, the badge only reflected the count
// at page load and never increased live.
let headerNotifSocket = null;
let headerNotifReconnect = null;

async function connectHeaderNotifSocket() {
    // The Messages page runs its own socket — don't open a second one there.
    if (document.getElementById('conversations-list')) return;
    if (!(await isAuthenticated())) return;

    // getAccessToken() refreshes the token if needed, so reconnects stay valid.
    let token = null;
    try {
        token = (typeof getAccessToken === "function") ? await getAccessToken() : accessToken;
    } catch (e) { token = null; }
    if (!token) return;

    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${scheme}://${window.location.host}/ws/messaging/?token=${encodeURIComponent(token)}`;

    try {
        headerNotifSocket = new WebSocket(url);
    } catch (e) {
        return;
    }

    headerNotifSocket.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch (e) { return; }
        // A new message arrived for this user (or the conversation list changed):
        // re-sync the header dropdown + badge from the server.
        if (data.type === "send_notification" || data.type === "refresh_conv") {
            renderUnread();
        }
    };

    headerNotifSocket.onclose = () => {
        // Reconnect after a short delay; the next attempt refreshes the token.
        clearTimeout(headerNotifReconnect);
        headerNotifReconnect = setTimeout(connectHeaderNotifSocket, 5000);
    };

    headerNotifSocket.onerror = () => {
        try { headerNotifSocket.close(); } catch (e) {}
    };
}

let contentLoaded = false;
let dataReady = false;
let initialRun = false;
async function whenReady() {
    if (userInfo && contentLoaded && dataReady && !initialRun) {
        initialRun = true;
        await renderUnread();
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    contentLoaded = true;
    await whenReady();
    if (await isAuthenticated()){
        await renderUnread();
        // Keep the header message badge live on non-Messages pages.
        connectHeaderNotifSocket();
    }

//const data = await fetchUserId();
//const userId = data.id;
//const wsUrl = `ws://127.0.0.1:8000/ws/messaging/?user_id=${userId}`;
//socket = new WebSocket(wsUrl);




//socket.onopen = (event) => {
//    console.log("✅ Connected to WebSocket");
//};

//socket.onmessage = (event) => {
//const data = JSON.parse(event.data);
//if (data.type === 'send_notification') {
//    const notificationData = data.data;
 //   console.log("New notification received:", notificationData);
   // renderItem(notificationData);
//}


//};

//socket.onclose = (event) => {
    //console.log("❌ WebSocket connection closed", event);
    //setTimeout(() => {
               // this.connnectWS;
          //  }, 3000);
//};

//socket.onerror = (event) => {
//console.error("WebSocket error:", error);
//};

});

document.addEventListener("data-ready", async () => {
    dataReady = true;
    console.log("userInfo:", userInfo);
    await whenReady();
    
});