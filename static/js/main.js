// Mobile menu
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');
if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));
}

// Smooth scroll for in-page anchors
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (!href || href === '#') return;
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Scroll-triggered fade for elements with .fade-in-up
const fadeObserver = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100', 'translate-y-0');
                fadeObserver.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
);

document.querySelectorAll('.fade-in-up').forEach((el) => {
    el.classList.add('opacity-0', 'translate-y-4', 'transition-all', 'duration-700');
    fadeObserver.observe(el);
});

// Subtle parallax on homepage floating cards
if (window.location.pathname === '/' || window.location.pathname === '/home/') {
    document.addEventListener('mousemove', (e) => {
        const cards = document.querySelectorAll('.floating-card');
        const mx = e.clientX / window.innerWidth - 0.5;
        const my = e.clientY / window.innerHeight - 0.5;
        cards.forEach((card, i) => {
            const s = (i + 1) * 8;
            card.style.transform = `translate(${mx * s}px, ${my * s}px)`;
        });
    });
}

// Heart button micro-interaction
document.querySelectorAll('.heart-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        btn.style.transform = 'scale(1.2)';
        setTimeout(() => { btn.style.transform = ''; }, 200);
    });
});

// Navbar scroll state
const ecoNavbar = document.getElementById('ecoNavbar');
window.addEventListener('scroll', () => {
    if (!ecoNavbar) return;
    if (window.scrollY > 40) {
        ecoNavbar.style.background = 'rgba(0, 0, 0, 0.75)';
        ecoNavbar.style.boxShadow = '0 4px 30px rgba(236, 72, 153, 0.15)';
    } else {
        ecoNavbar.style.background = '';
        ecoNavbar.style.boxShadow = '';
    }
}, { passive: true });

// --- Real-time notifications ---
(function initNotifications() {
    const root = document.getElementById('notificationRoot');
    if (!root) return;

    const bellBtn = document.getElementById('notificationBellBtn');
    const dropdown = document.getElementById('notificationDropdown');
    const badge = document.getElementById('notificationBadge');
    const listEl = document.getElementById('notificationList');
    const unreadLabel = document.getElementById('notificationUnreadLabel');
    const pollUrl = root.dataset.pollUrl;
    let dropdownOpen = false;

    function formatRelativeTime(isoString) {
        const seconds = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
        if (seconds < 60) return 'just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        return new Date(isoString).toLocaleDateString();
    }

    function avatarHtml(n) {
        if (n.avatar_url) {
            return `<img src="${n.avatar_url}" alt="" class="w-11 h-11 rounded-full object-cover ring-2 ring-pink-500/30" loading="lazy">`;
        }
        if (n.sender_username) {
            return `<div class="w-11 h-11 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">${n.sender_username.charAt(0).toUpperCase()}</div>`;
        }
        return `<div class="w-11 h-11 rounded-full bg-gradient-to-br from-amber-400 to-yellow-500 flex items-center justify-center"><svg class="w-5 h-5 text-black" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg></div>`;
    }

    function renderNotificationItem(n) {
        const unreadClass = n.is_read ? '' : 'bg-pink-500/5 border-pink-500/20';
        const dot = n.is_read ? '' : '<span class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-pink-500 rounded-full ring-2 ring-[#0a0612]"></span>';
        const link = n.link ? `<a href="${n.link}" class="inline-block mt-1.5 text-xs font-semibold text-pink-400 hover:text-pink-300">View</a>` : '';
        return `<article class="notification-entry group flex gap-3 p-3 rounded-xl border border-transparent hover:bg-white/5 transition-all ${unreadClass}">
            <div class="shrink-0 relative">${avatarHtml(n)}${dot}</div>
            <div class="min-w-0 flex-1">
                <div class="flex justify-between gap-2"><h3 class="text-sm font-semibold text-white">${n.title}</h3><time class="text-[11px] text-white/40">${formatRelativeTime(n.timestamp)}</time></div>
                <p class="text-xs text-white/60 mt-0.5 line-clamp-2">${n.message}</p>${link}
            </div></article>`;
    }

    function updateBadge(count) {
        if (!badge) return;
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : String(count);
            badge.classList.remove('hidden');
            badge.classList.add('notification-badge-pulse');
        } else {
            badge.classList.add('hidden');
        }
        if (unreadLabel) unreadLabel.textContent = String(count);
    }

    function renderList(notifications) {
        if (!listEl) return;
        if (!notifications?.length) {
            listEl.innerHTML = `<div class="py-10 px-4 text-center"><p class="text-sm font-semibold text-white">All caught up</p><p class="text-xs text-white/50 mt-1">New activity will appear here.</p></div>`;
            return;
        }
        listEl.innerHTML = notifications.map(renderNotificationItem).join('');
    }

    async function pollNotifications() {
        if (!pollUrl) return;
        try {
            const res = await fetch(pollUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' });
            if (!res.ok) return;
            const data = await res.json();
            updateBadge(data.unread_count);
            if (dropdownOpen) renderList(data.notifications);
        } catch (e) { /* silent */ }
    }

    function openDropdown() {
        dropdownOpen = true;
        dropdown.classList.remove('hidden', 'opacity-0', 'scale-95');
        dropdown.classList.add('opacity-100', 'scale-100');
        bellBtn?.setAttribute('aria-expanded', 'true');
        pollNotifications();
    }

    function closeDropdown() {
        dropdownOpen = false;
        dropdown.classList.add('opacity-0', 'scale-95');
        dropdown.classList.remove('opacity-100', 'scale-100');
        bellBtn?.setAttribute('aria-expanded', 'false');
        setTimeout(() => { if (!dropdownOpen) dropdown.classList.add('hidden'); }, 200);
    }

    bellBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownOpen ? closeDropdown() : openDropdown();
    });
    document.addEventListener('click', (e) => { if (!root.contains(e.target)) closeDropdown(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDropdown(); });

    setInterval(pollNotifications, 20000);
    pollNotifications();
})();
