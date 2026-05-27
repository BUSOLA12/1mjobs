
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




const notificationList = document.querySelector('.dashboard-box-list.notifications');

// function renderItem(notificationData) {
//     const li = document.createElement('li');
//     li.dataset.id = notificationData.message_id;
//     li.className = "notifications-not-read";
//     const convId = notificationData.conversation_id;
//     const senderId = notificationData.sender_id;

    

//     li.innerHTML = `
//         <a href="/dashboard/dashboard-messages/?conv_id=${convId}&sender_id=${senderId}">
//             <span class="notification-avatar status-online"><img src="{% static 'images/user-avatar-small-03.jpg' %}" alt=""></span>
//             <div class="notification-text">
//                 <strong>${notificationData.sender}</strong>
//                 <p class="notification-msg-text">${notificationData.message}</p>
//                 <span class="color">${timeAgo(notificationData.timestamp)}</span>
//             </div>
//         </a>
//     `;
//     messageList.prepend(li);
// }


async function loadUnreadNotification() {
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


async function renderUnreadNotification() {
    const data = await loadUnreadNotification();
    console.log("Notification Data", data);
    
    
    const userId_ = await fetchUserId();
    console.log("User details 2:", userId_);
    const userId = userId_.id;
    
    // Clear old notifications to avoid duplicates
    notificationList.innerHTML = '';

    for (const n of data) {
        
        const li = document.createElement('li');
        li.className = "notifications-not-read";
        li.dataset.id = n.id;

        
        //console.log("Time:", n.timestamp);
        

        li.innerHTML = `
            <span class="notification-icon"><i class="icon-material-outline-group"></i></span>
            <span class="notification-text">
            <strong>${n.message}</strong>  <a href="#"></a>
            </span>
            <!-- Buttons -->
            <div class="buttons-to-right">
                <a href="#" class="button ripple-effect ico mark-one" title="Mark as read" data-tippy-placement="left"><i class="icon-feather-check-square"></i></a>
            </div>
        `;

        
        notificationList.prepend(li);



        

    }
    

}


notificationList.addEventListener('click', async function(e) {
    const button = e.target.closest('.button.ripple-effect.ico.mark-one');
    if (!button) return;
    e.preventDefault();

    const li = button.closest('li');
    const currentNotId = li.dataset.id;

    try {
            await fetchProtected(`/api/notifications/mark-one-notification/${currentNotId}/`, {method: 'POST'});
            li.remove();
        } catch (error) {
                console.error("Error marking as read:", error);
                alert("Error marking as read:" + error.message);
            }
});


const markAllNotificationReadBtn = document.querySelector('.mark-as-read.ripple-effect-dark.not-box');
markAllNotificationReadBtn.addEventListener('click', async function (e) {
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



document.addEventListener('DOMContentLoaded', async function () {
await renderUnreadNotification();




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