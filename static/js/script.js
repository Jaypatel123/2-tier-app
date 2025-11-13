let reels = [];
let originalReels = []; // Store original order
let currentReelIndex = 0;
let isScrolling = false;
let viewsCount = 0;
let isLoggedIn = false;
let viewsRemaining = 10;
let viewedReelIds = new Set(); // Track which reels have been viewed
let allReelsViewed = false; // Flag to indicate all reels have been viewed

// Fetch and display reels
async function loadReels() {
    const container = document.getElementById('reelsContainer');
    if (!container) {
        console.error('reelsContainer element not found');
        return;
    }
    
    container.innerHTML = '<div class="loading">Loading reels...</div>';
    
    try {
        const response = await fetch('/api/reels');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        console.log('API Response:', data);
        
        if (data.success) {
            originalReels = data.reels || [];
            
            // Shuffle reels randomly from the start
            if (originalReels.length > 0) {
                reels = shuffleArray(originalReels);
            } else {
                reels = [...originalReels];
            }
            
            console.log(`Loaded ${reels.length} reels (randomly shuffled)`);
            
            // Update user status
            if (data.user) {
                isLoggedIn = data.user.is_logged_in;
                viewsCount = data.user.views_count || 0;
                viewsRemaining = data.user.views_remaining !== null ? data.user.views_remaining : null;
            }
            
            // Reset viewed reels tracking
            viewedReelIds.clear();
            allReelsViewed = false;
            
            if (reels.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h2>No reels yet</h2>
                        <p>Click "Add Reel" to add your first reel!</p>
                    </div>
                `;
                return;
            }
            
            // Create reel items
            try {
                container.innerHTML = reels.map((reel, index) => `
                <div class="reel-item" data-index="${index}">
                    <div class="reel-video-wrapper">
                        <video 
                            class="reel-video" 
                            preload="auto"
                            playsinline
                            webkit-playsinline
                            ${index === 0 ? 'autoplay muted' : ''}
                            loop
                            data-reel-id="${reel.id}">
                            <source src="${reel.url}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    <div class="reel-info-overlay">
                        <div class="reel-title">${reel.title || 'Untitled Reel'}</div>
                        ${reel.description ? `<div class="reel-description">${reel.description}</div>` : ''}
                        <div class="reel-meta">
                            <span>${formatDate(reel.created_at)}</span>
                        </div>
                    </div>
                </div>
            `).join('');
            } catch (renderError) {
                console.error('Error rendering reels:', renderError);
                container.innerHTML = `<div class="error">Error rendering reels: ${renderError.message}</div>`;
                return;
            }
            
            console.log('Reels rendered successfully');
            
            // Setup intersection observer for video autoplay
            try {
                setupVideoAutoplay();
                
                // Play first video immediately - start muted for autoplay, then unmute
                const playFirstVideo = () => {
                    const firstVideo = container.querySelector('.reel-video');
                    if (!firstVideo) return;
                    
                    // Start muted to allow autoplay, then unmute after playing
                    firstVideo.muted = true;
                    
                    const attemptPlay = () => {
                        firstVideo.play().then(() => {
                            // Once playing, unmute after a short delay
                            setTimeout(() => {
                                firstVideo.muted = false;
                                console.log('First video playing with sound');
                            }, 300);
                        }).catch(e => {
                            console.log('Error playing first video:', e);
                            // Try again after user interaction might be needed
                            setTimeout(() => {
                                firstVideo.play().catch(err => {
                                    console.log('Autoplay prevented, waiting for user interaction');
                                });
                            }, 1000);
                        });
                    };
                    
                    // If video is ready, play it
                    if (firstVideo.readyState >= 2) {
                        attemptPlay();
                    } else {
                        // Wait for video to be ready
                        const onReady = () => {
                            attemptPlay();
                        };
                        firstVideo.addEventListener('loadeddata', onReady, { once: true });
                        firstVideo.addEventListener('canplay', onReady, { once: true });
                        firstVideo.addEventListener('loadedmetadata', onReady, { once: true });
                        
                        // Fallback: try to play after delays
                        setTimeout(attemptPlay, 300);
                        setTimeout(attemptPlay, 1000);
                    }
                };
                
                // Try immediately and after short delays
                setTimeout(playFirstVideo, 100);
                setTimeout(playFirstVideo, 300);
                setTimeout(playFirstVideo, 500);
                setTimeout(playFirstVideo, 1000);
                
                // Also try when user interacts with page
                const enableOnInteraction = () => {
                    if (firstVideo && firstVideo.paused) {
                        firstVideo.muted = false;
                        firstVideo.play().catch(e => {
                            console.log('Error playing after interaction:', e);
                        });
                    }
                };
                
                // Listen for any user interaction
                document.addEventListener('click', enableOnInteraction, { once: true });
                document.addEventListener('touchstart', enableOnInteraction, { once: true });
                document.addEventListener('keydown', enableOnInteraction, { once: true });
            } catch (e) {
                console.error('Error setting up video autoplay:', e);
            }
            
            // Setup scroll handling
            try {
                setupScrollHandling();
            } catch (e) {
                console.error('Error setting up scroll handling:', e);
            }
            
            // Setup keyboard navigation
            try {
                setupKeyboardNavigation();
            } catch (e) {
                console.error('Error setting up keyboard navigation:', e);
            }
            
            // Setup touch handling
            try {
                setupTouchHandling();
            } catch (e) {
                console.error('Error setting up touch handling:', e);
            }
            
            // Update views counter after everything is set up
            try {
                updateViewsCounter();
            } catch (e) {
                console.error('Error updating views counter:', e);
            }
        } else {
            console.error('API returned error:', data.error);
            container.innerHTML = `<div class="error">Error: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        console.error('Error loading reels:', error);
        container.innerHTML = `<div class="error">Error loading reels: ${error.message}</div>`;
    }
}

// Setup intersection observer for video autoplay
function setupVideoAutoplay() {
    const container = document.getElementById('reelsContainer');
    if (!container) return;
    
    // Create global observer if it doesn't exist
    if (!globalVideoObserver) {
        globalVideoObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const video = entry.target;
                const reelId = parseInt(video.getAttribute('data-reel-id'));
                
                if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
                    // Video is in view - play it with sound
                    if (video.muted) {
                        video.muted = false;
                    }
                    
                    // Ensure video is ready before playing
                    const playVideo = () => {
                        video.play().catch(e => {
                            // Autoplay with sound was prevented, try muted first
                            if (e.name === 'NotAllowedError') {
                                video.muted = true;
                                video.play().then(() => {
                                    // Once playing, try to unmute after a short delay
                                    setTimeout(() => {
                                        video.muted = false;
                                    }, 100);
                                }).catch(err => {
                                    console.log('Autoplay prevented, waiting for user interaction');
                                });
                            } else {
                                console.log('Error playing video:', e);
                            }
                        });
                    };
                    
                    // If video is ready, play it
                    if (video.readyState >= 2) {
                        playVideo();
                    } else {
                        // Wait for video to be ready
                        video.addEventListener('loadeddata', playVideo, { once: true });
                        video.addEventListener('canplay', playVideo, { once: true });
                        // Fallback: try to play anyway
                        playVideo();
                    }
                    
                    // Track view if not already viewed
                    if (reelId && !viewedReelIds.has(reelId)) {
                        viewedReelIds.add(reelId);
                        console.log(`Viewed reel ${reelId}. Total viewed: ${viewedReelIds.size}/${originalReels.length}`);
                        
                        // Check if all reels have been viewed
                        if (viewedReelIds.size >= originalReels.length && !allReelsViewed) {
                            allReelsViewed = true;
                            console.log('All reels viewed! Continuing with continuous random playback...');
                        }
                        
                        // Track view for non-logged-in users (for 10-reel limit)
                        if (!isLoggedIn) {
                            trackReelView();
                        }
                    }
                } else {
                    // Video is out of view - pause it
                    video.pause();
                }
            });
        }, {
            threshold: 0.5,
            root: container
        });
    }
    
    // Observe all videos that haven't been observed yet
    const videos = document.querySelectorAll('.reel-video');
    videos.forEach((video, index) => {
        if (!video.hasAttribute('data-observed')) {
            video.setAttribute('data-observed', 'true');
            globalVideoObserver.observe(video);
            
            // For the first video, also check if it's already in view and play it
            if (index === 0) {
                setTimeout(() => {
                    const container = document.getElementById('reelsContainer');
                    if (container) {
                        const rect = video.getBoundingClientRect();
                        const containerRect = container.getBoundingClientRect();
                        const isInView = rect.top >= containerRect.top && 
                                        rect.top < containerRect.bottom &&
                                        rect.bottom <= containerRect.bottom;
                        
                        if (isInView && video.paused) {
                            video.muted = true;
                            video.play().then(() => {
                                setTimeout(() => {
                                    video.muted = false;
                                }, 300);
                            }).catch(e => {
                                console.log('First video autoplay failed:', e);
                            });
                        }
                    }
                }, 200);
            }
        }
    });
}

// Shuffle array using Fisher-Yates algorithm
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

// Global video observer for all videos
let globalVideoObserver = null;

// Append more shuffled reels for continuous infinite scroll
function appendMoreReels() {
    if (originalReels.length === 0) return;
    
    const container = document.getElementById('reelsContainer');
    if (!container) return;
    
    // Prevent multiple simultaneous appends
    if (container.hasAttribute('data-appending')) return;
    container.setAttribute('data-appending', 'true');
    
    // Shuffle original reels
    const shuffledReels = shuffleArray(originalReels);
    
    // Get current scroll position to maintain it
    const currentScroll = container.scrollTop;
    
    // Append new reels to existing ones
    const newReelsHTML = shuffledReels.map((reel, index) => {
        const globalIndex = reels.length + index;
        return `
            <div class="reel-item" data-index="${globalIndex}">
                <div class="reel-video-wrapper">
                    <video 
                        class="reel-video" 
                        preload="metadata"
                        playsinline
                        webkit-playsinline
                        loop
                        data-reel-id="${reel.id}">
                        <source src="${reel.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="reel-info-overlay">
                    <div class="reel-title">${reel.title || 'Untitled Reel'}</div>
                    ${reel.description ? `<div class="reel-description">${reel.description}</div>` : ''}
                    <div class="reel-meta">
                        <span>${formatDate(reel.created_at)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Append to container
    container.insertAdjacentHTML('beforeend', newReelsHTML);
    
    // Add to reels array
    reels = [...reels, ...shuffledReels];
    
    // Restore scroll position immediately to prevent jump
    container.scrollTop = currentScroll;
    
    // Setup observers for new videos using the global observer
    const newVideos = Array.from(container.querySelectorAll('.reel-video'))
        .filter(v => !v.hasAttribute('data-observed'));
    
    if (globalVideoObserver) {
        newVideos.forEach(video => {
            video.setAttribute('data-observed', 'true');
            globalVideoObserver.observe(video);
        });
    }
    
    // Remove the flag
    container.removeAttribute('data-appending');
    
    console.log(`Appended ${shuffledReels.length} more reels. Total: ${reels.length}`);
}

// Render reels in the container
function renderReels() {
    const container = document.getElementById('reelsContainer');
    if (!container) return;
    
    try {
        container.innerHTML = reels.map((reel, index) => `
            <div class="reel-item" data-index="${index}">
                <div class="reel-video-wrapper">
                    <video 
                        class="reel-video" 
                        preload="metadata"
                        playsinline
                        webkit-playsinline
                        loop
                        data-reel-id="${reel.id}">
                        <source src="${reel.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="reel-info-overlay">
                    <div class="reel-title">${reel.title || 'Untitled Reel'}</div>
                    ${reel.description ? `<div class="reel-description">${reel.description}</div>` : ''}
                    <div class="reel-meta">
                        <span>${formatDate(reel.created_at)}</span>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Re-setup all handlers
        setupVideoAutoplay();
        setupScrollHandling();
        setupKeyboardNavigation();
        setupTouchHandling();
        updateViewsCounter();
        
        console.log('Reels re-rendered with random order');
    } catch (renderError) {
        console.error('Error rendering reels:', renderError);
    }
}

// Track when a reel is viewed
async function trackReelView() {
    if (isLoggedIn) return; // Logged in users have unlimited views
    
    try {
        const response = await fetch('/api/track-view', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            viewsCount = data.views_count;
            viewsRemaining = data.views_remaining;
            updateViewsCounter();
            
            // Show login modal if user has viewed 10 reels
            if (data.requires_login) {
                showLoginModal();
            }
        }
    } catch (error) {
        console.error('Error tracking view:', error);
    }
}

// Setup scroll handling for smooth navigation
function setupScrollHandling() {
    const container = document.getElementById('reelsContainer');
    let scrollTimeout;
    
    container.addEventListener('scroll', () => {
        if (isScrolling) return;
        
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Just check if we need to append more reels, don't snap
            checkAndAppendReels();
        }, 150);
    });
    
    // Handle wheel events for better control
    let wheelTimeout;
    container.addEventListener('wheel', (e) => {
        clearTimeout(wheelTimeout);
        wheelTimeout = setTimeout(() => {
            // Just check if we need to append more reels, don't snap
            checkAndAppendReels();
        }, 100);
    }, { passive: true });
}

// Check if we're near the end and append more reels if needed
function checkAndAppendReels() {
    const container = document.getElementById('reelsContainer');
    const reelItems = document.querySelectorAll('.reel-item');
    
    if (reelItems.length === 0) return;
    
    // Calculate which reel is currently in view
    let nearestIndex = 0;
    let nearestDistance = Infinity;
    
    reelItems.forEach((item, index) => {
        const rect = item.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const distance = Math.abs(rect.top - containerRect.top);
        
        if (distance < nearestDistance) {
            nearestDistance = distance;
            nearestIndex = index;
        }
    });
    
    // Update current index without scrolling
    if (nearestIndex !== currentReelIndex) {
        currentReelIndex = nearestIndex;
    }
    
    // If we're near the end (last 3 reels), append more for infinite scroll
    if (nearestIndex >= reels.length - 3) {
        appendMoreReels();
    }
    
    // If reel is not properly aligned (more than 50px off), snap to it
    const currentItem = reelItems[nearestIndex];
    if (currentItem) {
        const rect = currentItem.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const offset = Math.abs(rect.top - containerRect.top);
        
        // If misaligned by more than 50px, snap to it
        if (offset > 50 && !isScrolling) {
            isScrolling = true;
            currentItem.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
            setTimeout(() => {
                isScrolling = false;
            }, 500);
        }
    }
}

// Snap to nearest reel (only used for keyboard/touch navigation, not automatic)
function snapToNearestReel() {
    const container = document.getElementById('reelsContainer');
    const reelItems = document.querySelectorAll('.reel-item');
    
    if (reelItems.length === 0) return;
    
    let nearestIndex = 0;
    let nearestDistance = Infinity;
    
    reelItems.forEach((item, index) => {
        const rect = item.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const distance = Math.abs(rect.top - containerRect.top);
        
        if (distance < nearestDistance) {
            nearestDistance = distance;
            nearestIndex = index;
        }
    });
    
    if (nearestIndex !== currentReelIndex) {
        currentReelIndex = nearestIndex;
        
        // If we're near the end (last 3 reels), append more reels for infinite scroll
        if (nearestIndex >= reels.length - 3) {
            appendMoreReels();
        }
    }
}

// Scroll to specific reel
function scrollToReel(index) {
    const container = document.getElementById('reelsContainer');
    const reelItems = document.querySelectorAll('.reel-item');
    
    if (index < 0) {
        return;
    }
    
    // If index is beyond current reels, append more
    if (index >= reelItems.length) {
        appendMoreReels();
        // Wait a bit for DOM to update, then scroll
        setTimeout(() => {
            const newItems = document.querySelectorAll('.reel-item');
            if (index < newItems.length) {
                scrollToReel(index);
            }
        }, 100);
        return;
    }
    
    // Scroll to specific reel with proper alignment
    const targetItem = reelItems[index];
    if (targetItem) {
        isScrolling = true;
        targetItem.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
        
        setTimeout(() => {
            isScrolling = false;
            
            // If we're near the end, append more reels for infinite scroll
            if (index >= reelItems.length - 3) {
                appendMoreReels();
            }
        }, 500);
    }
}

// Setup keyboard navigation
function setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
        // Don't navigate if user is typing in a form
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if (e.key === 'ArrowDown' || e.key === 'PageDown') {
            e.preventDefault();
            currentReelIndex++;
            scrollToReel(currentReelIndex);
        } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
            e.preventDefault();
            if (currentReelIndex > 0) {
                currentReelIndex--;
                scrollToReel(currentReelIndex);
            }
        } else if (e.key === 'Home') {
            e.preventDefault();
            currentReelIndex = 0;
            scrollToReel(0);
        } else if (e.key === 'End') {
            e.preventDefault();
            // Append more reels and go to the new end
            appendMoreReels();
            setTimeout(() => {
                const reelItems = document.querySelectorAll('.reel-item');
                if (reelItems.length > 0) {
                    currentReelIndex = reelItems.length - 1;
                    scrollToReel(currentReelIndex);
                }
            }, 100);
        }
    });
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

// Delete a reel
async function deleteReel(reelId) {
    if (!confirm('Are you sure you want to delete this reel?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/reels/${reelId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadReels(); // Reload reels after deletion
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error deleting reel: ${error.message}`);
    }
}

// Show add reel modal
function showAddReelModal() {
    // This feature requires login - handled by backend
    alert('Please login to add reels');
}

// Close add reel modal
function closeAddReelModal() {
    // Modal removed, function kept for compatibility
}

// Handle form submission (only if form exists)
const addReelForm = document.getElementById('addReelForm');
if (addReelForm) {
    addReelForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            filename: document.getElementById('reelUrl')?.value,
            title: document.getElementById('reelTitle')?.value,
            description: document.getElementById('reelDescription')?.value
        };
        
        try {
            const response = await fetch('/api/reels', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                closeAddReelModal();
                loadReels(); // Reload reels after adding
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            alert(`Error adding reel: ${error.message}`);
        }
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const loginModal = document.getElementById('loginModal');
    if (event.target === loginModal) {
        // Don't allow closing login modal by clicking outside if views are exhausted
        if (viewsRemaining === 0 && !isLoggedIn) {
            return;
        }
        closeLoginModal();
    }
}

// Login Modal Functions
function showLoginModal() {
    document.getElementById('loginModal').style.display = 'block';
    switchTab('login');
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('loginError').textContent = '';
    document.getElementById('registerError').textContent = '';
}

function switchTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.tab-btn');
    
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'login') {
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
        tabs[0].classList.add('active');
    } else {
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
        tabs[1].classList.add('active');
    }
    
    // Clear errors
    document.getElementById('loginError').textContent = '';
    document.getElementById('registerError').textContent = '';
}

// Handle login form submission (wait for DOM to be ready)
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            isLoggedIn = true;
            viewsCount = 0;
            viewsRemaining = null;
            closeLoginModal();
            updateViewsCounter();
            // Reload reels to get updated user status
            loadReels();
        } else {
            errorDiv.textContent = data.error || 'Login failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Error: ' + error.message;
    }
    });
}

// Handle register form submission (wait for DOM to be ready)
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const errorDiv = document.getElementById('registerError');
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            isLoggedIn = true;
            viewsCount = 0;
            viewsRemaining = null;
            closeLoginModal();
            updateViewsCounter();
            // Reload reels to get updated user status
            loadReels();
        } else {
            errorDiv.textContent = data.error || 'Registration failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Error: ' + error.message;
    }
    });
}

// Check auth status on page load
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.success) {
            isLoggedIn = data.is_logged_in;
            viewsCount = data.views_count || 0;
            viewsRemaining = data.views_remaining !== null ? data.views_remaining : null;
            updateViewsCounter();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}

// Update views counter display
function updateViewsCounter() {
    try {
        const counter = document.getElementById('viewsCounter');
        const text = document.getElementById('viewsText');
        const addBtn = document.getElementById('addReelBtn');
        
        if (!counter || !text) {
            console.warn('Views counter elements not found');
            return;
        }
        
        if (isLoggedIn) {
            counter.classList.remove('show');
            if (addBtn) addBtn.style.display = 'block';
        } else {
            if (viewsRemaining !== null && viewsRemaining >= 0) {
                counter.classList.add('show');
                text.textContent = `${viewsRemaining} reels remaining`;
            } else {
                counter.classList.remove('show');
            }
            if (addBtn) addBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Error updating views counter:', error);
    }
}

// Handle touch events for mobile swipe
let touchStartY = 0;
let touchEndY = 0;

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartY - touchEndY;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swipe up - next reel
            currentReelIndex++;
            scrollToReel(currentReelIndex);
        } else if (diff < 0 && currentReelIndex > 0) {
            // Swipe down - previous reel
            currentReelIndex--;
            scrollToReel(currentReelIndex);
        }
    }
}

function setupTouchHandling() {
    const container = document.getElementById('reelsContainer');
    if (!container) return;
    
    container.addEventListener('touchstart', (e) => {
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    container.addEventListener('touchend', (e) => {
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    }, { passive: true });
}

// Enable autoplay on user interaction (click anywhere on page)
let userInteracted = false;
document.addEventListener('click', () => {
    if (!userInteracted) {
        userInteracted = true;
        // Try to play first video if it exists
        const firstVideo = document.querySelector('.reel-video');
        if (firstVideo && firstVideo.paused) {
            firstVideo.muted = false;
            firstVideo.play().catch(e => {
                console.log('Error playing after user interaction:', e);
            });
        }
    }
}, { once: true });

// Load reels when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing...');
    
    // Setup form handlers after DOM is ready
    const loginFormEl = document.getElementById('loginForm');
    if (loginFormEl && !loginFormEl.hasAttribute('data-listener-added')) {
        loginFormEl.setAttribute('data-listener-added', 'true');
        loginFormEl.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            const errorDiv = document.getElementById('loginError');
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                
                if (data.success) {
                    isLoggedIn = true;
                    viewsCount = 0;
                    viewsRemaining = null;
                    closeLoginModal();
                    updateViewsCounter();
                    loadReels();
                } else {
                    errorDiv.textContent = data.error || 'Login failed';
                }
            } catch (error) {
                errorDiv.textContent = 'Error: ' + error.message;
            }
        });
    }
    
    const registerFormEl = document.getElementById('registerForm');
    if (registerFormEl && !registerFormEl.hasAttribute('data-listener-added')) {
        registerFormEl.setAttribute('data-listener-added', 'true');
        registerFormEl.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('registerUsername').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const errorDiv = document.getElementById('registerError');
            
            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                const data = await response.json();
                
                if (data.success) {
                    isLoggedIn = true;
                    viewsCount = 0;
                    viewsRemaining = null;
                    closeLoginModal();
                    updateViewsCounter();
                    loadReels();
                } else {
                    errorDiv.textContent = data.error || 'Registration failed';
                }
            } catch (error) {
                errorDiv.textContent = 'Error: ' + error.message;
            }
        });
    }
    
    checkAuthStatus().then(() => {
        loadReels();
    }).catch(err => {
        console.error('Error in initialization:', err);
        loadReels(); // Try to load reels anyway
    });
});
