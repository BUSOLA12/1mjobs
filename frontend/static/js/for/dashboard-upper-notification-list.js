
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
        const response = await fetch(`/api/users/currentuser/`);
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




const upperNotificationList = document.querySelector('.upper-notification');



async function loadUnreadloadUnreadUpperNotification() {
    try {
        const res = await fetchProtected(`/api/notifications/notification-list/`);
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


async function renderUnreadUpperNotification() {
    const data = await loadUnreadloadUnreadUpperNotification();
    console.log("Notification Data", data);
    
    
    const userId_ = await fetchUserId();
    console.log("User details 2:", userId_);
    const userId = userId_.id;
    
    // Clear old notifications to avoid duplicates
    upperNotificationList.innerHTML = '';

    for (const n of data) {
        //const user_data = await fetchcurrentuserId(n.sender_id);
        //console.log("User details:", user_data);
        const li = document.createElement('li');
        li.className = "notifications-not-read";
        li.dataset.id = n.id;

        
        console.log("Time:", n.timestamp);
        

        li.innerHTML = `
            <a href="{% url 'dashboard_manage_candidates' %}">
                <span class="notification-icon"><i class="icon-material-outline-group"></i></span>
                <span class="notification-text">
                    <strong>${n.message}</strong> <span class="color"></span>
                </span>
            </a>
        `;

        
        upperNotificationList.prepend(li);

        //for counting notification:
        const upperNotificationCount = upperNotificationList.children.length;
        const upperNotCount = document.getElementById("upper-notification-count");
        if (upperNotCount) {
            upperNotCount.textContent = upperNotificationCount;
        }
        

}
}

let contentLoaded1 = false;
let dataReady1 = false;
let initialRun1 = false;
async function whenReady() {
    if (userInfo && contentLoaded1 && dataReady1 && !initialRun1) {
        initialRun1 = true;
        await renderUnreadUpperNotification();
    }
}

const markAllUpperNotificationReadBtn = document.querySelector('.mark-as-read.ripple-effect-dark.upper-not');
console.log("userInfo:", userInfo);
if (userInfo) {
    markAllUpperNotificationReadBtn.addEventListener('click', async function (e) {
        e.preventDefault();

        try {
                await fetchProtected(`/api/notifications/mark-all-notification/`, {method: 'POST'});
                document.querySelectorAll(".notifications-not-read").forEach(li => {
                    li.remove();
                });
                alert("All notifications marked as read.");
        } catch (error) {
            console.error("Error marking all as read:", error);
            alert("Error marking all as read:" + error.message);
        }

    });
}


document.addEventListener('DOMContentLoaded', async function () {
        contentLoaded1 = true;
        await whenReady();

    if (await isAuthenticated()){
        await renderUnreadUpperNotification();
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
    dataReady1 = true;
    console.log("userInfo:", userInfo);
    await whenReady();
    
});