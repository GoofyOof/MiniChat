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

const messagesContainer =
    document.getElementById("messages");

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

        const newMessages =
            messages.filter(function(message) {

                return message.id > lastMessageId;

            });


        const emptyChat =
            messagesContainer.querySelector(".empty-chat");

        if (emptyChat) {
            emptyChat.remove();
        }


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

    return document.body.dataset.userId || "";

}


// -----------------------------------------
// MELDINGSVARSEL
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
            body: message
        }
    );

}


// -----------------------------------------
// LIVE BRUKERSØK
// -----------------------------------------

const usernameSearch =
    document.getElementById("username-search");

const userResults =
    document.getElementById("user-results");


if (usernameSearch && userResults) {

    let searchTimeout;


    usernameSearch.addEventListener(
        "input",
        function() {

            clearTimeout(searchTimeout);

            const search =
                usernameSearch.value.trim();


            userResults.innerHTML = "";


            if (search.length === 0) {
                return;
            }


            searchTimeout = setTimeout(
                searchUsers,
                200
            );

        }
    );


    async function searchUsers() {

        const search =
            usernameSearch.value.trim();


        if (search.length === 0) {
            return;
        }


        const messages =
            document.getElementById("messages");


        if (!messages) {
            return;
        }


        const groupId =
            messages.dataset.groupId;


        try {

            const response =
                await fetch(
                    `/search_users/${groupId}?q=${encodeURIComponent(search)}`
                );


            if (!response.ok) {
                return;
            }


            const data =
                await response.json();


            userResults.innerHTML = "";


            if (data.users.length === 0) {

                const noResults =
                    document.createElement("div");

                noResults.className =
                    "no-user-results";

                noResults.textContent =
                    "Ingen brukere funnet";

                userResults.appendChild(
                    noResults
                );

                return;

            }


            data.users.forEach(function(user) {

                const userElement =
                    document.createElement("button");

                userElement.type = "button";

                userElement.className =
                    "user-result";


                const avatar =
                    document.createElement("div");

                avatar.className =
                    "user-result-avatar";

                avatar.textContent =
                    user.username
                        .charAt(0)
                        .toUpperCase();


                const name =
                    document.createElement("span");

                name.textContent =
                    user.username;


                userElement.appendChild(avatar);
                userElement.appendChild(name);


                userElement.addEventListener(
                    "click",
                    function() {

                        usernameSearch.value =
                            user.username;

                        userResults.innerHTML =
                            "";

                    }
                );


                userResults.appendChild(
                    userElement
                );

            });


        } catch (error) {

            console.log(
                "Kunne ikke søke etter brukere:",
                error
            );

        }

    }

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