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
        function (e) {

            e.stopPropagation();

            dropdown.style.display =
                dropdown.style.display === "block"
                    ? "none"
                    : "block";

        });

    document.addEventListener(
        "click",
        function () {
            dropdown.style.display = "none";
        });

}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        const cardField =
            document.querySelector(
                "input[name='card_id']"
            );

        const fromField =
            document.querySelector(
                "input[name='Starting_place']"
            );

        const toField =
            document.querySelector(
                "input[name='Ending_place']"
            );

        const fareField =
            document.querySelector(
                "input[name='fare']"
            );
        cardField.addEventListener(
            "blur",
            async () => {

                let cardId =
                    cardField.value;

                if (cardId) {

                    let res =
                        await fetch(
                            `/get_active_ride?card_id=${cardId}`
                        );

                    let data =
                        await res.json();

                    fromField.value =
                        data.from_stop || "";

                }

            }
        );
        toField.addEventListener(
            "blur",
            async () => {

                let cardId =
                    cardField.value;

                let toStop =
                    toField.value;

                if (cardId && toStop) {

                    let res =
                        await fetch(
                            `/calculate_fare?card_id=${cardId}&to_stop=${toStop}`
                        );

                    let data =
                        await res.json();

                    fareField.value =
                        data.fare || "";

                }

            }
        );

    });



const nav =
    document.querySelector(
        ".top-nav"
    );

nav.addEventListener(
    "mousemove",
    (e) => {

        const rect =
            nav.getBoundingClientRect();

        const x =
            ((e.clientX - rect.left)
                / rect.width) * 100;

        const y =
            ((e.clientY - rect.top)
                / rect.height) * 100;

        nav.style.setProperty(
            "--x",
            x + "%"
        );

        nav.style.setProperty(
            "--y",
            y + "%"
        );

    }
);


function toggleMenu() {

    document
        .getElementById(
            "mobileMenu"
        )
        .classList.toggle(
            "show-menu"
        );
}