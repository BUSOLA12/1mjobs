document.addEventListener("DOMContentLoaded", function () {
    loadOfferDashboard();

    async function loadOfferDashboard() {
        try {
            loadOffersReceived();
            loadOffersSent();
        } catch (error) {
            console.error("Error loading dashboard:", error);
        }
    }

    // Load Offers Received
    async function loadOffersReceived() {
        const container = document.querySelector("#offers-received-list");
        container.innerHTML = `<li>Loading...</li>`;

        try {
            const response = await fetchProtected("/api/offers/received/", {
            });

            const data = await response.json();
            console.log("Offers Received:", data);
            container.innerHTML = "";
            if (data.unlisted !== null) {
                const noSub = document.querySelector("#no-subscription-message");
                noSub.querySelector("span").innerHTML = `${data.unlisted} offers not shown due to no active subscription.`;
                noSub.style.display = "block";
            }

            if (data.offers.length === 0) {
                container.innerHTML = `<li>No offers received yet.</li>`;
                return;
            }

            data.offers.forEach(offer => {
                const item = `
                    <li>
                        <div class="boxed-list-item">
                            <div class="item-content">
                                <h4>From: ${offer.sender.first_name} ${offer.sender.last_name}</h4>
                                <div class="item-details margin-top-10">
                                    <div class="detail-item"><i class="icon-material-outline-date-range"></i> ${timeSince(offer.created_at)}</div>
                                </div>
                                <div class="item-description">
                                    <p>${offer.message.substring(0, 50)}...</p>
                                </div>
                            </div>
                        </div>

                        <button data-mfp-src="#small-dialog-1" onclick="offerDetailsSetup(${offer.id}, 'received')" class="button gray ripple-effect margin-top-5 mfp-trigger">
                            <i class="icon-material-outline-arrow-right-alt"></i> View Details
                        </button>
                    </li>
                `;
                container.insertAdjacentHTML("beforeend", item);
            });

        } catch (error) {
            container.innerHTML = `<li>Error loading received offers</li>`;
        }
    }

    // Load Offers Sent
    async function loadOffersSent() {
        const container = document.querySelector("#offers-sent-list");
        container.innerHTML = `<li>Loading...</li>`;

        try {
            const response = await fetchProtected("/api/offers/sent/", {
            });

            const data = await response.json();
            console.log("Offers Sent:", data);
            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = `<li>You have not sent any offers yet.</li>`;
                return;
            }

            data.forEach(offer => {
                const item = `
                    <li>
                        <div class="boxed-list-item">
                            <div class="item-content">
                                <h4>To: ${offer.receiver.first_name} ${offer.receiver.last_name}</h4>
                                <div class="item-details margin-top-10">
                                    <div class="detail-item"><i class="icon-material-outline-date-range"></i> ${timeSince(offer.created_at)}</div>
                                </div>
                                <div class="item-description">
                                    <p>${offer.message.substring(0, 50)}...</p>
                                </div>
                            </div>
                        </div>

                        <div class="buttons-to-right">
                            <a href="#" onclick="deleteOffer(${offer.id})"
                                class="button red ripple-effect ico" title="Delete Offer"
                                data-tippy-placement="left">
                                <i class="icon-feather-trash-2"></i>
                            </a>
                        </div>

                        <button data-mfp-src="#small-dialog-1" onclick="offerDetailsSetup(${offer.id}, 'sent')" class="button gray ripple-effect margin-top-5 mfp-trigger">
                            <i class="icon-material-outline-arrow-right-alt"></i> View Details
                        </button>
                    </li>
                `
                container.insertAdjacentHTML("beforeend", item);
            });

        } catch (error) {
            container.innerHTML = `<li>Error loading sent offers</li>`;
        }
    }

});

// Delete Offer
async function deleteOffer(id) {
    if (!confirm("Are you sure you want to delete this offer?")) return;

    try {
        const response = await fetchProtected(`/api/offers/${id}/delete/`, {
            method: "DELETE",
        });

        if (response.status === 204) {
            appendError("Offer deleted.", "success");
            location.reload();
        } else {
            appendError("Cannot delete offer.");
        }

    } catch (error) {
        console.error("Error deleting offer:", error);
        appendError("Error deleting offer.");
    }
}

function offerDetailsSetup(offerId, offerType) {
    loadOfferDetails(offerId);
    async function loadOfferDetails(id) {
        try {
            const response = await fetchProtected(`/api/offers/${id}/`, {
            });

            const data = await response.json();

            buildOfferDetail(data, offerType);
            buildAttachments(data.files);
            if (offerType === "sent") {
                setupMessageButton(data.receiver_id);
            } else {
                setupMessageButton(data.sender_id);
            }

        } catch (err) {
            document.querySelector("#offer-detail-content").innerHTML =
                `<p>Error loading offer details.</p>`;
        }
    }

    // Build the main offer detail box
    function buildOfferDetail(data, offerType = "received") {
        const container = document.querySelector("#offer-detail-content");

        container.innerHTML = `
            <div class="boxed-list-item">
                <div class="item-content">

                    <h3 class="margin-bottom-10">
                    ${offerType === "received" ? "From: " + data.sender.first_name + " " + data.sender.last_name
                                                : "To: " + data.receiver.first_name + " " + data.receiver.last_name}
                    </h3>

                    <div class="item-details margin-top-10">
                        <div class="detail-item">
                            <i class="icon-material-outline-email"></i> ${offerType === "received" ? data.sender.email : data.receiver.email}
                        </div>
                        <div class="detail-item">
                            <i class="icon-material-outline-date-range"></i> ${timeSince(data.created_at)}
                        </div>
                    </div>

                    <div class="item-description margin-top-20">
                        <p>${data.message.replace(/\n/g, "<br>")}</p>
                    </div>

                </div>
            </div>
        `;
    }

    // Build attachments section
    function buildAttachments(files) {
        const box = document.querySelector("#offer-attachments");
        box.innerHTML = "";

        if (!files || files.length === 0) {
            box.innerHTML = `<p>No attachments</p>`;
            return;
        }

        files.forEach((file, index) => {
            const extension = file.file.split(".").pop().toUpperCase();

            const item = `
                <a href="${file.file}" target="_blank" class="attachment-box ripple-effect">
                    <span>${"File-" + (index+1)}</span>
                    <i>${extension}</i>
                </a>
            `;
            box.insertAdjacentHTML("beforeend", item);
        });
    }

    // Send message button setup
    function setupMessageButton(senderId) {
        const button = document.querySelector("#send-message-btn");

        button.href = `/messages/chat/${senderId}/`; 
    }

};