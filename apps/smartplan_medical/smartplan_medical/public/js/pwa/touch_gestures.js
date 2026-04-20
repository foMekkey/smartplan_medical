/**
 * SmartPlan Medical — Touch Gestures
 * Swipe-back navigation only. Pull-to-refresh disabled (uses native browser).
 */

const SmartPlanGestures = {
    init() {
        if (!document.documentElement.classList.contains('sp-mobile')) return;
        this.setupSwipeBack();
    },

    // ─── SWIPE BACK NAVIGATION ───────────────
    setupSwipeBack() {
        let startX = 0;
        let startY = 0;
        let swiping = false;

        document.addEventListener('touchstart', (e) => {
            if (e.touches[0].clientX > 30) return;
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            swiping = true;
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!swiping) return;
            const deltaY = Math.abs(e.touches[0].clientY - startY);
            if (deltaY > 50) swiping = false;
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!swiping) return;
            swiping = false;
            const deltaX = e.changedTouches[0].clientX - startX;
            if (deltaX > 100) {
                window.history.back();
            }
        }, { passive: true });
    },
};

export default SmartPlanGestures;
