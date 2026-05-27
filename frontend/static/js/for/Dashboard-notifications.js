


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
        <a href="/dashboard/dashboard-messages/?conv_id=${convId}&sender_id=${senderId}">
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
        

        li.innerHTML = `
        <a href="/dashboard/dashboard-messages/?conv_id=${convId}&sender_id=${senderId}">
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
        

        const notificationCount = messageList.children.length;
        const notCount = document.getElementById("notification-count");
        if (notCount) {
            notCount.textContent = notificationCount;
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
}

const markAllReadBtn = document.querySelector('#mark-all-read');

if (markAllReadBtn && userInfo) {
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

                // ✅ Alert success
                alert("All notifications marked as read!");

                // ✅ Re-render notifications list to reflect changes
                await renderUnread();

                // ✅ Update notification count badge to 0
                const countElement = document.getElementById("notification-count");
                if (countElement) {
                    countElement.textContent = "0";
                    countElement.style.display = "none"; // Hide badge if empty
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