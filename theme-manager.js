/**
 * Advanced Theme Manager for VM Dashboard
 * Features: Dark/Light mode, Auto-detection, Smooth transitions
 */

class ThemeManager {
    constructor() {
        this.THEMES = {
            LIGHT: 'light',
            DARK: 'dark',
            AUTO: 'auto'
        };
        
        this.STORAGE_KEY = 'vm-dashboard-theme';
        this.currentTheme = this.THEMES.LIGHT;
        this.systemPreference = this.getSystemPreference();
        
        this.init();
    }
    
    init() {
        // Load saved theme or detect system preference
        const savedTheme = this.getSavedTheme();
        this.setTheme(savedTheme);
        
        // Listen for system theme changes
        this.watchSystemPreference();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        console.log('🎨 Theme Manager initialized');
        console.log(`Current theme: ${this.currentTheme}`);
        console.log(`System preference: ${this.systemPreference}`);
    }
    
    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return this.THEMES.DARK;
        }
        return this.THEMES.LIGHT;
    }
    
    getSavedTheme() {
        const saved = localStorage.getItem(this.STORAGE_KEY);
        if (saved && Object.values(this.THEMES).includes(saved)) {
            return saved;
        }
        return this.THEMES.AUTO; // Default to auto-detection
    }
    
    setTheme(theme) {
        let actualTheme = theme;
        
        // Handle auto theme
        if (theme === this.THEMES.AUTO) {
            actualTheme = this.systemPreference;
        }
        
        // Apply theme
        document.documentElement.setAttribute('data-theme', actualTheme);
        this.currentTheme = theme; // Keep the user preference, not the actual theme
        
        // Save preference
        localStorage.setItem(this.STORAGE_KEY, theme);
        
        // Update UI
        this.updateThemeToggle(theme, actualTheme);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme, actualTheme: actualTheme }
        }));
        
        console.log(`🎨 Theme changed to: ${theme} (actual: ${actualTheme})`);
    }
    
    updateThemeToggle(preferenceTheme, actualTheme) {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        const themeText = document.getElementById('themeText');
        
        if (!themeToggle || !themeIcon || !themeText) return;
        
        // Update based on preference theme
        switch (preferenceTheme) {
            case this.THEMES.LIGHT:
                themeIcon.textContent = '🌙';
                themeText.textContent = 'Dark';
                themeToggle.classList.remove('active', 'auto');
                break;
            case this.THEMES.DARK:
                themeIcon.textContent = '☀️';
                themeText.textContent = 'Light';
                themeToggle.classList.add('active');
                themeToggle.classList.remove('auto');
                break;
            case this.THEMES.AUTO:
                themeIcon.textContent = '🔄';
                themeText.textContent = 'Auto';
                themeToggle.classList.add('auto');
                themeToggle.classList.toggle('active', actualTheme === this.THEMES.DARK);
                break;
        }
    }
    
    toggleTheme() {
        const currentTheme = this.currentTheme;
        let nextTheme;
        
        // Cycle through themes: Light -> Dark -> Auto -> Light
        switch (currentTheme) {
            case this.THEMES.LIGHT:
                nextTheme = this.THEMES.DARK;
                break;
            case this.THEMES.DARK:
                nextTheme = this.THEMES.AUTO;
                break;
            case this.THEMES.AUTO:
                nextTheme = this.THEMES.LIGHT;
                break;
            default:
                nextTheme = this.THEMES.LIGHT;
        }
        
        this.setTheme(nextTheme);
        this.animateToggle();
        
        // Show brief notification
        this.showThemeNotification(nextTheme);
    }
    
    animateToggle() {
        const toggle = document.getElementById('themeToggle');
        if (!toggle) return;
        
        toggle.style.transform = 'scale(0.9) rotate(180deg)';
        setTimeout(() => {
            toggle.style.transform = 'scale(1) rotate(0deg)';
        }, 200);
    }
    
    showThemeNotification(theme) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        
        let message;
        switch (theme) {
            case this.THEMES.LIGHT:
                message = '☀️ Light Mode';
                break;
            case this.THEMES.DARK:
                message = '🌙 Dark Mode';
                break;
            case this.THEMES.AUTO:
                message = '🔄 Auto Mode';
                break;
        }
        
        notification.textContent = message;
        
        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '70px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '25px',
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: '500',
            backdropFilter: 'var(--backdrop-blur)',
            zIndex: '9999',
            opacity: '0',
            transition: 'all 0.3s ease',
            pointerEvents: 'none'
        });
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(-50%) translateY(10px)';
        }, 50);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(-50%) translateY(-10px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 2000);
    }
    
    watchSystemPreference() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                this.systemPreference = e.matches ? this.THEMES.DARK : this.THEMES.LIGHT;
                console.log(`🔄 System preference changed to: ${this.systemPreference}`);
                
                // If user is on auto mode, update the theme
                if (this.currentTheme === this.THEMES.AUTO) {
                    this.setTheme(this.THEMES.AUTO);
                }
            });
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + D for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                this.toggleTheme();
            }
            
            // Ctrl/Cmd + Shift + L for light mode
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'L') {
                e.preventDefault();
                this.setTheme(this.THEMES.LIGHT);
            }
            
            // Ctrl/Cmd + Shift + D for dark mode
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.setTheme(this.THEMES.DARK);
            }
            
            // Ctrl/Cmd + Shift + A for auto mode
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.setTheme(this.THEMES.AUTO);
            }
        });
    }
    
    // Method to get current effective theme (useful for other components)
    getEffectiveTheme() {
        if (this.currentTheme === this.THEMES.AUTO) {
            return this.systemPreference;
        }
        return this.currentTheme;
    }
    
    // Method to check if dark mode is active
    isDarkMode() {
        return this.getEffectiveTheme() === this.THEMES.DARK;
    }
    
    // Method for external components to force theme
    forceTheme(theme) {
        if (Object.values(this.THEMES).includes(theme)) {
            this.setTheme(theme);
            return true;
        }
        return false;
    }
}

// Enhanced CSS for theme notifications and auto mode
const enhancedThemeCSS = `
    .theme-toggle.auto {
        background: linear-gradient(45deg, var(--color-info), var(--color-success));
        color: white;
        animation: rainbow 3s ease-in-out infinite;
    }
    
    @keyframes rainbow {
        0%, 100% { background: linear-gradient(45deg, var(--color-info), var(--color-success)); }
        50% { background: linear-gradient(45deg, var(--color-success), var(--color-warning)); }
    }
    
    .theme-notification {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-50%) translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(-50%) translateY(10px);
        }
    }
    
    /* Enhanced transitions for theme changes */
    [data-theme="dark"] {
        transition: background 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                   color 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                   border-color 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    [data-theme="light"] {
        transition: background 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                   color 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                   border-color 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Loading animation for theme changes */
    .theme-changing {
        pointer-events: none;
    }
    
    .theme-changing * {
        transition: all 0.3s ease !important;
    }
`;

// Inject enhanced CSS
function injectEnhancedThemeCSS() {
    const style = document.createElement('style');
    style.textContent = enhancedThemeCSS;
    document.head.appendChild(style);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        injectEnhancedThemeCSS();
        window.themeManager = new ThemeManager();
    });
} else {
    injectEnhancedThemeCSS();
    window.themeManager = new ThemeManager();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
