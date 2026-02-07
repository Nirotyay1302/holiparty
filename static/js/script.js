// Countdown Timer (only runs on pages with countdown elements)
function updateCountdown() {
    const daysEl = document.getElementById('days');
    const hoursEl = document.getElementById('hours');
    const minutesEl = document.getElementById('minutes');
    const secondsEl = document.getElementById('seconds');
    if (!daysEl || !hoursEl || !minutesEl || !secondsEl) return;

    const timerEl = document.querySelector('.countdown-timer');
    if (!timerEl) return;

    // Get date from data attribute or fallback to hardcoded
    const dateStr = timerEl.getAttribute('data-event-date') || 'February 28, 2026';
    // Append time to ensure it counts down to end of that day (or start, depending on need. User said "Last Date of Registration", usually implies end of day)
    const eventDate = new Date(dateStr + ' 23:59:59').getTime();
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
// Update countdown every second (only if countdown exists)
if (document.getElementById('days')) {
    setInterval(updateCountdown, 1000);
    updateCountdown(); // Initial call
}

// Scroll Reveal Animation using Intersection Observer
document.addEventListener('DOMContentLoaded', () => {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Elements to animate
    document.querySelectorAll('.card, .section-title, .hero-content > *, .list-unstyled li').forEach(el => {
        el.classList.add('reveal-on-scroll');
        observer.observe(el);
    });

    // Add click splash effect
    document.addEventListener('click', (e) => {
        createSplash(e.clientX, e.clientY);
    });
});

function createSplash(x, y) {
    const splash = document.createElement('div');
    splash.classList.add('click-splash');

    // Random vibrant colors
    const colors = ['#ff2f92', '#ffd400', '#32cd32', '#00ced1', '#1e90ff', '#ffa500'];
    const color = colors[Math.floor(Math.random() * colors.length)];

    splash.style.left = x + 'px';
    splash.style.top = y + 'px';
    splash.style.backgroundColor = color;

    document.body.appendChild(splash);

    // Remove after animation
    setTimeout(() => {
        splash.remove();
    }, 1000);
}
