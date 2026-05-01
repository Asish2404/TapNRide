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