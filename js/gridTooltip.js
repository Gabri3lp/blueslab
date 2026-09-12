// Floating tooltip positioning for Sync Grid tiles
(function () {
    let lastX = 0;
    let lastY = 0;

    function positionTooltip() {
        const tooltip = document.getElementById('grid-tile-tooltip');
        if (!tooltip) return;

        // Ensure we have rendered dimensions
        const w = tooltip.offsetWidth || 280;
        const h = tooltip.offsetHeight || 120;

        // Horizontally center tooltip over cursor, clamped within viewport
        const minMargin = 12;
        let left = lastX - (w / 2);
        if (left < minMargin) {
            left = minMargin;
        } else if (left + w > window.innerWidth - minMargin) {
            left = window.innerWidth - w - minMargin;
        }

        // Vertically place directly above cursor (14px gap)
        let top = lastY - h - 14;

        // If too close to top of viewport, flip below cursor (20px gap)
        if (top < minMargin) {
            top = lastY + 20;
        }

        // If flipped below and exceeds bottom of window, clamp it
        if (top + h > window.innerHeight - minMargin) {
            top = window.innerHeight - h - minMargin;
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
        tooltip.style.opacity = '1';
    }

    // Passive listener tracks cursor position everywhere with 0 performance impact
    document.addEventListener('pointermove', function (e) {
        lastX = e.clientX;
        lastY = e.clientY;
        positionTooltip();
    }, { passive: true });

    // MutationObserver positions tooltip immediately whenever Blazor renders it into the DOM
    const observer = new MutationObserver(function () {
        if (document.getElementById('grid-tile-tooltip')) {
            positionTooltip();
        }
    });

    function initObserver() {
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        } else {
            document.addEventListener('DOMContentLoaded', initObserver);
        }
    }
    initObserver();
})();
