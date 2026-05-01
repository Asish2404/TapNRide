const btn = document.getElementById("profileBtn");
const dropdown = document.getElementById("dropdown");

if (btn) {
    btn.addEventListener("click", function (e) {
        e.stopPropagation();

        dropdown.style.display =
            dropdown.style.display === "block"
                ? "none"
                : "block";
    });

    document.addEventListener("click", function () {
        dropdown.style.display = "none";
    });
}



/* FLOATING HAMBURGER MENU */

const hamburger = document.getElementById("hamburger");
const mobileMenu = document.getElementById("mobileMenu");

hamburger.addEventListener("click", function (e) {
    e.stopPropagation();
    mobileMenu.classList.toggle("show-menu");
});


document.addEventListener("click", function (e) {
    if (
        !mobileMenu.contains(e.target) &&
        !hamburger.contains(e.target)
    ) {
        mobileMenu.classList.remove("show-menu");
    }
});


window.addEventListener("resize", function () {
    if (window.innerWidth > 768) {
        mobileMenu.classList.remove("show-menu");
        hamburger.classList.remove("active");
    }
});