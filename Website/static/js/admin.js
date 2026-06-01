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

// new addition
// FILTER LOGIC
const applyBtn = document.getElementById("applyFilters");
const resetBtn = document.getElementById("resetFilters");

applyBtn.addEventListener("click", () => {
  const cardId = document.getElementById("filterCardID").value;
  const day = document.getElementById("filterDay").value;
  const date = document.getElementById("filterDate").value;
  const month = document.getElementById("filterMonth").value;
  const year = document.getElementById("filterYear").value;
  const busNo = document.getElementById("filterBusNo").value;
  const deviceId = document.getElementById("filterDeviceID").value;
  const fromDate = document.getElementById("fromDate").value;
  const toDate = document.getElementById("toDate").value;

  // Example: send filters to backend via query params
  let query = "/admin?";
  if (cardId) query += `card_id=${cardId}&`;
  if (day) query += `day=${day}&`;
  if (date) query += `date=${date}&`;
  if (month) query += `month=${month}&`;
  if (year) query += `year=${year}&`;
  if (busNo) query += `bus_no=${busNo}&`;
  if (deviceId) query += `device_id=${deviceId}&`;
  if (fromDate && toDate) query += `from_date=${fromDate}&to_date=${toDate}&`;
  window.location.href = query.endsWith("&") ? query.slice(0, -1) : query;
});

resetBtn.addEventListener("click", () => {
  window.location.href = "/admin?all=true"; // reload all transactions
});
