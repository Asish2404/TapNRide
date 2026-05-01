const editBtn =
    document.getElementById(
        "editBtn"
    );

const saveBtn =
    document.getElementById(
        "saveBtn"
    );

const imageGroup =
    document.getElementById(
        "imageUploadGroup"
    );

const card =
    editBtn.closest(
        ".cards"
    );

const profileBtn =
    document.querySelector(
        ".profile-btn"
    );

const dropdown =
    document.querySelector(
        ".dropdown-menu"
    );

const profilePic =
    document.getElementById(
        "profile-pic"
    );

const inputFile =
    document.getElementById(
        "input-file"
    );

const status =
    document.getElementById(
        "systemStatus"
    );

const statusText =
    document.getElementById(
        "statusText"
    );


/* dropdown */
if (profileBtn && dropdown) {

    profileBtn.addEventListener(
        "click",
        function (e) {

            e.stopPropagation();

            const visible =
                getComputedStyle(dropdown)
                    .display !== "none";

            dropdown.style.display =
                visible ? "none" : "flex";

        });

    dropdown.addEventListener(
        "click",
        function (e) {
            e.stopPropagation();
        });

    document.addEventListener(
        "click",
        function () {
            dropdown.style.display = "none";
        });

}



/* edit mode */
if (editBtn) {

    editBtn.addEventListener(
        "click",
        () => {

            document
                .querySelectorAll(".editable")
                .forEach(input => {
                    input.removeAttribute(
                        "readonly"
                    );
                });

            saveBtn.style.display =
                "inline-block";

            editBtn.style.display =
                "none";

            card.classList.add(
                "edit-mode"
            );

            imageGroup.style.display =
                "block";

        });

}



/* image preview */
if (inputFile && profilePic) {

    inputFile.addEventListener(
        "change",
        () => {

            const file =
                inputFile.files[0];

            if (file) {
                profilePic.src =
                    URL.createObjectURL(file);

                document.querySelector(
                    ".custom-file span"
                ).innerText = file.name;
            }
            else {
                document.querySelector(
                    ".custom-file span"
                ).innerText =
                    "Choose Image";
            }

        });

}


/* status */
function setStatus(type, text) {
    status.className =
        "status " + type;

    statusText.innerText = text;
}

setInterval(() => {

    const states = [
        ["active", "System Active • All routes operational"],
        ["warning", "Minor delays detected"],
        ["offline", "System Offline"]
    ];

    const random =
        states[
        Math.floor(
            Math.random() * states.length
        )
        ];

    setStatus(
        random[0],
        random[1]
    );

}, 4000);



function showPopup(message) {
    const popup =
        document.getElementById(
            "popup"
        );

    const msg =
        document.getElementById(
            "popup-message"
        );

    msg.innerText = message;
    popup.style.display = "flex";
}

function closePopup() {
    document.getElementById(
        "popup"
    ).style.display = "none";
}

const popupOk =
    document.getElementById(
        "popupOK"
    );

if (popupOk) {
    popupOk.addEventListener(
        "click",
        closePopup
    );
}


window.addEventListener(
    "DOMContentLoaded",
    () => {
        if (window.profileError) {
            showPopup(
                window.profileError
            );
        }
    });


if (window.history.replaceState) {
    window.history.replaceState(
        null,
        null,
        window.location.href
    );
}

/* HAMBURGER */
function toggleMenu() {
    document
        .getElementById(
            "mobileMenu"
        )
        .classList.toggle(
            "show-menu"
        );
}