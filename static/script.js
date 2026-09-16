// =========================================
// SKRIV MELDING
// =========================================

const messageInput =
    document.querySelector(".message-box input[name='content']");

if (messageInput) {

    messageInput.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                event.preventDefault();

                messageInput.closest("form").submit();

            }

        }
    );

}


// =========================================
// GRUPPEVINDU
// =========================================

function openGroupWindow() {

    const windowElement =
        document.getElementById("group-window");

    if (windowElement) {
        windowElement.style.display = "flex";
    }

}


function closeGroupWindow() {

    const windowElement =
        document.getElementById("group-window");

    if (windowElement) {
        windowElement.style.display = "none";
    }

}


// =========================================
// MEDLEMSVINDU
// =========================================

function openMemberWindow() {

    const windowElement =
        document.getElementById("member-window");

    if (!windowElement) {
        return;
    }

    windowElement.style.display = "flex";

    const searchInput =
        document.getElementById("username-search");

    if (searchInput) {

        searchInput.value = "";
        searchInput.focus();

    }

    const results =
        document.getElementById("user-results");

    if (results) {
        results.innerHTML = "";
    }

}


function closeMemberWindow() {

    const windowElement =
        document.getElementById("member-window");

    if (windowElement) {
        windowElement.style.display = "none";
    }

}


// =========================================
// VARSLER
// =========================================

async function enableNotifications() {

    if (!("Notification" in window)) {

        alert(
            "Nettleseren din støtter ikke varsler."
        );

        return;
    }

    const permission =
        await Notification.requestPermission();

    if (permission === "granted") {

        new Notification(
            "MiniChat",
            {
                body: "Varsler er nå aktivert! 🔔"
            }
        );

        localStorage.setItem(
            "minichat_notifications",
            "enabled"
        );

    } else {

        alert(
            "Du må tillate varsler i nettleseren."
        );

    }

}


// =========================================
// CHAT
// =========================================

const messagesContainer =
    document.getElementById("messages");

let lastMessageId = 0;


if (messagesContainer) {

    const existingMessages =
        messagesContainer.querySelectorAll(
            "[data-message-id]"
        );

    existingMessages.forEach(
        function(message) {

            const id =
                parseInt(
                    message.dataset.messageId
                );

            if (
                !isNaN(id) &&
                id > lastMessageId
            ) {
                lastMessageId = id;
            }

        }
    );

}


// =========================================
// BRUKER-ID
// =========================================

function getCurrentUserId() {

    return document.body.dataset.userId || "";

}


// =========================================
// OPPDATER MELDINGER
// =========================================

async function updateMessages() {

    if (!messagesContainer) {
        return;
    }

    const groupId =
        messagesContainer.dataset.groupId;

    if (!groupId) {
        return;
    }

    try {

        const response =
            await fetch(
                `/messages/${groupId}`
            );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        const messages =
            data.messages || [];


        // =====================================
        // OPPDATER EKSISTERENDE MELDINGER
        // =====================================

        messages.forEach(
            function(message) {

                const existing =
                    messagesContainer.querySelector(
                        `[data-message-id="${message.id}"]`
                    );

                if (!existing) {
                    return;
                }


                const content =
                    existing.querySelector(
                        ".message-content"
                    );

                if (content) {

                    content.textContent =
                        message.content;

                }


                // Redigert-label

                let editedLabel =
                    existing.querySelector(
                        ".edited-label"
                    );


                if (
                    message.edited &&
                    !editedLabel
                ) {

                    editedLabel =
                        document.createElement("small");

                    editedLabel.className =
                        "edited-label";

                    editedLabel.textContent =
                        "redigert";


                    const time =
                        existing.querySelector(
                            ".message-time"
                        );


                    if (time) {

                        existing.insertBefore(
                            editedLabel,
                            time
                        );

                    } else {

                        existing.appendChild(
                            editedLabel
                        );

                    }

                }

            }
        );


        // =====================================
        // NYE MELDINGER
        // =====================================

        const newMessages =
            messages.filter(
                function(message) {

                    return message.id > lastMessageId;

                }
            );


        if (newMessages.length === 0) {
            return;
        }


        const emptyChat =
            messagesContainer.querySelector(
                ".empty-chat"
            );

        if (emptyChat) {
            emptyChat.remove();
        }


        newMessages.forEach(
            function(message) {

                const messageElement =
                    document.createElement("div");

                messageElement.className =
                    "message";

                messageElement.dataset.messageId =
                    message.id;


                // ---------------------------------
                // TOPP
                // ---------------------------------

                const messageTop =
                    document.createElement("div");

                messageTop.className =
                    "message-top";


                const username =
                    document.createElement("strong");

                username.textContent =
                    message.username;


                messageTop.appendChild(
                    username
                );


                // ---------------------------------
                // KNAPPER
                // ---------------------------------

                if (
                    String(message.user_id) ===
                    String(getCurrentUserId())
                ) {

                    const actions =
                        document.createElement("div");

                    actions.className =
                        "message-actions";


                    // Rediger

                    const editButton =
                        document.createElement("button");

                    editButton.type =
                        "button";

                    editButton.className =
                        "message-menu-button";

                    editButton.dataset.editMessage =
                        message.id;

                    editButton.title =
                        "Rediger melding";

                    editButton.textContent =
                        "✏️";


                    editButton.addEventListener(
                        "click",
                        function() {

                            startEditMessage(
                                message.id
                            );

                        }
                    );


                    // Slett

                    const deleteButton =
                        document.createElement("button");

                    deleteButton.type =
                        "button";

                    deleteButton.className =
                        "message-menu-button delete-message-button";

                    deleteButton.dataset.deleteMessage =
                        message.id;

                    deleteButton.title =
                        "Slett melding";

                    deleteButton.textContent =
                        "🗑️";


                    deleteButton.addEventListener(
                        "click",
                        function() {

                            deleteMessage(
                                message.id
                            );

                        }
                    );


                    actions.appendChild(
                        editButton
                    );

                    actions.appendChild(
                        deleteButton
                    );


                    messageTop.appendChild(
                        actions
                    );

                }


                messageElement.appendChild(
                    messageTop
                );


                // ---------------------------------
                // INNHOLD
                // ---------------------------------

                const content =
                    document.createElement("p");

                content.className =
                    "message-content";

                content.textContent =
                    message.content;


                messageElement.appendChild(
                    content
                );


                // ---------------------------------
                // REDIGERT
                // ---------------------------------

                if (message.edited) {

                    const editedLabel =
                        document.createElement("small");

                    editedLabel.className =
                        "edited-label";

                    editedLabel.textContent =
                        "redigert";

                    messageElement.appendChild(
                        editedLabel
                    );

                }


                // ---------------------------------
                // TID
                // ---------------------------------

                const time =
                    document.createElement("small");

                time.className =
                    "message-time";

                time.textContent =
                    message.created_at;


                messageElement.appendChild(
                    time
                );


                messagesContainer.appendChild(
                    messageElement
                );


                // ---------------------------------
                // VARSEL
                // ---------------------------------

                if (
                    String(message.user_id) !==
                    String(getCurrentUserId())
                ) {

                    showMessageNotification(
                        message.username,
                        message.content
                    );

                }

            }
        );


        lastMessageId =
            newMessages[
                newMessages.length - 1
            ].id;


        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;


    } catch (error) {

        console.log(
            "Kunne ikke hente meldinger:",
            error
        );

    }

}


// =========================================
// REDIGER MELDING
// =========================================

async function startEditMessage(messageId) {

    if (!messagesContainer) {
        return;
    }

    const messageElement =
        messagesContainer.querySelector(
            `[data-message-id="${messageId}"]`
        );

    if (!messageElement) {
        return;
    }


    const contentElement =
        messageElement.querySelector(
            ".message-content"
        );

    if (!contentElement) {
        return;
    }


    if (
        messageElement.querySelector(
            ".edit-message-box"
        )
    ) {
        return;
    }


    const oldContent =
        contentElement.textContent;


    contentElement.style.display =
        "none";


    const editBox =
        document.createElement("div");

    editBox.className =
        "edit-message-box";


    const input =
        document.createElement("input");

    input.type =
        "text";

    input.className =
        "edit-message-input";

    input.value =
        oldContent;

    input.autocomplete =
        "off";


    const saveButton =
        document.createElement("button");

    saveButton.type =
        "button";

    saveButton.className =
        "edit-message-save";

    saveButton.textContent =
        "Lagre";


    const cancelButton =
        document.createElement("button");

    cancelButton.type =
        "button";

    cancelButton.className =
        "edit-message-cancel";

    cancelButton.textContent =
        "Avbryt";


    editBox.appendChild(
        input
    );

    editBox.appendChild(
        saveButton
    );

    editBox.appendChild(
        cancelButton
    );


    contentElement.parentNode.insertBefore(
        editBox,
        contentElement.nextSibling
    );


    input.focus();
    input.select();


    function cancelEdit() {

        editBox.remove();

        contentElement.style.display =
            "";

    }


    async function saveEdit() {

        const newContent =
            input.value.trim();


        if (newContent === "") {

            alert(
                "Meldingen kan ikke være tom."
            );

            return;

        }


        saveButton.disabled =
            true;


        try {

            const response =
                await fetch(
                    `/edit_message/${messageId}`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            content: newContent
                        })
                    }
                );


            const data =
                await response.json();


            if (
                !response.ok ||
                !data.success
            ) {

                alert(
                    data.error ||
                    "Kunne ikke redigere meldingen."
                );

                saveButton.disabled =
                    false;

                return;

            }


            contentElement.textContent =
                data.content;

            contentElement.style.display =
                "";


            editBox.remove();


            let editedLabel =
                messageElement.querySelector(
                    ".edited-label"
                );


            if (!editedLabel) {

                editedLabel =
                    document.createElement("small");

                editedLabel.className =
                    "edited-label";

                editedLabel.textContent =
                    "redigert";


                const time =
                    messageElement.querySelector(
                        ".message-time"
                    );


                if (time) {

                    messageElement.insertBefore(
                        editedLabel,
                        time
                    );

                } else {

                    messageElement.appendChild(
                        editedLabel
                    );

                }

            }


        } catch (error) {

            console.log(
                "Kunne ikke redigere melding:",
                error
            );

            alert(
                "Noe gikk galt."
            );

            saveButton.disabled =
                false;

        }

    }


    cancelButton.addEventListener(
        "click",
        cancelEdit
    );


    saveButton.addEventListener(
        "click",
        saveEdit
    );


    input.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Escape") {

                event.preventDefault();

                cancelEdit();

            }


            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                saveEdit();

            }

        }
    );

}


// =========================================
// SLETT MELDING
// =========================================

async function deleteMessage(messageId) {

    const confirmed =
        confirm(
            "Er du sikker på at du vil slette denne meldingen?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `/delete_message/${messageId}`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            alert(
                data.error ||
                "Kunne ikke slette meldingen."
            );

            return;

        }


        const messageElement =
            messagesContainer.querySelector(
                `[data-message-id="${messageId}"]`
            );


        if (messageElement) {

            messageElement.remove();

        }


    } catch (error) {

        console.log(
            "Kunne ikke slette melding:",
            error
        );

        alert(
            "Noe gikk galt."
        );

    }

}


// =========================================
// KOBLE TIL KNAPPER SOM ALLEREDE FINNES
// =========================================

document.querySelectorAll(
    "[data-edit-message]"
).forEach(
    function(button) {

        button.addEventListener(
            "click",
            function() {

                const messageId =
                    button.dataset.editMessage;

                startEditMessage(
                    messageId
                );

            }
        );

    }
);


document.querySelectorAll(
    "[data-delete-message]"
).forEach(
    function(button) {

        button.addEventListener(
            "click",
            function() {

                const messageId =
                    button.dataset.deleteMessage;

                deleteMessage(
                    messageId
                );

            }
        );

    }
);


// =========================================
// MELDINGSVARSEL
// =========================================

function showMessageNotification(
    username,
    message
) {

    if (!("Notification" in window)) {
        return;
    }

    if (
        Notification.permission !==
        "granted"
    ) {
        return;
    }

    new Notification(
        "Ny melding fra " + username,
        {
            body: message
        }
    );

}


// =========================================
// LIVE BRUKERSØK
// =========================================

const usernameSearch =
    document.getElementById(
        "username-search"
    );

const userResults =
    document.getElementById(
        "user-results"
    );


if (
    usernameSearch &&
    userResults
) {

    let searchTimeout;


    usernameSearch.addEventListener(
        "input",
        function() {

            clearTimeout(
                searchTimeout
            );


            const search =
                usernameSearch.value.trim();


            userResults.innerHTML =
                "";


            if (search.length === 0) {
                return;
            }


            searchTimeout =
                setTimeout(
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
            document.getElementById(
                "messages"
            );


        if (!messages) {
            return;
        }


        const groupId =
            messages.dataset.groupId;


        if (!groupId) {
            return;
        }


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


            userResults.innerHTML =
                "";


            if (
                !data.users ||
                data.users.length === 0
            ) {

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


            data.users.forEach(
                function(user) {

                    const userElement =
                        document.createElement(
                            "button"
                        );

                    userElement.type =
                        "button";

                    userElement.className =
                        "user-result";


                    const avatar =
                        document.createElement(
                            "div"
                        );

                    avatar.className =
                        "user-result-avatar";

                    avatar.textContent =
                        user.username
                            .charAt(0)
                            .toUpperCase();


                    const name =
                        document.createElement(
                            "span"
                        );

                    name.textContent =
                        user.username;


                    userElement.appendChild(
                        avatar
                    );

                    userElement.appendChild(
                        name
                    );


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

                }
            );


        } catch (error) {

            console.log(
                "Kunne ikke søke etter brukere:",
                error
            );

        }

    }

}


// =========================================
// AUTO-OPPDATERING
// =========================================

if (messagesContainer) {

    setInterval(
        updateMessages,
        2000
    );

}