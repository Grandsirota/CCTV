// main.js - Fixed Camera Display System
let cameras = [];
let currentCamera = '';
let detectionData = [];
let refreshInterval;
let systemStats = {};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing NT Security System...');
    
    // Get cameras from template data or use default
    if (window.cameraList && window.cameraList.length > 0) {
        cameras = window.cameraList;
    } else {
        cameras = [
            'Front Gate Camera',
            'Main Entrance', 
            'Parking Area',
            'Lobby Camera'
        ];
    }
    
    currentCamera = cameras[0];
    
    initializeApp();
    setupEventListeners();
    startDataRefresh();
    
    // Initialize datetime display
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    console.log('✅ System initialized successfully');
});

function initializeApp() {
    // Initialize navigation
    initializeNavigation();
    
    // Initialize camera displays
    initializeCameraDisplays();
    
    // Load initial data
    loadDashboardData();
    
    // Show dashboard by default
    showContent('dashboard');
}

function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Add active class to clicked item
            this.parentElement.classList.add('active');
            
            // Get target from href
            const target = this.getAttribute('href').replace('#', '');
            showContent(target);
        });
    });
    
    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.premium-sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }
}

function initializeCameraDisplays() {
    console.log('📹 Initializing camera displays...');
    
    // Initialize dashboard camera grid
    const dashboardGrid = document.getElementById('camera-grid');
    if (dashboardGrid) {
        createCameraGrid(dashboardGrid, 'dashboard');
    }
    
    // Initialize surveillance grid  
    const surveillanceGrid = document.getElementById('surveillance-grid');
    if (surveillanceGrid) {
        createSurveillanceGrid(surveillanceGrid);
    }
    
    // Initialize main video feed
    updateMainVideoFeed();
    
    console.log('✅ Camera displays initialized');
}

function createCameraGrid(container, type = 'dashboard') {
    if (!container) return;
    
    container.innerHTML = '';
    
    cameras.forEach((camera, index) => {
        const cameraCard = document.createElement('div');
        cameraCard.className = `camera-card ${index === 0 ? 'active' : ''}`;
        cameraCard.dataset.camera = camera;
        
        const safeCameraName = camera.replace(/\s+/g, '');
        
        cameraCard.innerHTML = `
            <div class="camera-preview">
                <img src="/video_feed?camera_id=${encodeURIComponent(camera)}" 
                     alt="${camera}"
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 300 200\\"><rect width=\\"100%\\" height=\\"100%\\" fill=\\"%23333\\"/><text x=\\"50%\\" y=\\"50%\\" text-anchor=\\"middle\\" fill=\\"white\\">Camera Offline</text></svg>'">
                <div class="camera-overlay">
                    <div class="camera-status">
                        <span class="status-dot online"></span>
                        <span>LIVE</span>
                    </div>
                </div>
            </div>
            <div class="camera-info">
                <h4>${camera}</h4>
                <div class="camera-stats">
                    <span class="detection-count">0 detections</span>
                </div>
            </div>
        `;
        
        // Add click handler
        cameraCard.addEventListener('click', function() {
            selectCamera(camera, this);
        });
        
        container.appendChild(cameraCard);
    });
    
    console.log(`📹 Created ${type} camera grid with ${cameras.length} cameras`);
}

function createSurveillanceGrid(container) {
    if (!container) return;
    
    container.innerHTML = '';
    
    cameras.forEach((camera, index) => {
        const cameraPanel = document.createElement('div');
        cameraPanel.className = 'surveillance-panel';
        cameraPanel.dataset.camera = camera;
        
        cameraPanel.innerHTML = `
            <div class="surveillance-header">
                <h3>${camera}</h3>
                <div class="surveillance-controls">
                    <span class="status-indicator">
                        <span class="status-dot online"></span>
                        LIVE
                    </span>
                </div>
            </div>
            <div class="surveillance-video">
                <img src="/video_feed?camera_id=${encodeURIComponent(camera)}" 
                     alt="${camera} Live Feed"
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 400 300\\"><rect width=\\"100%\\" height=\\"100%\\" fill=\\"%23222\\"/><text x=\\"50%\\" y=\\"45%\\" text-anchor=\\"middle\\" fill=\\"white\\" font-size=\\"16\\">Camera Offline</text><text x=\\"50%\\" y=\\"55%\\" text-anchor=\\"middle\\" fill=\\"white\\" font-size=\\"12\\">${camera}</text></svg>'">
                <div class="surveillance-overlay">
                    <div class="detection-indicator" style="display: none;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>PERSON DETECTED</span>
                    </div>
                </div>
            </div>
            <div class="surveillance-footer">
                <div class="detection-stats">
                    <span class="detection-count">0 detections today</span>
                </div>
                <div class="camera-actions">
                    <button class="action-btn" onclick="refreshCamera('${camera}')" title="Refresh">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <button class="action-btn" onclick="selectMainCamera('${camera}')" title="View in Main">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(cameraPanel);
    });
    
    console.log(`📹 Created surveillance grid with ${cameras.length} cameras`);
}

function selectCamera(cameraId, element) {
    console.log(`📹 Selecting camera: ${cameraId}`);
    
    currentCamera = cameraId;
    
    // Update active states in camera grid
    document.querySelectorAll('.camera-card').forEach(card => {
        card.classList.remove('active');
    });
    
    if (element) {
        element.classList.add('active');
    }
    
    // Update main video feed
    updateMainVideoFeed();
    
    // Update active camera name
    const activeNameElement = document.getElementById('active-camera-name');
    if (activeNameElement) {
        activeNameElement.textContent = cameraId;
    }
    
    // Send switch request to backend
    fetch(`/switch_camera/${encodeURIComponent(cameraId)}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(`✅ Switched to ${cameraId}`);
                showToast(`Switched to ${cameraId}`, 'success');
            } else {
                console.error(`❌ Failed to switch to ${cameraId}:`, data.message);
                showToast(`Failed to switch camera: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            console.error('❌ Camera switch error:', error);
            showToast('Failed to switch camera', 'error');
        });
}

function updateMainVideoFeed() {
    const mainVideoFeed = document.getElementById('main-video-feed');
    if (!mainVideoFeed || !currentCamera) return;
    
    console.log(`📹 Updating main video feed to: ${currentCamera}`);
    
    // Create new image URL with timestamp to prevent caching
    const timestamp = new Date().getTime();
    const newSrc = `/video_feed?camera_id=${encodeURIComponent(currentCamera)}&t=${timestamp}`;
    
    // Show loading state
    const videoContainer = mainVideoFeed.parentElement;
    const loadingIndicator = videoContainer.querySelector('.video-loading');
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    }
    
    // Update src
    mainVideoFeed.src = newSrc;
    
    // Handle load event
    mainVideoFeed.onload = function() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        console.log(`✅ Main video feed updated: ${currentCamera}`);
    };
    
    // Handle error
    mainVideoFeed.onerror = function() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        console.error(`❌ Failed to load video feed: ${currentCamera}`);
        this.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><rect width="100%" height="100%" fill="#1a1a1a"/><text x="50%" y="45%" text-anchor="middle" fill="white" font-size="24">Camera Offline</text><text x="50%" y="55%" text-anchor="middle" fill="#666" font-size="16">${currentCamera}</text></svg>`;
    };
}

function showContent(contentId) {
    console.log(`🔄 Switching to content: ${contentId}`);
    
    // Hide all content areas
    document.querySelectorAll('.content-area').forEach(area => {
        area.classList.remove('active');
    });
    
    // Show selected content
    const targetContent = document.getElementById(`${contentId}-content`);
    if (targetContent) {
        targetContent.classList.add('active');
    }
    
    // Update page title and breadcrumb
    updatePageTitle(contentId);
    
    // Load content-specific data
    switch(contentId) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'surveillance':
            loadSurveillanceData();
            break;
        case 'detections':
            loadDetectionHistory();
            break;
        case 'reports':
            loadReportsData();
            break;
    }
}

function updatePageTitle(contentId) {
    const titles = {
        'dashboard': 'Intelligence Dashboard',
        'surveillance': 'Live Surveillance',
        'detections': 'Detection History',
        'reports': 'Analytics & Reports'
    };
    
    const breadcrumbs = {
        'dashboard': 'Dashboard',
        'surveillance': 'Live Surveillance', 
        'detections': 'Detection History',
        'reports': 'Reports'
    };
    
    const titleElement = document.getElementById('page-title');
    const breadcrumbElement = document.getElementById('current-page');
    
    if (titleElement) {
        titleElement.textContent = titles[contentId] || 'NT Security';
    }
    
    if (breadcrumbElement) {
        breadcrumbElement.textContent = breadcrumbs[contentId] || contentId;
    }
}

function loadDashboardData() {
    console.log('📊 Loading dashboard data...');
    
    // Load detection data
    fetch('/get_all_detections')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
            updateActivityStream(data.recent_detections);
        })
        .catch(error => {
            console.error('❌ Dashboard data error:', error);
            showToast('Failed to load dashboard data', 'error');
        });
    
    // Load system stats
    loadSystemStats();
}

function updateDashboardStats(data) {
    const totalCount = data.total_counts?.total || 0;
    const todayCount = getTodayDetections(data.recent_detections);
    
    // Update stat cards
    updateStatCard('total-detections', totalCount);
    updateStatCard('today-detections', todayCount);
    updateStatCard('active-cameras', `${cameras.length}/${cameras.length}`);
    
    // Update camera grid detection counts
    updateCameraDetectionCounts(data.total_counts);
}

function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        // Add loading spinner
        const spinner = element.parentElement.querySelector('.loading-spinner');
        if (spinner) {
            spinner.style.display = 'block';
        }
        
        // Animate number change
        animateNumber(element, value);
        
        // Hide spinner
        setTimeout(() => {
            if (spinner) {
                spinner.style.display = 'none';
            }
        }, 500);
    }
}

function animateNumber(element, targetValue) {
    const currentValue = parseInt(element.textContent) || 0;
    const increment = Math.ceil((targetValue - currentValue) / 20);
    
    if (increment === 0) {
        element.textContent = targetValue;
        return;
    }
    
    let current = currentValue;
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= targetValue) || (increment < 0 && current <= targetValue)) {
            current = targetValue;
            clearInterval(timer);
        }
        element.textContent = current;
    }, 50);
}

function getTodayDetections(detections) {
    if (!detections) return 0;
    
    const today = new Date().toDateString();
    return detections.filter(detection => {
        const detectionDate = new Date(detection.timestamp).toDateString();
        return detectionDate === today;
    }).length;
}

function updateCameraDetectionCounts(totalCounts) {
    cameras.forEach(camera => {
        const count = totalCounts[camera] || 0;
        const cameraCard = document.querySelector(`[data-camera="${camera}"]`);
        if (cameraCard) {
            const countElement = cameraCard.querySelector('.detection-count');
            if (countElement) {
                countElement.textContent = `${count} detections`;
            }
        }
    });
}

function updateActivityStream(detections) {
    const activityStream = document.getElementById('activity-stream');
    if (!activityStream || !detections) return;
    
    if (detections.length === 0) {
        activityStream.innerHTML = `
            <div class="activity-placeholder">
                <i class="fas fa-search"></i>
                <p>No recent activity</p>
            </div>
        `;
        return;
    }
    
    const recentDetections = detections.slice(0, 10);
    activityStream.innerHTML = recentDetections.map(detection => `
        <div class="activity-item">
            <div class="activity-icon">
                <i class="fas fa-user"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">Person detected</div>
                <div class="activity-subtitle">${detection.camera_id}</div>
                <div class="activity-time">${formatTime(detection.timestamp)}</div>
            </div>
            <div class="activity-confidence">${Math.round(detection.confidence)}%</div>
        </div>
    `).join('');
}

function loadSurveillanceData() {
    console.log('📹 Loading surveillance data...');
    
    // Refresh surveillance grid if it exists
    const surveillanceGrid = document.getElementById('surveillance-grid');
    if (surveillanceGrid && surveillanceGrid.children.length === 0) {
        createSurveillanceGrid(surveillanceGrid);
    }
    
    // Refresh all camera feeds
    refreshAllCameraFeeds();
}

function refreshAllCameraFeeds() {
    console.log('🔄 Refreshing all camera feeds...');
    
    // Refresh main feed
    updateMainVideoFeed();
    
    // Refresh all camera previews
    document.querySelectorAll('img[src*="/video_feed"]').forEach(img => {
        const originalSrc = img.src.split('&t=')[0]; // Remove old timestamp
        const newSrc = `${originalSrc}&t=${new Date().getTime()}`;
        img.src = newSrc;
    });
    
    showToast('Camera feeds refreshed', 'success');
}

function loadDetectionHistory() {
    console.log('📋 Loading detection history...');
    
    const tableBody = document.getElementById('detections-tbody');
    if (!tableBody) return;
    
    // Show loading
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" class="loading-row">
                <div class="loading-spinner"></div>
                <p>Loading detections...</p>
            </td>
        </tr>
    `;
    
    fetch('/get_all_detections')
        .then(response => response.json())
        .then(data => {
            populateDetectionTable(data.recent_detections);
        })
        .catch(error => {
            console.error('❌ Detection history error:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="error-row">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load detection history</p>
                    </td>
                </tr>
            `;
        });
}

function populateDetectionTable(detections) {
    const tableBody = document.getElementById('detections-tbody');
    if (!tableBody) return;
    
    if (!detections || detections.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-row">
                    <i class="fas fa-search"></i>
                    <p>No detections found</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = detections.map(detection => `
        <tr>
            <td>${formatDateTime(detection.timestamp)}</td>
            <td>
                <div class="camera-cell">
                    <i class="fas fa-video"></i>
                    ${detection.camera_id}
                </div>
            </td>
            <td>
                <div class="confidence-cell">
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${detection.confidence}%"></div>
                    </div>
                    <span>${Math.round(detection.confidence)}%</span>
                </div>
            </td>
            <td>
                ${detection.image_path ? `
                    <img src="/image/${detection.image_path}" 
                         alt="Detection" 
                         class="detection-thumbnail"
                         onclick="showDetectionModal(${JSON.stringify(detection).replace(/"/g, '&quot;')})"
                         loading="lazy">
                ` : '<span class="no-image">No image</span>'}
            </td>
            <td>
                <div class="action-buttons">
                    ${detection.image_path ? `
                        <button class="action-btn view-btn" 
                                onclick="showDetectionModal(${JSON.stringify(detection).replace(/"/g, '&quot;')})"
                                title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                    ` : ''}
                    <button class="action-btn delete-btn" 
                            onclick="deleteDetection(${detection.id})"
                            title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function loadSystemStats() {
    fetch('/get_system_stats')
        .then(response => response.json())
        .then(stats => {
            systemStats = stats;
            updateSystemStatus(stats);
        })
        .catch(error => {
            console.error('❌ System stats error:', error);
        });
}

function updateSystemStatus(stats) {
    // Update uptime display
    const uptimeElement = document.getElementById('system-uptime');
    if (uptimeElement && stats.uptime) {
        uptimeElement.textContent = formatUptime(stats.uptime);
    }
    
    // Update health indicators
    const healthIndicator = document.querySelector('.health-check .health-indicator');
    if (healthIndicator) {
        const isHealthy = stats.cpu_percent < 80 && stats.memory_percent < 80;
        healthIndicator.className = `health-indicator ${isHealthy ? 'healthy' : 'warning'}`;
    }
}

function startDataRefresh() {
    // Refresh data every 30 seconds
    refreshInterval = setInterval(() => {
        const activeContent = document.querySelector('.content-area.active');
        if (activeContent) {
            const contentId = activeContent.id.replace('-content', '');
            
            switch(contentId) {
                case 'dashboard':
                    loadDashboardData();
                    break;
                case 'detections':
                    loadDetectionHistory();
                    break;
            }
        }
        
        // Always refresh system stats
        loadSystemStats();
    }, 30000);
    
    console.log('🔄 Started data refresh interval');
}

// Event Listeners
function setupEventListeners() {
    // Camera refresh button
    const refreshCamerasBtn = document.getElementById('refresh-cameras');
    if (refreshCamerasBtn) {
        refreshCamerasBtn.addEventListener('click', refreshAllCameraFeeds);
    }
    
    // Start all cameras button
    const startAllBtn = document.getElementById('start-all-cameras');
    if (startAllBtn) {
        startAllBtn.addEventListener('click', startAllCameras);
    }
    
    // Refresh surveillance button
    const refreshSurveillanceBtn = document.getElementById('refresh-surveillance');
    if (refreshSurveillanceBtn) {
        refreshSurveillanceBtn.addEventListener('click', refreshAllCameraFeeds);
    }
    
    // Detection search
    const detectionSearch = document.getElementById('detection-search');
    if (detectionSearch) {
        detectionSearch.addEventListener('input', filterDetections);
    }
    
    // Date filter
    const dateFilter = document.getElementById('date-filter');
    if (dateFilter) {
        dateFilter.addEventListener('change', filterDetectionsByDate);
    }
    
    // Clear filters
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearDetectionFilters);
    }
    
    // Modal close handlers
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    // Quality selector
    const qualitySelector = document.querySelector('.quality-selector');
    if (qualitySelector) {
        qualitySelector.addEventListener('change', changeVideoQuality);
    }
}

// Utility Functions
function startAllCameras() {
    console.log('🚀 Starting all cameras...');
    
    fetch('/start_all_cameras')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('All cameras started successfully', 'success');
                setTimeout(refreshAllCameraFeeds, 2000);
            } else {
                showToast(`Failed to start cameras: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            console.error('❌ Start cameras error:', error);
            showToast('Failed to start cameras', 'error');
        });
}

function refreshCamera(cameraId) {
    console.log(`🔄 Refreshing camera: ${cameraId}`);
    
    const cameraImages = document.querySelectorAll(`img[src*="${encodeURIComponent(cameraId)}"]`);
    cameraImages.forEach(img => {
        const originalSrc = img.src.split('&t=')[0];
        img.src = `${originalSrc}&t=${new Date().getTime()}`;
    });
    
    showToast(`${cameraId} refreshed`, 'success');
}

function selectMainCamera(cameraId) {
    selectCamera(cameraId);
    showContent('dashboard');
}

function changeVideoQuality(event) {
    const quality = event.target.value;
    console.log(`🎥 Changing video quality to: ${quality}`);
    
    // Update all video feeds with quality parameter
    document.querySelectorAll('img[src*="/video_feed"]').forEach(img => {
        const url = new URL(img.src);
        url.searchParams.set('quality', quality);
        url.searchParams.set('t', new Date().getTime());
        img.src = url.toString();
    });
    
    showToast(`Video quality changed to ${quality}`, 'success');
}

function filterDetections() {
    const searchTerm = document.getElementById('detection-search').value.toLowerCase();
    const rows = document.querySelectorAll('#detections-tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function filterDetectionsByDate() {
    const selectedDate = document.getElementById('date-filter').value;
    if (!selectedDate) return;
    
    const rows = document.querySelectorAll('#detections-tbody tr');
    rows.forEach(row => {
        const dateCell = row.querySelector('td:first-child');
        if (dateCell) {
            const rowDate = new Date(dateCell.textContent).toISOString().split('T')[0];
            row.style.display = rowDate === selectedDate ? '' : 'none';
        }
    });
}

function clearDetectionFilters() {
    document.getElementById('detection-search').value = '';
    document.getElementById('date-filter').value = '';
    
    document.querySelectorAll('#detections-tbody tr').forEach(row => {
        row.style.display = '';
    });
    
    showToast('Filters cleared', 'success');
}

function deleteDetection(detectionId) {
    if (!confirm('Are you sure you want to delete this detection?')) return;
    
    fetch(`/delete_detection?id=${detectionId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('Detection deleted', 'success');
                loadDetectionHistory();
            } else {
                showToast(`Failed to delete: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            console.error('❌ Delete error:', error);
            showToast('Failed to delete detection', 'error');
        });
}

function showDetectionModal(detection) {
    const modal = document.getElementById('detection-modal');
    const modalImage = document.getElementById('modal-image');
    const modalDetails = document.getElementById('modal-details');
    
    if (!modal || !modalImage || !modalDetails) return;
    
    // Set modal content
    modalImage.src = `/image/${detection.image_path}`;
    modalDetails.innerHTML = `
        <div class="detail-item">
            <label>Camera:</label>
            <span>${detection.camera_id}</span>
        </div>
        <div class="detail-item">
            <label>Time:</label>
            <span>${formatDateTime(detection.timestamp)}</span>
        </div>
        <div class="detail-item">
            <label>Confidence:</label>
            <span>${Math.round(detection.confidence)}%</span>
        </div>
    `;
    
    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('detection-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close">×</button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
    
    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });
}

function updateDateTime() {
    const now = new Date();
    
    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');
    
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}

function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('❌ Global error:', event.error);
    showToast('An error occurred. Check console for details.', 'error');
});

// Global functions for onclick handlers
window.refreshCamera = refreshCamera;
window.selectMainCamera = selectMainCamera;
window.showDetectionModal = showDetectionModal;
window.deleteDetection = deleteDetection;

console.log('📱 Main.js loaded successfully');