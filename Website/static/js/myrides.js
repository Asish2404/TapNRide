// --- Profile dropdown ---
const btn = document.getElementById("profileBtn");
const dropdown = document.getElementById("dropdown");

if (btn) {
  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    dropdown.style.display =
      dropdown.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", function () {
    dropdown.style.display = "none";
  });
}

// --- Navbar hover effect ---
const nav = document.querySelector(".top-nav");
if (nav) {
  nav.addEventListener("mousemove", (e) => {
    const rect = nav.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    nav.style.setProperty("--x", x + "%");
    nav.style.setProperty("--y", y + "%");
  });
}

// --- Mobile menu toggle ---
function toggleMenu() {
  document.getElementById("mobileMenu").classList.toggle("show-menu");
}

// --- My Rides data fetch ---
async function loadData() {
  const cardId = document.getElementById("userCardId").value; // inject from backend
  const res = await fetch(`/api/myrides/${cardId}`);
  const data = await res.json();

  // Rides
  const ridesDiv = document.getElementById("rides");
  
  ridesDiv.innerHTML = "";
  data.rides.forEach((r) => {
    const rideDate = new Date(r.ride_time).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
    const rideTime = new Date(r.ride_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    ridesDiv.innerHTML += `
      <div class="card">
        <h4>Ride</h4>
        <p>${r.from_stop} → ${r.to_stop}</p>
        <p>Fare: ₹${r.fare}</p>
        <p class="date">Date: ${rideDate}</p>
        <p class="time">Time: ${rideTime}</p>
        <p>Bus No: ${r.bus_no}</p>
      </div>`;
  });

  // Penalties
  const penaltiesDiv = document.getElementById("penalties");
  penaltiesDiv.innerHTML = "";
  data.penalties.forEach((p) => {
    const transactionDate = new Date(p.transaction_time).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
    const transactionTime = new Date(p.transaction_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    penaltiesDiv.innerHTML += `
      <div class="card penalty">
        <h4>Penalty</h4>
        <p>Reason: ${p.description}</p>
        <p>Amount: ₹${p.amount}</p>
        <p class="date">Date: ${transactionDate}</p>
        <p class="time">Time: ${transactionTime}</p>
        <p>Bus No: ${p.bus_no}</p>
      </div>`;
  });
}

// --- Tabs toggle ---
function showSection(id) {
  document.getElementById("rides").style.display =
    id === "rides" ? "flex" : "none";
  document.getElementById("penalties").style.display =
    id === "penalties" ? "flex" : "none";
}

// Load data on page ready
document.addEventListener("DOMContentLoaded", loadData);
