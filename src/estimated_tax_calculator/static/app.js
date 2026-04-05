/**
 * 1040ES Calculator — Client-side enhancements
 * Form validation, number formatting, smooth transitions
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('tax-form');
    const resultsSection = document.getElementById('results');

    // Smooth scroll to results after form submission
    if (resultsSection) {
        setTimeout(() => {
            resultsSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start',
            });
        }, 300);
    }

    // Add subtle animation to form cards on load
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(16px)';
        card.style.transition = `opacity 0.4s ease ${index * 0.06}s, transform 0.4s ease ${index * 0.06}s`;
        requestAnimationFrame(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    });

    // Format number inputs with commas on blur (visual only)
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach((input) => {
        // Add focus animation
        input.addEventListener('focus', () => {
            const parent = input.closest('.card');
            if (parent) {
                parent.style.borderColor = 'rgba(99, 102, 241, 0.35)';
            }
        });

        input.addEventListener('blur', () => {
            const parent = input.closest('.card');
            if (parent) {
                parent.style.borderColor = '';
            }
        });
    });

    // Button loading state
    if (form) {
        form.addEventListener('submit', () => {
            const btn = document.getElementById('calculate-btn');
            if (btn) {
                btn.disabled = true;
                const textEl = btn.querySelector('.btn-text');
                const iconEl = btn.querySelector('.btn-icon');
                if (textEl) textEl.textContent = 'Calculating…';
                if (iconEl) iconEl.textContent = '⏳';
                btn.style.opacity = '0.8';
            }
        });
    }
    // Global tooltip to escape backdrop-filter containing blocks
    const globalTooltip = document.getElementById('global-tooltip');
    if (globalTooltip) {
        const infoTips = document.querySelectorAll('.info-tip, .tooltip-inline');
        infoTips.forEach((tip) => {
            tip.addEventListener('mouseenter', () => {
                const tipText = tip.getAttribute('data-tip');
                if (!tipText) return;

                globalTooltip.textContent = tipText;
                
                const rect = tip.getBoundingClientRect();
                
                // Position centered above the icon, but constrained by viewport width
                let left = rect.left + (rect.width / 2) - 200;
                left = Math.max(10, Math.min(left, window.innerWidth - 410));
                
                // Position above the icon (with a small gap)
                // If it goes off the top of the screen, place it below the icon
                let top = rect.top - globalTooltip.offsetHeight - 8;
                if (top < 10) {
                    top = rect.bottom + 8;
                }
                
                globalTooltip.style.left = left + 'px';
                globalTooltip.style.top = top + 'px';
                globalTooltip.style.opacity = '1';
                globalTooltip.style.visibility = 'visible';
            });

            tip.addEventListener('mouseleave', () => {
                globalTooltip.style.opacity = '0';
                globalTooltip.style.visibility = 'hidden';
            });
        });
    }

    /* =========================================
       Header Actions Logic
       ========================================= */

    // --- Reset Form Logic ---
    const resetBtn = document.getElementById('reset-button');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            // Soft clear all inputs
            const inputs = document.querySelectorAll('#tax-form input[type="number"]');
            inputs.forEach(input => {
                if (input.hasAttribute('required')) {
                    input.value = ''; // clears to placeholder via HTML for required fields
                } else {
                    input.value = '0'; // solid 0 for optional fields
                }
            });
            // Reset select dropdowns
            const selects = document.querySelectorAll('#tax-form select');
            selects.forEach(select => {
                select.selectedIndex = 0;
            });
            // Hide the results section dynamically if it exists
            if (resultsSection) {
                resultsSection.style.display = 'none';
            }
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // --- Theme Toggle Logic ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const moonIcon = document.getElementById('moon-icon');
    const sunIcon = document.getElementById('sun-icon');
    
    // Function to apply theme
    function applyTheme(isLight) {
        if (isLight) {
            document.documentElement.classList.add('light-theme');
            if (moonIcon) moonIcon.style.display = 'none';
            if (sunIcon) sunIcon.style.display = 'block';
        } else {
            document.documentElement.classList.remove('light-theme');
            if (moonIcon) moonIcon.style.display = 'block';
            if (sunIcon) sunIcon.style.display = 'none';
        }
    }

    // Check system preference & localStorage
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    const isInitialLight = savedTheme === 'light' || (!savedTheme && systemPrefersLight);
    
    // Apply initial theme
    applyTheme(isInitialLight);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentlyLight = document.documentElement.classList.contains('light-theme');
            const newIsLight = !currentlyLight;
            
            applyTheme(newIsLight);
            localStorage.setItem('theme', newIsLight ? 'light' : 'dark');
        });
    }
});
