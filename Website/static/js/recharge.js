const btn =
    document.getElementById(
        "profileBtn"
    );

const dropdown =
    document.getElementById(
        "dropdown"
    );

if (btn) {
    btn.addEventListener(
        "click",
        (e) => {
            e.stopPropagation();

            dropdown.style.display =
                dropdown.style.display === "block"
                    ? "none"
                    : "block";
        });

    document.addEventListener(
        "click",
        () => {
            dropdown.style.display = "none";
        });
}

/* slider sync */

let slider =
    document.getElementById(
        "slider"
    );

let amountInput =
    document.getElementById(
        "amount"
    );

slider.oninput = () => {
    amountInput.value =
        slider.value;
}

amountInput.oninput = () => {
    slider.value =
        amountInput.value;
}

/* quick amount */

function setAmount(val) {

    amountInput.value = val;

    slider.value = val;
}

/* validation */

function validateRecharge() {

    let enteredCard =
        document.querySelector(
            "input[name='card_id']"
        ).value.trim();

    let amount =
        parseInt(
            document.getElementById(
                "amount"
            ).value
        );

    if (
        !enteredCard ||
        !amount ||
        isNaN(amount)
    ) {

        showPopup(
            "Please enter valid inputs"
        );

        return false;
    }

    if (amount < 50) {

        showPopup(
            "Minimum recharge ₹50"
        );

        return false;
    }

    if (amount > 5000) {

        showPopup(
            "Max limit ₹5000"
        );

        return false;
    }

    return true;
}

function showMessage(text, type) {

    let msg =
        document.getElementById(
            "message"
        );

    msg.innerText = text;

    msg.className = type;
}

function showSuccessAnimation() {

    let card =
        document.querySelector(
            ".glass-card"
        );

    card.style.transform =
        "scale(1.05)";

    setTimeout(
        () => card.style.transform = "scale(1)",
        300
    );
}

function showPopup(message) {

    document.getElementById(
        "popupMessage"
    ).innerText = message;

    document.getElementById(
        "popupModal"
    ).classList.remove(
        "hidden"
    );
}

function closePopup() {

    document.getElementById(
        "popupModal"
    ).classList.add(
        "hidden"
    );

    if (amountInput) {
        amountInput.value = "";
    }

    if (slider) {
        slider.value = 50;
    }
}

window.addEventListener(
    "DOMContentLoaded",
    () => {

        if (window.popupError) {
            showPopup(
                window.popupError
            );
        }

        if (window.popupSuccess) {
            showPopup(
                window.popupSuccess
            );
        }

    }
);

if (window.history.replaceState) {

    window.history.replaceState(
        null,
        null,
        window.location.href
    );
}

function toggleMenu() {

    document
        .getElementById(
            "mobileMenu"
        )
        .classList.toggle(
            "show-menu"
        );
}

/* ---------------- PAYMENT ---------------- */

function openPaymentPopup() {

    let amount = parseInt(
        document.getElementById(
            "amount"
        ).value
    );

    if (!amount || amount < 50) {

        showPopup(
            "Enter a valid amount"
        );

        return;
    }

    document
        .getElementById(
            "paymentPopup"
        )
        .classList.remove(
            "hidden"
        );
}

function closePaymentPopup() {

    document
        .getElementById(
            "paymentPopup"
        )
        .classList.add(
            "hidden"
        );
}

/* ---------------- UPI ---------------- */

function openUPIPopup() {

    closePaymentPopup();

    document
        .getElementById(
            "upiPopup"
        )
        .classList.remove(
            "hidden"
        );
}

function closeUPIPopup() {

    document
        .getElementById(
            "upiPopup"
        )
        .classList.add(
            "hidden"
        );
}

function processUPI() {

    let upiId =
        document.getElementById(
            "upiId"
        ).value.trim();

    if (
        !upiId ||
        !upiId.includes("@")
    ) {

        showPopup(
            "Enter a valid UPI ID"
        );

        return;
    }

    closeUPIPopup();

    showPopup(
        "Processing Payment..."
    );

    setTimeout(() => {

        let txnId =
            "TXN" +
            Math.floor(
                100000 +
                Math.random() * 900000
            );

        showPopup(
            "Payment Successful!\n\nTransaction ID: "
            + txnId
        );

        setTimeout(() => {

            if (
                validateRecharge()
            ) {

                document
                    .querySelector(
                        "form"
                    )
                    .submit();
            }

        }, 1500);

    }, 2000);
}

/* ---------------- CARD ---------------- */

function openCardPopup() {

    closePaymentPopup();

    showPopup(
        "Card Payment Coming Soon"
    );
}

/* ---------------- NET BANKING ---------------- */

function openNetBankingPopup() {

    closePaymentPopup();

    showPopup(
        "Net Banking Coming Soon"
    );
}