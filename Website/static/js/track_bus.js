'use strict';

/* ═══════════════════════════════════════════════════
   CONFIG
   ═══════════════════════════════════════════════════ */
const CONFIG = {
    MOVEMENT_SPEED: 600000,
    BUSES_JSON_PATH: '/static/data/buses.json',
    DEFAULT_BUS_ID: 'DN43'
};

/* ═══════════════════════════════════════════════════
   STOP COORDINATES (Kolkata)
   ═══════════════════════════════════════════════════ */
const STOP_COORDS = {
    'Barasat': [22.7215, 88.4798],
    'Madhyamgram': [22.6984, 88.4627],
    'Airport': [22.6547, 88.4469],
    'Chinar Park': [22.6205, 88.4717],
    'Technopolis': [22.6057, 88.4699],
    'Sector V': [22.5958, 88.4311],
    'Karunamoyee': [22.5880, 88.4180],
    'Ultadanga': [22.6010, 88.3940],
    'New Town': [22.5790, 88.4790],
    'Eco Park': [22.5820, 88.4900],
    'Eco Space': [22.5830, 88.4850],
    'Sealdah': [22.5667, 88.3711],
    'Howrah': [22.5851, 88.3387],
    'Esplanade': [22.5645, 88.3521],
    'Lake Town': [22.5850, 88.3920],
    'Shyambazar': [22.5940, 88.3660],
    'Hridaypur': [22.7100, 88.4500],
    'Rajarhat': [22.5850, 88.4850],
    'Salt Lake': [22.5800, 88.4100],
    'Salt Lake Stadium': [22.5716, 88.4100]
};

/* ═══════════════════════════════════════════════════
   STATE
   ═══════════════════════════════════════════════════ */
const State = {
    busId: null,
    busData: null,
    busesRegistry: [],
    leafletMap: null,
    busMarker: null,
    stopMarkers: [],
    routePolyline: null,
    moveTimer: null,
    currentStopIndex: 0
};

/* ═══════════════════════════════════════════════════
   LOAD BUSES REGISTRY
   ═══════════════════════════════════════════════════ */
async function loadBusesRegistry() {
    try {
        const res = await fetch(CONFIG.BUSES_JSON_PATH);
        if (!res.ok) throw new Error();
        State.busesRegistry = await res.json();
    } catch {
        console.warn('[Registry] Using built-in fallback');
        State.busesRegistry = [
            { bus_no: 'DN43', route: ['Barasat', 'Madhyamgram', 'Airport', 'Chinar Park', 'Technopolis', 'Sector V'], eta: '18 mins' },
            { bus_no: 'DN47', route: ['Barasat', 'Madhyamgram', 'Airport', 'Chinar Park', 'Karunamoyee'], eta: '24 mins' },
            { bus_no: 'S12D', route: ['Barasat', 'Madhyamgram', 'Ultadanga', 'Karunamoyee', 'Sector V'], eta: '30 mins' },
            { bus_no: 'AC12', route: ['Barasat', 'Airport', 'New Town', 'Eco Park', 'Sector V'], eta: '20 mins' },
            { bus_no: 'AC47', route: ['Barasat', 'Airport', 'New Town', 'Karunamoyee'], eta: '15 mins' },
            { bus_no: 'VS1', route: ['Barasat', 'Madhyamgram', 'Airport', 'Salt Lake Stadium', 'Sector V'], eta: '25 mins' },
            { bus_no: '215A', route: ['Barasat', 'Hridaypur', 'Madhyamgram', 'Airport', 'Ultadanga', 'Howrah'], eta: '35 mins' },
            { bus_no: '211', route: ['Barasat', 'Madhyamgram', 'Airport', 'Lake Town', 'Shyambazar', 'Esplanade'], eta: '40 mins' },
            { bus_no: '78/1', route: ['Barasat', 'Airport', 'Ultadanga', 'Sealdah'], eta: '28 mins' },
            { bus_no: 'L238', route: ['Barasat', 'Airport', 'New Town', 'Eco Space', 'Sector V'], eta: '22 mins' },
            { bus_no: 'L20B', route: ['Barasat', 'Madhyamgram', 'Airport', 'Chinar Park', 'New Town'], eta: '26 mins' },
            { bus_no: 'KB16', route: ['Barasat', 'Airport', 'Rajarhat', 'New Town', 'Sector V'], eta: '19 mins' },
            { bus_no: 'KB22', route: ['Barasat', 'Airport', 'Eco Park', 'Karunamoyee'], eta: '23 mins' },
            { bus_no: 'ST6', route: ['Barasat', 'Madhyamgram', 'Airport', 'Salt Lake', 'Karunamoyee'], eta: '17 mins' },
            { bus_no: 'WBTC1', route: ['Barasat', 'Airport', 'New Town', 'Eco Space', 'Sector V', 'Karunamoyee'], eta: '14 mins' }
        ];
    }
    console.log(`[Registry] ${State.busesRegistry.length} buses loaded`);
}

/* ═══════════════════════════════════════════════════
   READ BUS ID FROM URL
   This is how other pages send the bus to track:
   /track_bus?bus_id=DN43
   ═══════════════════════════════════════════════════ */
function getBusIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('bus_id') || params.get('bus') || null;
}

/* Update URL without reload so bookmarking works */
function updateURL(busId) {
    const url = new URL(window.location);
    url.searchParams.set('bus_id', busId);
    window.history.replaceState({}, '', url);
}

/* ═══════════════════════════════════════════════════
   BUILD BUS DATA FROM REGISTRY
   ═══════════════════════════════════════════════════ */
function getBusData(busNo) {
    const entry = State.busesRegistry.find(
        b => b.bus_no.toUpperCase() === busNo.toUpperCase()
    );
    if (!entry) return null;

    const origin = entry.route[0];
    const destination = entry.route[entry.route.length - 1];
    const isAC = busNo.toUpperCase().startsWith('AC');
    const etaNum = parseInt(entry.eta) || 20;

    // Calculate total route distance (approximate)
    let totalDist = 0;
    for (let i = 1; i < entry.route.length; i++) {
        const c1 = STOP_COORDS[entry.route[i - 1]];
        const c2 = STOP_COORDS[entry.route[i]];
        if (c1 && c2) totalDist += haversine(c1, c2);
    }

    return {
        bus_number: entry.bus_no,
        registration: `WB01-${isAC ? 'AC' : 'TX'}-${hashCode(busNo)}`,
        route_name: `${origin} ↔ ${destination}`,
        bus_type: isAC ? 'AC' : 'Non-AC',
        bus_category: isAC ? 'AC Express' : 'Ordinary',
        driver: randomDriver(),
        contact: `+91 ${90000 + hashCode(busNo)} ${10000 + hashCode(busNo)}`,
        status: 'Running',
        stops: entry.route,
        origin,
        destination,
        eta: entry.eta,
        eta_minutes: etaNum,
        total_distance: totalDist.toFixed(1),
        speed: Math.floor(22 + Math.random() * 18),
        traffic: ['Smooth', 'Moderate', 'Heavy'][Math.floor(Math.random() * 3)],
        delay: Math.floor(Math.random() * 8),
        capacity: isAC ? 45 : 60,
        filled: Math.floor(25 + Math.random() * 25),
        health_score: Math.floor(78 + Math.random() * 20),
        fuel: Math.floor(50 + Math.random() * 40)
    };
}

/* ═══════════════════════════════════════════════════
   RENDER ENGINE
   ═══════════════════════════════════════════════════ */
const Render = {

    /* ── MASTER RENDER ── */
    all(busNo) {
        const data = getBusData(busNo);
        if (!data) {
            showToast(`Bus "${busNo}" not found in registry. Try: DN43, AC12, 211`, 'error');
            showSuggestions(busNo);
            return;
        }

        State.busId = busNo;
        State.busData = data;
        State.currentStopIndex = 0;

        // Update browser URL so refresh keeps this bus
        updateURL(busNo);

        // Update search input to show current bus
        const input = document.getElementById('bus-search-input');
        if (input) input.value = busNo;

        // Render all sections
        this.busInfo(data);
        this.liveTracking(data, 0);
        this.occupancy(data);
        this.timeline(data.stops, 0);
        this.predictions(data);
        this.health(data);
        this.performance(data);
        this.map(data.stops);

        // Update page title
        document.title = `${data.bus_number} — Live Tracker`;

        showToast(`🚌 Now tracking Bus ${data.bus_number}`, 'success');
    },

    /* ── BUS INFO CARD ── */
    busInfo(data) {
        setText('bi-number', data.bus_number);
        setText('bi-route', data.route_name);
        setText('bi-routename', data.route_name);
        setText('bi-regnum', data.registration);
        setText('bi-driver', data.driver);
        setText('bi-contact', data.contact);
        setText('bi-status', data.status);
        setText('bi-type-chip', data.bus_type === 'AC' ? '❄ AC' : 'Non-AC');
        setText('last-updated', new Date().toLocaleTimeString());

        // Status color
        const statusEl = document.getElementById('bi-status');
        if (statusEl) statusEl.style.color = data.status === 'Running' ? 'var(--green-bright)' : 'var(--amber)';

        // Update chips
        const chipsContainer = document.querySelector('.bus-type-chips');
        if (chipsContainer) {
            chipsContainer.innerHTML = `
                <span class="chip chip-ac">${data.bus_category}</span>
                <span class="chip chip-running">🟢 ${data.status}</span>
                <span class="chip chip-express">Route ${data.bus_number}</span>
            `;
        }
    },

    /* ── LIVE TRACKING CARD ── */
    liveTracking(data, stopIndex) {
        const stops = data.stops;
        const current = stops[stopIndex] || stops[0];
        const next = stops[stopIndex + 1] || 'Destination';
        const remaining = stops.length - stopIndex - 1;
        const distLeft = (remaining * parseFloat(data.total_distance) / stops.length).toFixed(1);
        const etaLeft = Math.max(1, Math.round(remaining * data.eta_minutes / stops.length));
        const coord = STOP_COORDS[current] || [22.5726, 88.3639];

        setText('lt-location', current);
        setText('lt-nextstop', next);
        setText('lt-eta', `${etaLeft} min`);
        setText('lt-eta-next', `${Math.max(1, Math.round(etaLeft / remaining || 1))} min`);
        setText('lt-destination', data.destination);
        setText('lt-distance', `${distLeft} km`);
        setText('lt-speed', data.speed + Math.floor(Math.random() * 6 - 3));
        setText('lt-traffic', data.traffic);
        setText('lt-updated', new Date().toLocaleTimeString());
        setText('lt-coords', `${coord[0].toFixed(4)}°N, ${coord[1].toFixed(4)}°E`);
        setText('map-coords', `${coord[0].toFixed(4)}°N, ${coord[1].toFixed(4)}°E`);

        // Delay
        const delayEl = document.getElementById('lt-delay');
        if (delayEl) {
            if (data.delay > 0) {
                delayEl.textContent = `${data.delay} min late`;
                delayEl.style.color = 'var(--amber)';
            } else {
                delayEl.textContent = 'On Time';
                delayEl.style.color = 'var(--green-bright)';
            }
        }

        // Traffic color
        const trafficEl = document.getElementById('lt-traffic');
        if (trafficEl) {
            trafficEl.style.color =
                data.traffic === 'Heavy' ? 'var(--red)' :
                    data.traffic === 'Moderate' ? 'var(--amber)' : 'var(--green-bright)';
        }

        // Alert message
        const alertEl = document.querySelector('.tracking-alert:not(.success)');
        if (alertEl) {
            const alertSpan = alertEl.querySelector('span');
            if (alertSpan) {
                if (data.traffic === 'Heavy') {
                    alertSpan.textContent = `Heavy traffic detected near ${next} — expect significant delays`;
                } else if (data.traffic === 'Moderate') {
                    alertSpan.textContent = `Moderate traffic near ${next} — expect minor delays`;
                } else {
                    alertSpan.textContent = `Traffic is smooth — bus running on schedule to ${data.destination}`;
                }
            }
        }
    },

    /* ── OCCUPANCY ── */
    occupancy(data) {
        const pct = Math.round((data.filled / data.capacity) * 100);
        const available = data.capacity - data.filled;
        const predicted = Math.min(100, pct + Math.floor(Math.random() * 15));

        setText('occ-filled', data.filled);
        setText('occ-available', available);
        setText('occ-total', data.capacity);
        setText('occ-percent', `${pct}%`);
        setText('occ-ring-pct', `${pct}%`);
        setText('occ-predicted', `${predicted}%`);

        // Ring animation
        const ring = document.getElementById('occ-ring-fill');
        if (ring) ring.style.strokeDashoffset = 283 - (pct / 100) * 283;

        // Bars
        setWidth('occ-bar-filled', `${pct}%`);
        setWidth('crowd-bar-fill', `${pct}%`);

        // Crowd level
        const crowdEl = document.getElementById('occ-crowd');
        if (crowdEl) {
            if (pct >= 85) { crowdEl.textContent = 'Crowded'; crowdEl.style.color = 'var(--red)'; }
            else if (pct >= 60) { crowdEl.textContent = 'Moderate'; crowdEl.style.color = 'var(--amber)'; }
            else { crowdEl.textContent = 'Available'; crowdEl.style.color = 'var(--green-bright)'; }
        }
    },

    /* ── ROUTE TIMELINE ── */
    timeline(stops, currentIdx) {
        const container = document.getElementById('route-timeline');
        if (!container) return;

        // Update stop count badge
        const badge = document.querySelector('.timeline-card .card-badge');
        if (badge) badge.textContent = `${stops.length} STOPS`;

        container.innerHTML = stops.map((stop, i) => {
            let statusClass, icon, pillHTML = '';

            if (i < currentIdx) {
                statusClass = 'tl-done';
                icon = '<i class="fas fa-check" style="font-size:0.6rem;color:var(--green)"></i>';
                pillHTML = '<span class="tl-eta-pill pill-arrived">Arrived</span>';
            } else if (i === currentIdx) {
                statusClass = 'tl-current';
                icon = '<i class="fas fa-bus" style="font-size:0.65rem;color:var(--accent)"></i>';
                pillHTML = '<span class="tl-eta-pill pill-current">HERE</span>';
            } else {
                statusClass = 'tl-upcoming';
                icon = `<span style="font-size:0.6rem;color:var(--text-muted)">${i + 1}</span>`;
                const perStopMinutes =
                    Math.round(
                        (State.busData?.eta_minutes || 90) /
                        (stops.length - 1)
                    );

                const mins =
                    (i - currentIdx) * perStopMinutes;
                pillHTML = `<span class="tl-eta-pill pill-eta">~${mins} min</span>`;
            }

            // const baseHour = 8;
            // const totalMins = baseHour * 60 + i * 12;
            // const hh = String(Math.floor(totalMins / 60)).padStart(2, '0');
            // const mm = String(totalMins % 60).padStart(2, '0');

            const now = new Date();

            const totalJourneyMinutes =
                State.busData?.eta_minutes || 90;

            const perStopMinutes =
                Math.round(
                    totalJourneyMinutes /
                    (stops.length - 1)
                );

            const stopTime = new Date(
                now.getTime() +
                (i * perStopMinutes * 60000)
            );

            const hh = String(
                stopTime.getHours()
            ).padStart(2, "0");

            const mm = String(
                stopTime.getMinutes()
            ).padStart(2, "0");

            // const hh = String(stopTime.getHours()).padStart(2, "0");
            // const mm = String(stopTime.getMinutes()).padStart(2, "0");

            return `
                <div class="timeline-item ${statusClass}" id="tl-stop-${i}">
                    <div class="timeline-left">
                        <div class="tl-node">${icon}</div>
                        ${i < stops.length - 1 ? '<div class="tl-line"></div>' : ''}
                    </div>
                    <div class="tl-content">
                        <div class="tl-stop-name">${stop}</div>
                        <div class="tl-meta">
                            <span class="tl-time">${hh}:${mm}</span>
                            ${pillHTML}
                        </div>
                    </div>
                </div>`;
        }).join('');
    },

    /* ── AI PREDICTIONS ── */
    predictions(data) {
        const preds = {
            'pred-occ': Math.min(99, Math.round((data.filled / data.capacity) * 100) + 10),
            'pred-delay': data.delay > 3 ? 65 : 30,
            'pred-traffic': data.traffic === 'Heavy' ? 80 : data.traffic === 'Moderate' ? 55 : 25,
            'pred-confidence': data.traffic === 'Smooth' ? 92 : 78
        };

        Object.entries(preds).forEach(([id, val]) => {
            setText(`${id}-val`, `${val}%`);
            const bar = document.getElementById(`${id}-bar`);
            if (bar) setTimeout(() => bar.style.width = `${val}%`, 400);
        });
    },

    /* ── BUS HEALTH ── */
    health(data) {
        setText('health-score', data.health_score);
        setText('health-fuel', `${data.fuel}%`);
        const fuelBar = document.getElementById('health-fuel-bar');
        if (fuelBar) setTimeout(() => fuelBar.style.width = `${data.fuel}%`, 400);

        const scoreEl = document.getElementById('health-score');
        if (scoreEl) {
            scoreEl.style.color = data.health_score >= 85 ? 'var(--green-bright)' :
                data.health_score >= 65 ? 'var(--amber)' : 'var(--red)';
        }
    },

    /* ── ROUTE PERFORMANCE ── */
    performance(data) {
        setText('sc-efficiency', `${Math.floor(75 + Math.random() * 20)}%`);
        setText('sc-fuel', `${(8 + Math.random() * 6).toFixed(1)}L`);
    },

    /* ═══════════════════════════════════════════════
       MAP + BUS MOVEMENT
       ═══════════════════════════════════════════════ */
    map(stopNames) {
        const coords = stopNames
            .map(name => STOP_COORDS[name])
            .filter(Boolean);

        if (coords.length < 2) {
            console.warn('[Map] Not enough coordinates');
            return;
        }

        // Hide decorative map, show Leaflet
        const deco = document.getElementById('decorative-map');
        const mapEl = document.getElementById('leaflet-map');
        if (deco) deco.style.display = 'none';
        if (mapEl) mapEl.style.display = 'block';

        // Initialize map once
        if (!State.leafletMap) {
            State.leafletMap = L.map('leaflet-map', {
                zoomControl: false,
                attributionControl: false
            }).setView(coords[0], 12);

            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                maxZoom: 18
            }).addTo(State.leafletMap);

            L.control.zoom({ position: 'topright' }).addTo(State.leafletMap);
        }

        // Clear previous layers
        if (State.routePolyline) State.leafletMap.removeLayer(State.routePolyline);
        if (State.busMarker) State.leafletMap.removeLayer(State.busMarker);
        State.stopMarkers.forEach(m => State.leafletMap.removeLayer(m));
        State.stopMarkers = [];

        // Draw route polyline
        State.routePolyline = L.polyline(coords, {
            color: '#22d3ee',
            weight: 4,
            opacity: 0.7,
            dashArray: '8, 6'
        }).addTo(State.leafletMap);

        // Add stop markers
        stopNames.forEach((name, i) => {
            const c = STOP_COORDS[name];
            if (!c) return;

            const isFirst = i === 0;
            const isLast = i === stopNames.length - 1;

            const stopIcon = L.divIcon({
                className: 'stop-icon',
                html: `<div style="
                    width:${isFirst || isLast ? 14 : 10}px;
                    height:${isFirst || isLast ? 14 : 10}px;
                    border-radius:50%;
                    background:${isFirst ? '#22c55e' : isLast ? '#f87171' : 'rgba(56,189,248,0.5)'};
                    border:2px solid ${isFirst ? '#22c55e' : isLast ? '#f87171' : '#22d3ee'};
                    box-shadow:0 0 8px ${isFirst ? 'rgba(34,197,94,0.6)' : isLast ? 'rgba(248,113,113,0.6)' : 'rgba(34,211,238,0.4)'};
                "></div>`,
                iconSize: [14, 14],
                iconAnchor: [7, 7]
            });

            const marker = L.marker(c, { icon: stopIcon })
                .bindTooltip(name, {
                    permanent: isFirst || isLast,
                    direction: 'top',
                    className: 'stop-tooltip-leaflet'
                })
                .addTo(State.leafletMap);

            State.stopMarkers.push(marker);
        });

        // Bus marker
        const busIcon = L.divIcon({
            className: 'leaflet-bus-marker',
            html: `<div style="
                background: linear-gradient(135deg, #22d3ee, #0ea5e9);
                width: 36px; height: 36px;
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 18px;
                border: 2px solid rgba(255,255,255,0.4);
                box-shadow: 0 0 20px rgba(34,211,238,0.7), 0 0 40px rgba(34,211,238,0.3);
            ">🚌</div>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });

        State.busMarker = L.marker(coords[0], { icon: busIcon })
            .bindPopup(`<b>Bus ${State.busData.bus_number}</b><br>${stopNames[0]}`)
            .addTo(State.leafletMap);

        // Fit map to route
        State.leafletMap.fitBounds(State.routePolyline.getBounds(), { padding: [40, 40] });

        // Start movement
        this.startMovement(coords, stopNames);
    },

    /* ── BUS MOVEMENT ANIMATION ── */
    startMovement(coords, stopNames) {
        if (State.moveTimer) clearInterval(State.moveTimer);
        State.currentStopIndex = 0;

        State.moveTimer = setInterval(() => {
            State.currentStopIndex++;

            // Loop back to start for continuous demo
            if (State.currentStopIndex >= coords.length) {
                State.currentStopIndex = 0;
            }

            const pos = coords[State.currentStopIndex];

            // Move bus marker smoothly
            State.busMarker.setLatLng(pos);
            State.busMarker.setPopupContent(
                `<b>Bus ${State.busData.bus_number}</b><br>${stopNames[State.currentStopIndex]}`
            );

            // Update ALL live tracking text
            this.liveTracking(State.busData, State.currentStopIndex);

            // Update timeline highlight
            this.timeline(State.busData.stops, State.currentStopIndex);

        }, CONFIG.MOVEMENT_SPEED);
    }
};

/* ═══════════════════════════════════════════════════
   SEARCH WITH SUGGESTIONS
   ═══════════════════════════════════════════════════ */
function setupSearch() {
    const input = document.getElementById('bus-search-input');
    const btn = document.getElementById('bus-search-btn');
    if (!input || !btn) return;

    // Create suggestions dropdown
    const sugBox = document.createElement('div');
    sugBox.id = 'search-suggestions';
    sugBox.style.cssText = `
        position:absolute; top:100%; left:0; right:0;
        background:rgba(8,15,35,0.97);
        border:1px solid rgba(34,211,238,0.2);
        border-radius:0 0 16px 16px;
        max-height:300px; overflow-y:auto;
        display:none; z-index:100;
        backdrop-filter:blur(12px);
    `;
    input.parentElement.style.position = 'relative';
    input.parentElement.appendChild(sugBox);

    // Live search as you type
    input.addEventListener('input', () => {
        const val = input.value.trim().toUpperCase();
        if (val.length < 1) { sugBox.style.display = 'none'; return; }

        const matches = State.busesRegistry.filter(b =>
            b.bus_no.toUpperCase().includes(val) ||
            b.route.some(s => s.toUpperCase().includes(val))
        ).slice(0, 8);

        if (matches.length === 0) {
            sugBox.style.display = 'none';
            return;
        }

        sugBox.innerHTML = matches.map(b => `
            <div class="search-suggestion" data-bus="${b.bus_no}" style="
                padding:12px 18px;
                cursor:pointer;
                border-bottom:1px solid rgba(255,255,255,0.05);
                transition:0.2s;
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <div>
                    <div style="font-weight:700;color:var(--accent);font-size:14px">
                        🚌 ${b.bus_no}
                    </div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:2px">
                        ${b.route[0]} → ${b.route[b.route.length - 1]}
                    </div>
                </div>
                <div style="
                    font-size:11px;
                    color:var(--green-bright);
                    background:rgba(34,197,94,0.1);
                    padding:3px 10px;
                    border-radius:999px;
                    border:1px solid rgba(34,197,94,0.2);
                ">ETA ${b.eta}</div>
            </div>
        `).join('');

        sugBox.style.display = 'block';

        // Click suggestion
        sugBox.querySelectorAll('.search-suggestion').forEach(el => {
            el.addEventListener('click', () => {
                input.value = el.dataset.bus;
                sugBox.style.display = 'none';
                trackBus(el.dataset.bus);
            });
            el.addEventListener('mouseenter', () => el.style.background = 'rgba(34,211,238,0.08)');
            el.addEventListener('mouseleave', () => el.style.background = 'transparent');
        });
    });

    // Hide suggestions on outside click
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !sugBox.contains(e.target)) {
            sugBox.style.display = 'none';
        }
    });

    // Search button click
    btn.addEventListener('click', () => {
        sugBox.style.display = 'none';
        trackBus(input.value.trim());
    });

    // Enter key
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sugBox.style.display = 'none';
            trackBus(input.value.trim());
        }
    });
}

function trackBus(busNo) {
    if (!busNo) return showToast('Please enter a bus number', 'error');
    Render.all(busNo);
}

/* Show suggestions when bus not found */
function showSuggestions(query) {
    const similar = State.busesRegistry
        .filter(b => b.bus_no.toUpperCase().includes(query.charAt(0)))
        .slice(0, 3);

    if (similar.length > 0) {
        const names = similar.map(b => b.bus_no).join(', ');
        showToast(`Did you mean: ${names}?`, 'info');
    }
}

/* ═══════════════════════════════════════════════════
   SPARKLINE CHARTS
   ═══════════════════════════════════════════════════ */
function renderSparkline(svgId, data, color) {
    const svg = document.getElementById(svgId);
    if (!svg) return;
    const w = svg.clientWidth || 120;
    const h = svg.clientHeight || 36;
    const max = Math.max(...data), min = Math.min(...data);
    const range = max - min || 1;

    const pts = data.map((v, i) => {
        const x = (i / (data.length - 1)) * w;
        const y = h - ((v - min) / range) * (h - 4) - 2;
        return `${x},${y}`;
    }).join(' ');

    svg.innerHTML = `
        <defs>
            <linearGradient id="g_${svgId}" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="${color}" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
            </linearGradient>
        </defs>
        <polygon points="0,${h} ${pts} ${w},${h}" fill="url(#g_${svgId})"/>
        <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
    `;
}

/* ═══════════════════════════════════════════════════
   PASSENGER ACTION BUTTONS
   ═══════════════════════════════════════════════════ */
function setupActions() {
    const actions = {
        'action-notify': () => showToast('🔔 You will be notified when bus arrives!', 'success'),
        'action-share': () => {
            const text = `Bus ${State.busData?.bus_number} is heading to ${State.busData?.destination}. ETA: ${State.busData?.eta}`;
            if (navigator.share) navigator.share({ title: 'Bus Location', text });
            else { navigator.clipboard?.writeText(text); showToast('📋 Copied to clipboard!', 'success'); }
        },
        'action-save': () => {
            const saved = JSON.parse(localStorage.getItem('saved_buses') || '[]');
            if (!saved.includes(State.busId)) {
                saved.push(State.busId);
                localStorage.setItem('saved_buses', JSON.stringify(saved));
                showToast('✅ Bus saved to favorites!', 'success');
            } else showToast('Already saved', 'info');
        },
        'action-call': () => {
            if (State.busData?.contact) window.location.href = `tel:${State.busData.contact.replace(/\s/g, '')}`;
        },
        'action-emergency': () => {
            if (confirm('Contact Emergency Helpline?\n📞 1800-345-5670')) {
                window.location.href = 'tel:18003455670';
            }
        },
        'refresh-btn': () => { if (State.busId) Render.all(State.busId); },
        'map-center': () => {
            if (State.leafletMap && State.busMarker) {
                State.leafletMap.setView(State.busMarker.getLatLng(), 15);
                showToast('🎯 Centered on bus', 'info');
            }
        },
        'map-refresh': () => {
            showToast('📍 Location refreshed', 'info');
        }
    };

    Object.entries(actions).forEach(([id, fn]) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    });
}

/* ═══════════════════════════════════════════════════
   UTILITIES
   ═══════════════════════════════════════════════════ */
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function setWidth(id, val) {
    const el = document.getElementById(id);
    if (el) setTimeout(() => el.style.width = val, 300);
}

function haversine([lat1, lon1], [lat2, lon2]) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = ((hash << 5) - hash) + str.charCodeAt(i);
    return Math.abs(hash) % 9000 + 1000;
}

function randomDriver() {
    const names = ['Subhash Mondal', 'Rajesh Das', 'Amit Sarkar', 'Tapan Ghosh', 'Ravi Shaw', 'Bikash Roy', 'Sunil Mandal'];
    return names[Math.floor(Math.random() * names.length)];
}

function showToast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'} ${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

/* ═══════════════════════════════════════════════════
   INIT — THE ENTRY POINT
   ═══════════════════════════════════════════════════ */
async function init() {
    // 1. Load registry first
    await loadBusesRegistry();

    // 2. Check URL for bus_id (from search page or bookmark)
    const busFromURL = getBusIdFromURL();
    const busId = busFromURL || CONFIG.DEFAULT_BUS_ID;

    // 3. Pre-fill search input
    const input = document.getElementById('bus-search-input');
    if (input) input.value = busId;

    // 4. Setup search with live suggestions
    setupSearch();

    // 5. Setup action buttons
    setupActions();

    // 6. Setup hamburger menu
    document.getElementById('nav-hamburger')?.addEventListener('click', () => {
        document.getElementById('nav-links')?.classList.toggle('open');
    });

    // 7. Load and render the bus
    Render.all(busId);

    // 8. Render sparklines
    setTimeout(() => {
        renderSparkline('spark-passengers', [2300, 2600, 2800, 3000, 3124], '#38bdf8');
        renderSparkline('spark-trips', [14, 16, 18, 20, 21], '#10b981');
        renderSparkline('spark-distance', [420, 490, 540, 580, 618], '#a78bfa');
        renderSparkline('spark-delay', [5.8, 5.2, 4.6, 4.2, 3.8], '#f59e0b');
    }, 600);

    console.log(`%c[SmartCity Tracker] Initialized — Bus: ${busId}`, 'color:#22d3ee;font-weight:bold');
}

document.addEventListener('DOMContentLoaded', init);

/* ═══════════════════════════════════════════════════
   PUBLIC API (for other pages to use)
   ═══════════════════════════════════════════════════ */
window.SmartBusTracker = {
    track: (id) => Render.all(id),
    getState: () => ({ ...State }),
    getBuses: () => State.busesRegistry
};