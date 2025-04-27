// AI Research Hub - Main JavaScript

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    setupMobileMenu();
    
    // Initialize tooltips
    initTooltips();
    
    // Update last updated time
    updateLastUpdated();
    
    // Setup scroll animations
    setupScrollAnimations();
});

/**
 * Mobile menu functionality
 */
function setupMobileMenu() {
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
            
            // Toggle menu icon
            const icon = menuButton.querySelector('i');
            if (icon) {
                if (icon.classList.contains('fa-bars')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-times');
                } else {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }
}

/**
 * Initialize custom tooltips
 */
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const message = this.getAttribute('data-tooltip');
            const position = this.getAttribute('data-tooltip-position') || 'top';
            
            showTooltip(this, message, position);
        });
        
        tooltip.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

/**
 * Show tooltip
 */
function showTooltip(element, message, position = 'top') {
    // Remove any existing tooltips
    hideTooltip();
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip fade-in';
    tooltip.textContent = message;
    
    // Add tooltip to body
    document.body.appendChild(tooltip);
    
    // Position tooltip relative to element
    const rect = element.getBoundingClientRect();
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    let top, left;
    
    switch (position) {
        case 'bottom':
            top = rect.bottom + scrollTop + 10;
            left = rect.left + scrollLeft + (rect.width / 2) - (tooltip.offsetWidth / 2);
            break;
        case 'left':
            top = rect.top + scrollTop + (rect.height / 2) - (tooltip.offsetHeight / 2);
            left = rect.left + scrollLeft - tooltip.offsetWidth - 10;
            break;
        case 'right':
            top = rect.top + scrollTop + (rect.height / 2) - (tooltip.offsetHeight / 2);
            left = rect.right + scrollLeft + 10;
            break;
        default: // top
            top = rect.top + scrollTop - tooltip.offsetHeight - 10;
            left = rect.left + scrollLeft + (rect.width / 2) - (tooltip.offsetWidth / 2);
    }
    
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Update last updated time
 */
function updateLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        const now = new Date();
        lastUpdatedElement.textContent = now.toLocaleString();
    }
}

/**
 * Setup scroll animations
 */
function setupScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1
        });
        
        animatedElements.forEach(element => {
            observer.observe(element);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animatedElements.forEach(element => {
            element.classList.add('fade-in');
        });
    }
}

/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Generate chart for trending topics
 */
function generateTrendingChart(data) {
    const ctx = document.getElementById('trending-chart');
    if (!ctx) return;
    
    // Sample data - would be replaced with actual data from backend
    const chartData = {
        labels: ['Machine Learning', 'Large Language Models', 'Computer Vision', 'Reinforcement Learning', 'Neural Networks'],
        datasets: [{
            label: 'Topic Mentions',
            data: [65, 59, 80, 81, 56],
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2,
            borderRadius: 4,
            borderSkipped: false,
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Initialize word cloud
 */
function initializeWordCloud(data) {
    const container = document.getElementById('word-cloud');
    if (!container) return;
    
    // This is a placeholder - you would integrate with a proper
    // word cloud library like d3-cloud in a production app
    container.innerHTML = '<div class="text-center py-10">Word cloud visualization enabled</div>';
}

/**
 * Handle form submissions via AJAX
 */
function setupFormSubmissions() {
    const forms = document.querySelectorAll('form[data-ajax="true"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const submitButton = form.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            
            // Show loading state
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Processing...';
            }
            
            // API endpoint from form action
            fetch(form.action, {
                method: form.method || 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Handle success
                if (data.success) {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.message) {
                        showNotification(data.message, 'success');
                    }
                } else {
                    // Handle error
                    showNotification(data.message || 'An error occurred', 'error');
                }
            })
            .catch(error => {
                showNotification('An error occurred while processing your request', 'error');
            })
            .finally(() => {
                // Reset button state
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonText;
                }
            });
        });
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} fade-in`;
    
    // Set icon based on type
    let icon = 'info-circle';
    switch (type) {
        case 'success':
            icon = 'check-circle';
            break;
        case 'error':
            icon = 'exclamation-circle';
            break;
        case 'warning':
            icon = 'exclamation-triangle';
            break;
    }
    
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas fa-${icon}"></i>
        </div>
        <div class="notification-content">
            ${message}
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Close button functionality
    const closeButton = notification.querySelector('.notification-close');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            notification.remove();
        });
    }
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

/**
 * Create and display a topic network graph
 */
function createTopicGraph(container, data) {
    if (!container) return;
    
    // This is a placeholder - in a real implementation, you would use
    // a library like D3.js or Vis.js to create an interactive network graph
    container.innerHTML = `
        <div class="flex items-center justify-center h-full">
            <div class="text-center">
                <div class="mb-4 text-blue-600">
                    <i class="fas fa-project-diagram text-4xl"></i>
                </div>
                <p>Topic graph visualization enabled</p>
            </div>
        </div>
    `;
}