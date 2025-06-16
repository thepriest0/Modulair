// ModulAIr JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Profile dropdown toggle
    const profileDropdownButton = document.querySelector('.profile-dropdown-button');
    const profileDropdownMenu = document.querySelector('.profile-dropdown-menu');
    
    if (profileDropdownButton && profileDropdownMenu) {
        profileDropdownButton.addEventListener('click', function(e) {
            e.stopPropagation();
            profileDropdownMenu.classList.toggle('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!profileDropdownButton.contains(e.target) && !profileDropdownMenu.contains(e.target)) {
                profileDropdownMenu.classList.add('hidden');
            }
        });

        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                profileDropdownMenu.classList.add('hidden');
            }
        });
    }

    // Custom topic toggle
    const topicSelect = document.getElementById('topic');
    const customTopicContainer = document.getElementById('custom-topic-container');
    
    if (topicSelect && customTopicContainer) {
        topicSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customTopicContainer.classList.remove('hidden');
                document.getElementById('custom_topic').setAttribute('required', 'required');
            } else {
                customTopicContainer.classList.add('hidden');
                document.getElementById('custom_topic').removeAttribute('required');
            }
        });
    }

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('border-red-500');
                    field.classList.remove('border-gray-300');
                } else {
                    field.classList.remove('border-red-500');
                    field.classList.add('border-gray-300');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields.', 'error');
                return false;
            }
            
            // Show loading state
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
                submitButton.disabled = true;
                
                // Re-enable after 30 seconds as fallback
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 30000);
            }
        });
    });

    // Quiz functionality
    const quizForm = document.querySelector('form[action*="submit-quiz"]');
    if (quizForm) {
        const radioButtons = quizForm.querySelectorAll('input[type="radio"]');
        
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                const label = this.closest('label');
                const questionDiv = label.closest('.border-b, div');
                
                // Remove selected styling from all options in this question
                const allLabels = questionDiv.querySelectorAll('label');
                allLabels.forEach(l => {
                    l.classList.remove('bg-blue-50', 'border-blue-300');
                    l.classList.add('border-gray-200');
                });
                
                // Add selected styling to chosen option
                label.classList.add('bg-blue-50', 'border-blue-300');
                label.classList.remove('border-gray-200');
            });
        });
    }

    // Progress bar animation
    const progressBars = document.querySelectorAll('[style*="width"]');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
            bar.classList.add('progress-bar-animated');
        }, 100);
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Course card hover effects
    const courseCards = document.querySelectorAll('.course-card, .bg-white.rounded-xl.shadow-md');
    courseCards.forEach(card => {
        card.classList.add('card-hover');
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            navigator.clipboard.writeText(textToCopy).then(() => {
                showNotification('Copied to clipboard!', 'success');
            }).catch(err => {
                console.error('Failed to copy: ', err);
                showNotification('Failed to copy to clipboard', 'error');
            });
        });
    });

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        // Close mobile menu with Escape key
        if (e.key === 'Escape' && mobileMenu && !mobileMenu.classList.contains('hidden')) {
            mobileMenu.classList.add('hidden');
        }
        
        // Navigate between form fields with Enter key
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'BUTTON') {
            const form = e.target.closest('form');
            if (form) {
                const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
                const currentIndex = inputs.indexOf(e.target);
                const nextInput = inputs[currentIndex + 1];
                
                if (nextInput) {
                    e.preventDefault();
                    nextInput.focus();
                }
            }
        }
    });

    // Print functionality for certificates
    const printButtons = document.querySelectorAll('[onclick*="print"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Hide non-printable elements
            const nonPrintElements = document.querySelectorAll('nav, footer, .no-print');
            nonPrintElements.forEach(el => el.style.display = 'none');
            
            // Print
            window.print();
            
            // Restore elements after printing
            setTimeout(() => {
                nonPrintElements.forEach(el => el.style.display = '');
            }, 100);
        });
    });

    // Lazy loading for images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));

    // Course progress tracking
    const lessonLinks = document.querySelectorAll('.lesson-link');
    lessonLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Update progress indicators
            const lessonIndex = parseInt(this.dataset.lessonIndex);
            updateLessonProgress(lessonIndex);
        });
    });

    // Dark mode toggle (if implemented)
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
            localStorage.setItem('darkMode', document.documentElement.classList.contains('dark'));
        });
        
        // Load saved dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.documentElement.classList.add('dark');
        }
    }

    // Search functionality
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    
    if (searchInput && searchResults) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.classList.add('hidden');
                return;
            }
            
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        });
    }

    // New Mobile Menu Overlay Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const closeMobileMenu = document.getElementById('closeMobileMenu');

    if (mobileMenuBtn && mobileMenu && closeMobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.remove('hidden');
        });
        closeMobileMenu.addEventListener('click', function() {
            mobileMenu.classList.add('hidden');
        });
        mobileMenu.addEventListener('click', function(e) {
            if (e.target === mobileMenu) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
});

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} fixed top-4 right-4 z-50 max-w-sm`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} mr-2"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function updateLessonProgress(currentLessonIndex) {
    const lessonItems = document.querySelectorAll('.lesson-item');
    lessonItems.forEach((item, index) => {
        const icon = item.querySelector('i');
        if (index < currentLessonIndex) {
            icon.className = 'fas fa-check-circle text-green-500';
            item.classList.add('bg-green-50', 'border-green-200');
            item.classList.remove('bg-gray-50', 'border-gray-200', 'bg-blue-50', 'border-blue-200');
        } else if (index === currentLessonIndex) {
            icon.className = 'fas fa-play-circle text-blue-500';
            item.classList.add('bg-blue-50', 'border-blue-200');
            item.classList.remove('bg-gray-50', 'border-gray-200', 'bg-green-50', 'border-green-200');
        } else {
            icon.className = 'fas fa-circle text-gray-300';
            item.classList.add('bg-gray-50', 'border-gray-200');
            item.classList.remove('bg-blue-50', 'border-blue-200', 'bg-green-50', 'border-green-200');
        }
    });
}

function performSearch(query) {
    // This would typically make an AJAX request to search courses
    // For now, we'll simulate a search
    const searchResults = document.getElementById('search-results');
    searchResults.innerHTML = `
        <div class="p-4 text-center text-gray-500">
            <i class="fas fa-search mb-2"></i>
            <p>Searching for "${query}"...</p>
        </div>
    `;
    searchResults.classList.remove('hidden');
    
    // Simulate search delay
    setTimeout(() => {
        searchResults.innerHTML = `
            <div class="p-4 text-center text-gray-500">
                <i class="fas fa-search mb-2"></i>
                <p>No courses found for "${query}"</p>
                <p class="text-sm mt-2">Try creating a course on this topic!</p>
            </div>
        `;
    }, 1000);
}

// Service Worker registration (for PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    showNotification('An error occurred. Please refresh the page.', 'error');
});

// Performance monitoring
window.addEventListener('load', function() {
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log('Page load time:', loadTime + 'ms');
    }
});

// Lesson navigation function
function navigateToLesson(courseId, lessonIndex) {
    window.location.href = `/course/${courseId}/lesson/${lessonIndex}`;
}

// Mobile lessons toggle for course page
window.toggleLessons = function() {
    const lessonsList = document.getElementById('lessons-list');
    const toggleText = document.getElementById('lessons-toggle-text');
    if (lessonsList.classList.contains('hidden')) {
        lessonsList.classList.remove('hidden');
        toggleText.textContent = 'Hide Lessons';
    } else {
        lessonsList.classList.add('hidden');
        toggleText.textContent = 'Show Lessons';
    }
};
