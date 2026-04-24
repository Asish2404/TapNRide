(function () {
    const root = document.documentElement;
    const themeRoot = document.getElementById('themeRoot');
    const themeToggle = document.getElementById('themeToggle');
    const sunIcon = document.getElementById('sunIcon');
    const moonIcon = document.getElementById('moonIcon');

    // Theme init (persist)
    const storedTheme = localStorage.getItem('smartbus-theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = storedTheme ? storedTheme === 'dark' : prefersDark;
    setTheme(isDark);

    themeToggle.addEventListener('click', () => {
        const nowDark = !root.classList.contains('dark');
        setTheme(nowDark);
        localStorage.setItem('smartbus-theme', nowDark ? 'dark' : 'light');
    });

    function setTheme(dark) {
        if (dark) { root.classList.add('dark'); moonIcon.classList.remove('hidden'); sunIcon.classList.add('hidden'); }
        else { root.classList.remove('dark'); moonIcon.classList.add('hidden'); sunIcon.classList.remove('hidden'); }
    }

    // Tabs
    const loginTab = document.getElementById('loginTab');
    const signupTab = document.getElementById('signupTab');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const goLogin = document.getElementById('goLogin');
    function setActive(tab) {
        if (tab === 'login') {
            loginTab.classList.add('active'); signupTab.classList.remove('active');
            loginForm.classList.remove('hidden'); signupForm.classList.add('hidden');
        } else {
            signupTab.classList.add('active'); loginTab.classList.remove('active');
            signupForm.classList.remove('hidden'); loginForm.classList.add('hidden');
        }
    }
    loginTab.addEventListener('click', () => setActive('login'));
    signupTab.addEventListener('click', () => setActive('signup'));
    goLogin.addEventListener('click', () => setActive('login'));

    // Role chips (login)
    const roleChips = Array.from(document.querySelectorAll('#signupForm .role-chip'));
    let selectedRole = 'passenger';

    const hiddenRole = document.getElementById('hiddenRole');
    const roleText = document.getElementById('roleText');

    // set default
    if (hiddenRole) hiddenRole.value = selectedRole;
    if (roleText) roleText.textContent = "Passenger";

    roleChips.forEach(chip => {
        chip.addEventListener('click', () => {

            roleChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            selectedRole = chip.getAttribute('data-role');

            // update hidden input
            if (hiddenRole) hiddenRole.value = selectedRole;

            // update UI text
            if (roleText) {
                roleText.textContent =
                    selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1);
            }
        });
    });

    // Password eye
    const passInput = document.getElementById('loginPassword');
    const togglePass = document.getElementById('togglePass');
    const eyeOn = document.getElementById('eyeOn');
    const eyeOff = document.getElementById('eyeOff');
    togglePass.addEventListener('click', () => {
        const isText = passInput.type === 'text';
        passInput.type = isText ? 'password' : 'text';
        eyeOn.classList.toggle('hidden'); eyeOff.classList.toggle('hidden');
    });

    // Strength meter
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    passInput.addEventListener('input', () => {
        const v = passInput.value;
        const score = calcStrength(v);
        const pct = [0, 25, 50, 75, 100][score];
        strengthBar.style.width = pct + '%';
        strengthText.textContent = ['Too short', 'Weak', 'Okay', 'Good', 'Strong'][score];
    });
    function calcStrength(v) {
        if (!v || v.length < 8) return 0;
        let s = 1;
        if (v.length >= 8) s++;
        if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++;
        if (/\d/.test(v) && /[^A-Za-z0-9]/.test(v)) s++;
        if (v.length >= 12) s = 4;
        return Math.min(s, 4);
    }


    // Validators
    const emailOrPhoneRe = /^(?:[^\s@]+@[^\s@]+\.[^\s@]+|\+?\d{8,15})$/;
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRe = /^\+?\d{8,15}$/;

    function showErr(el, show) { el.classList.toggle('hidden', !show); }

    // Login submit
    const loginEmail = document.getElementById('loginEmail');
    const remember = document.getElementById('remember');
    const loginSubmit = document.getElementById('loginSubmit');
    loginForm.addEventListener('submit', (e) => {

        let ok = true;

        showErr(document.getElementById('loginEmailErr'), false);
        showErr(document.getElementById('loginPassErr'), false);

        if (!emailOrPhoneRe.test(loginEmail.value.trim())) {
            showErr(document.getElementById('loginEmailErr'), true);
            e.preventDefault();
            return;
        }

        if (passInput.value.length < 8) {
            showErr(document.getElementById('loginPassErr'), true);
            e.preventDefault();
            return;
        }

        // Allow default form behavior to handle valid submission.
    });
    // Sign up
    const suFirstName = document.getElementById('suFirstName');
    const suLastName = document.getElementById('suLastName');
    const suEmail = document.getElementById('suEmail');
    const suPhone = document.getElementById('suPhone');
    const suPass = document.getElementById('suPass');
    const suPass2 = document.getElementById('suPass2');
    const agree = document.getElementById('agree');

    signupForm.addEventListener('submit', (e) => {

        let ok = true;

        showErr(document.getElementById('suFirstNameErr'), false);
        showErr(document.getElementById('suLastNameErr'), false);
        showErr(document.getElementById('suEmailErr'), false);
        showErr(document.getElementById('suPhoneErr'), false);
        showErr(document.getElementById('suPassErr'), false);
        showErr(document.getElementById('suPass2Err'), false);
        showErr(document.getElementById('agreeErr'), false);

        if (!suFirstName.value.trim()) { showErr(document.getElementById('suFirstNameErr'), true); ok = false; }
        if (!suLastName.value.trim()) { showErr(document.getElementById('suLastNameErr'), true); ok = false; }
        if (!emailRe.test(suEmail.value.trim())) { showErr(document.getElementById('suEmailErr'), true); ok = false; }
        if (!phoneRe.test(suPhone.value.trim())) { showErr(document.getElementById('suPhoneErr'), true); ok = false; }
        if (suPass.value.length < 8) { showErr(document.getElementById('suPassErr'), true); ok = false; }
        if (suPass2.value !== suPass.value) { showErr(document.getElementById('suPass2Err'), true); ok = false; }
        if (!agree.checked) { showErr(document.getElementById('agreeErr'), true); ok = false; }

        if (!ok) {
            e.preventDefault();   // ❗ only block if invalid
        }

        // ✅ otherwise allow normal POST /signup
    });

    // Forgot modal
    const forgotBtn = document.getElementById('forgotBtn');
    const forgotModal = document.getElementById('forgotModal');
    const closeForgot = document.getElementById('closeForgot');
    const sendReset = document.getElementById('sendReset');
    const forgotInput = document.getElementById('forgotInput');
    const forgotMsg = document.getElementById('forgotMsg');

    forgotBtn.addEventListener('click', () => { forgotModal.classList.remove('hidden'); setTimeout(() => forgotInput.focus(), 50); });
    closeForgot.addEventListener('click', () => { forgotModal.classList.add('hidden'); forgotMsg.classList.add('hidden'); forgotInput.value = ''; });
    forgotModal.addEventListener('click', (e) => { if (e.target === forgotModal.firstElementChild) { closeForgot.click(); } });
    sendReset.addEventListener('click', async () => {
        forgotMsg.classList.add('hidden');
        if (!emailOrPhoneRe.test(forgotInput.value.trim())) {
            forgotMsg.textContent = 'Please enter a valid email or phone.';
            forgotMsg.className = 'text-center text-sm text-rose-500';
            forgotMsg.classList.remove('hidden'); return;
        }
        const original = sendReset.innerHTML;
        sendReset.disabled = true;
        sendReset.innerHTML = '<svg class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg><span>Sending…</span>';
        await sleep(900);
        sendReset.disabled = false;
        sendReset.innerHTML = original;
        forgotMsg.textContent = 'Reset link sent! Check your inbox/SMS.';
        forgotMsg.className = 'text-center text-sm text-emerald-600 dark:text-emerald-300';
        forgotMsg.classList.remove('hidden');
        setTimeout(() => { closeForgot.click(); toast('Password reset requested.'); }, 900);
    });

    // Toast
    const toastEl = document.getElementById('toast');
    const toastInner = document.getElementById('toastInner');
    let toastTimer;
    function toast(msg) {
        toastInner.textContent = msg;
        toastInner.classList.remove('hidden');
        toastInner.style.transform = 'translateY(-6px)';
        toastInner.style.opacity = '0';
        requestAnimationFrame(() => {
            toastInner.style.transition = 'all .25s ease';
            toastInner.style.transform = 'translateY(0)';
            toastInner.style.opacity = '1';
        });
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toastInner.style.opacity = '0';
            toastInner.style.transform = 'translateY(-6px)';
            setTimeout(() => toastInner.classList.add('hidden'), 250);
        }, 2200);
    }

    const popupModal = document.getElementById('popupModal');
    const popupMessage = document.getElementById('popupMessage');
    const popupOk = document.getElementById('popupOk');

    function showPopup(message, redirectUrl = null) {
        popupMessage.textContent = message;
        popupModal.classList.remove('hidden');

        popupOk.onclick = () => {
            popupModal.classList.add('hidden');

            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        };
    }

    // Helpers
    function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

    // Auto-fill demo (optional). Comment out if not needed.
    // loginEmail.value = "driver@smartbus.app"; passInput.value = "Driver@123"; passInput.dispatchEvent(new Event('input'));

    // Footer year
    document.getElementById('year').textContent = new Date().getFullYear();

    // ✅ Show login error popup if exists
    window.addEventListener("DOMContentLoaded", () => {
    if (window.loginError) {
        showPopup(window.loginError);

        // ✅ REMOVE error from URL after showing once
        const url = new URL(window.location);
        url.searchParams.delete("error");
        window.history.replaceState({}, document.title, url.pathname);
    }
});

})();