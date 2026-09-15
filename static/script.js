const input = document.querySelector(".message-box input");

if (input) {

    input.addEventListener("keydown", function(event) {

        if (event.key === "Enter") {

            event.preventDefault();

            input.closest("form").submit();

        }

    });

}


function openGroupWindow() {

    document.getElementById("group-window").style.display = "flex";

}


function closeGroupWindow() {

    document.getElementById("group-window").style.display = "none";

}


function openMemberWindow() {

    document.getElementById("member-window").style.display = "flex";

}


function closeMemberWindow() {

    document.getElementById("member-window").style.display = "none";

}