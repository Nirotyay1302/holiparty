// Countdown Timer (only runs on pages with countdown elements)
function updateCountdown() {
    const daysEl = document.getElementById('days');
    const hoursEl = document.getElementById('hours');
    const minutesEl = document.getElementById('minutes');
    const secondsEl = document.getElementById('seconds');
    if (!daysEl || !hoursEl || !minutesEl || !secondsEl) return;

    const eventDate = new Date('February 28, 2026 23:59:59').getTime(); // Last date of registration
    const now = new Date().getTime();
    const distance = eventDate - now;

    if (distance > 0) {
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        daysEl.innerText = days.toString().padStart(2, '0');
        hoursEl.innerText = hours.toString().padStart(2, '0');
        minutesEl.innerText = minutes.toString().padStart(2, '0');
        secondsEl.innerText = seconds.toString().padStart(2, '0');
    } else {
        daysEl.innerText = '00';
        hoursEl.innerText = '00';
        minutesEl.innerText = '00';
        secondsEl.innerText = '00';
    }
}

// Update countdown every second (only if countdown exists)
if (document.getElementById('days')) {
    setInterval(updateCountdown, 1000);
    updateCountdown(); // Initial call
}

// Add any additional JavaScript here
