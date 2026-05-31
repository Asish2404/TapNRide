const btn =
    document.getElementById("profileBtn");

const dropdown =
    document.getElementById("dropdown");


if (btn && dropdown) {

    btn.addEventListener(
        "click",
        function (e) {

            e.stopPropagation();

            const isVisible =
                getComputedStyle(dropdown)
                    .display !== "none";

            dropdown.style.display =
                isVisible ? "none" : "flex";

        });

    document.addEventListener(
        "click",
        function () {
            dropdown.style.display = "none";
        });

}



/* theme */
function ThemeChange() {
    document.body.classList.toggle(
        "light-bg"
    );

    document.body.classList.toggle(
        "gradient-bg"
    );
}



/* hamburger */
function toggleMenu() {
    document
        .getElementById("mobileMenu")
        .classList.toggle(
            "show-menu"
        );
}
/* =========================
   CHATBOT OPEN / CLOSE
========================= */

const chatToggle =
    document.getElementById(
        "chatToggle"
    );

const chatWindow =
    document.getElementById(
        "chatWindow"
    );

if (chatToggle) {

    chatToggle.addEventListener(
        "click",
        function () {

            if (
                chatWindow.style.display
                === "flex"
            ) {

                chatWindow.style.display =
                    "none";

            }
            else {

                chatWindow.style.display =
                    "flex";

            }

        }
    );

}


/* =========================
   SEND MESSAGE TO GEMINI
========================= */

async function sendMessage() {

    let input =
        document.getElementById(
            "chatInput"
        );

    let msg =
        input.value.trim();

    if (!msg) {
        return;
    }

    let chatBody =
        document.getElementById(
            "chatBody"
        );

    // User message
    chatBody.innerHTML += `
        <div class="user-message">
            ${msg}
        </div>
    `;

    input.value = "";

    chatBody.scrollTop =
        chatBody.scrollHeight;

    let formData =
        new FormData();

    formData.append(
        "message",
        msg
    );

    try {

        let response =
            await fetch(
                "/chat",
                {
                    method: "POST",
                    body: formData
                }
            );

        let data =
            await response.json();

        // Gemini reply
        chatBody.innerHTML += `
            <div class="bot-message">
                ${data.reply}
            </div>
        `;

        chatBody.scrollTop =
            chatBody.scrollHeight;

    }

    catch (error) {

        chatBody.innerHTML += `
            <div class="bot-message">
                Unable to connect.
            </div>
        `;

    }

}
function sendSuggestion(question){

    document.getElementById(
        "chatInput"
    ).value = question;

    sendMessage();

}

/* =========================
   ENTER KEY SUPPORT
========================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const chatInput =
            document.getElementById(
                "chatInput"
            );

        if (chatInput) {

            chatInput.addEventListener(
                "keypress",
                function (e) {

                    if (
                        e.key === "Enter"
                    ) {

                        sendMessage();

                    }

                }
            );

        }

    }
);