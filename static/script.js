const input = document.querySelector(".message-box input");

if (input) {

    input.addEventListener("keydown", function(event) {

        if (event.key === "Enter") {

            event.preventDefault();

            input.closest("form").submit();

        }

    });

}


// -----------------------------------------
// GRUPPEVINDU
// -----------------------------------------

function openGroupWindow() {

    document.getElementById("group-window").style.display = "flex";

}


function closeGroupWindow() {

    document.getElementById("group-window").style.display = "none";

}


// -----------------------------------------
// MEDLEMSVINDU
// -----------------------------------------

function openMemberWindow() {

    document.getElementById("member-window").style.display = "flex";

}


function closeMemberWindow() {

    document.getElementById("member-window").style.display = "none";

}


// -----------------------------------------
// VARSLER
// -----------------------------------------

async function enableNotifications() {

    if (!("Notification" in window)) {

        alert("Nettleseren din støtter ikke varsler.");

        return;

    }

    const permission = await Notification.requestPermission();

    if (permission === "granted") {

        new Notification("MiniChat", {
            body: "Varsler er nå aktivert! 🔔"
        });

        localStorage.setItem(
            "minichat_notifications",
            "enabled"
        );

    } else {

        alert(
            "Du må tillate varsler i nettleseren for å bruke denne funksjonen."
        );

    }

}


// -----------------------------------------
// CHAT-OPPDATERING
// -----------------------------------------

const messagesContainer = document.getElementById("messages");

let lastMessageId = 0;

if (messagesContainer) {

    const existingMessages =
        messagesContainer.querySelectorAll(".message");

    existingMessages.forEach(function(message) {

        const id = parseInt(
            message.dataset.messageId
        );

        if (id > lastMessageId) {

            lastMessageId = id;

        }

    });

}


// -----------------------------------------
// HENT NYE MELDINGER
// -----------------------------------------

async function updateMessages() {

    if (!messagesContainer) {
        return;
    }

    const groupId =
        messagesContainer.dataset.groupId;

    try {

        const response = await fetch(
            `/messages/${groupId}`
        );

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        const messages = data.messages;

        if (messages.length === 0) {
            return;
        }

        const newestMessage =
            messages[messages.length - 1];

        if (newestMessage.id <= lastMessageId) {
            return;
        }


        // Finn alle nye meldinger

        const newMessages =
            messages.filter(function(message) {

                return message.id > lastMessageId;

            });


        // Fjern "Ingen meldinger"

        const emptyChat =
            messagesContainer.querySelector(".empty-chat");

        if (emptyChat) {
            emptyChat.remove();
        }


        // Legg til nye meldinger

        newMessages.forEach(function(message) {

            const messageElement =
                document.createElement("div");

            messageElement.className = "message";

            messageElement.dataset.messageId =
                message.id;


            const username =
                document.createElement("strong");

            username.textContent =
                message.username;


            const content =
                document.createElement("p");

            content.textContent =
                message.content;


            const time =
                document.createElement("small");

            time.textContent =
                message.created_at;


            messageElement.appendChild(username);

            messageElement.appendChild(content);

            messageElement.appendChild(time);


            messagesContainer.appendChild(
                messageElement
            );


            // Varsel hvis meldingen er fra noen andre

            if (
                message.user_id !=
                getCurrentUserId()
            ) {

                showMessageNotification(
                    message.username,
                    message.content
                );

            }

        });


        lastMessageId =
            newestMessage.id;


        // Scroll ned

        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;


    } catch (error) {

        console.log(
            "Kunne ikke hente meldinger:",
            error
        );

    }

}


// -----------------------------------------
// BRUKER-ID
// -----------------------------------------

function getCurrentUserId() {

    const body =
        document.body;

    return body.dataset.userId || "";

}


// -----------------------------------------
// VIS VARSEL
// -----------------------------------------

function showMessageNotification(
    username,
    message
) {

    if (!("Notification" in window)) {
        return;
    }

    if (Notification.permission !== "granted") {
        return;
    }

    new Notification(
        "Ny melding fra " + username,
        {
            body: message,
            icon: "/static/icon.png"
        }
    );

}


// -----------------------------------------
// START AUTO-OPPDATERING
// -----------------------------------------

if (messagesContainer) {

    setInterval(
        updateMessages,
        2000
    );

}