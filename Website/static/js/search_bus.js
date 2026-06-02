let buses = [];

const sourceSelect = document.getElementById("source");
const destinationSelect = document.getElementById("destination");

async function loadBusData() {
    try {
        const response = await fetch("/static/data/buses.json");

        if (!response.ok) {
            throw new Error("Failed to load bus data");
        }

        buses = await response.json();

        const stops = new Set();

        buses.forEach(bus => {
            bus.route.forEach(stop => {
                stops.add(stop);
            });
        });

        sourceSelect.innerHTML =
            '<option value="">Select Source</option>';

        destinationSelect.innerHTML =
            '<option value="">Select Destination</option>';

        stops.forEach(stop => {
            sourceSelect.innerHTML +=
                `<option value="${stop}">${stop}</option>`;

            destinationSelect.innerHTML +=
                `<option value="${stop}">${stop}</option>`;
        });

    } catch (error) {
        console.error("Error loading bus data:", error);

        document.getElementById("busResults").innerHTML = `
            <div class="bus-card">
                <h3>Error</h3>
                <p>Could not load bus data.</p>
            </div>
        `;
    }
}

function swapStops() {

    const swapBtn = document.getElementById("swapBtn");
    swapBtn.classList.remove("swap-rotate");
    void swapBtn.offsetWidth;
    swapBtn.classList.add("swap-rotate");
    let temp = sourceSelect.value;
    sourceSelect.value = destinationSelect.value;
    destinationSelect.value = temp;
}

function searchBus() {

    const source = sourceSelect.value;
    const destination = destinationSelect.value;

    if (!source || !destination) {
        alert("Please select source and destination.");
        return;
    }

    if (source === destination) {
        alert("Source and destination cannot be the same.");
        return;
    }

    let html = "";

    buses.forEach(bus => {

        if (bus.route.includes(source) && bus.route.includes(destination)) {
            let routeDisplay;
            if (bus.route.indexOf(source) < bus.route.indexOf(destination)) {
                routeDisplay = bus.route.join(" → ");
            }
            else {
                routeDisplay = [...bus.route].reverse().join(" → ");
            }
            html += `
            <div class="bus-card">

                <div class="bus-header">

                    <h3>
                        🚌 ${bus.bus_no}
                    </h3>

                    <span class="eta">
                        ${bus.eta}
                    </span>

                </div>

                <p>
                    <strong>Journey:</strong>
                    ${source} → ${destination}
                </p>

                <br>

                <p>
                    <strong>Route:</strong>
                    ${routeDisplay}
                </p>

                    <button
                        class="track-btn"
                        onclick="trackBus('${bus.bus_no}')">
                        Track Bus
                    </button>
                </div>
            `;
        }
    });

    if (html === "") {
        html = `
            <div class="bus-card">
                <h3>No buses found</h3>
                <p>No buses are available on this route.</p>
            </div>
        `;
    }

    document.getElementById("busResults").innerHTML = html;
}

window.onload = loadBusData;

function trackBus(busNo) {

    window.location.href =
        `/track-bus?bus=${busNo}`;

}