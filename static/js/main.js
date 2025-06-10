// main.js - Fixed Navigation and Chart Issues

class OptimizedNTVisionDashboard {
    constructor() {
        this.cameras = {
            "Front Gate Camera": "Front Gate Camera",
            "Main Entrance": "Main Entrance", 
            "Parking Area": "Parking Area",
            "Lobby Camera": "Lobby Camera"
        };
        
        this.currentCamera = 'Front Gate Camera';
        this.isAutoRefresh = true;
        this.refreshInterval = 10000; // 10 seconds
        this.charts = {};
        this.notifications = [];
        this.lastUpdateTime = 0;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        // Performance optimization settings
        this.updateThrottle = 2000;
        this.maxConcurrentRequests = 2;
        this.activeRequests = 0;
        
        // Chart initialization flags
        this.chartsInitialized = {
            analytics: false,
            trends: false,
            performance: false
        };
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing Optimized NT Vision Dashboard...');
        
        this.initializeEventListeners();
        this.initializeTheme();
        this.initializeNavigation();
        this.initializeClock();
        this.setupCameraGridOptimized();
        this.loadInitialDataOptimized();
        this.startOptimizedAutoRefresh();
        
        console.log('✅ Optimized Dashboard initialized successfully');
    }

    initializeEventListeners() {
        // Use event delegation for better performance
        document.addEventListener('click', (e) => {
            // Sidebar toggle
            if (e.target.closest('#sidebar-toggle')) {
                this.toggleSidebar();
                return;
            }
            
            // Navigation links
            if (e.target.closest('.nav-link')) {
                e.preventDefault();
                const link = e.target.closest('.nav-link');
                const href = link.getAttribute('href');
                
                // Skip if it's the export data link (removed) or has no href
                if (!href || href === '#') {
                    return;
                }
                
                const target = href.substring(1);
                this.navigateToPage(target);
                return;
            }
            
            // Notifications button
            if (e.target.closest('#notifications')) {
                this.toggleNotifications();
                return;
            }
            
            // Period buttons
            if (e.target.closest('.period-btn')) {
                const period = e.target.closest('.period-btn').dataset.period;
                this.updateChartPeriod(period);
                return;
            }
            
            // Modal close
            if (e.target.closest('.modal-close')) {
                this.closeModal();
                return;
            }
            
            // Panel refresh
            if (e.target.closest('.panel-btn')) {
                this.refreshPanelDataThrottled();
                return;
            }
        });

        // Debounced input handlers
        const searchInput = document.getElementById('detection-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.filterDetections(e.target.value);
            }, 300));
        }

        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) {
            dateFilter.addEventListener('change', this.debounce((e) => {
                this.filterByDate(e.target.value);
            }, 500));
        }

        // Quality selector
        const qualitySelector = document.querySelector('.quality-selector');
        if (qualitySelector) {
            qualitySelector.addEventListener('change', (e) => {
                this.changeVideoQuality(e.target.value);
            });
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    setupCameraGridOptimized() {
        const cameraGrid = document.getElementById('camera-grid');
        if (!cameraGrid) return;

        cameraGrid.style.display = 'flex';
        cameraGrid.style.flexDirection = 'row';
        cameraGrid.style.gap = '12px';
        cameraGrid.style.overflowX = 'auto';
        cameraGrid.style.padding = '12px';

        const fragment = document.createDocumentFragment();

        Object.keys(this.cameras).forEach((cameraName, index) => {
            const cameraCard = document.createElement('div');
            cameraCard.className = `camera-card ${index === 0 ? 'active' : ''}`;
            cameraCard.dataset.cameraId = cameraName;
            cameraCard.style.minWidth = '200px';
            cameraCard.style.flexShrink = '0';

            cameraCard.innerHTML = `
                <div class="camera-header">
                    <h4>${this.formatCameraName(cameraName)}</h4>
                    <span class="camera-status online">
                        <i class="fas fa-circle"></i>
                        LIVE
                    </span>
                </div>
                <div class="camera-preview">
                    <img src="/video_feed?camera_id=${encodeURIComponent(cameraName)}&quality=low" 
                        alt="${cameraName}" 
                        loading="lazy"
                        onerror="this.src='/api/placeholder/200/150'">
                </div>
            `;

            cameraCard.addEventListener('click', () => {
                this.switchCameraOptimized(cameraName);
            });

            fragment.appendChild(cameraCard);
        });

        cameraGrid.innerHTML = '';
        cameraGrid.appendChild(fragment);
        this.updateMainVideoFeedOptimized();
    }

    formatCameraName(cameraName) {
        const nameMap = {
            "Front Gate Camera": "Front Gate",
            "Main Entrance": "Main Entrance",
            "Parking Area": "Parking", 
            "Lobby Camera": "Lobby"
        };
        return nameMap[cameraName] || cameraName;
    }

    updateMainVideoFeedOptimized() {
        const videoFeed = document.getElementById('main-video-feed');
        if (videoFeed) {
            const timestamp = Date.now();
            videoFeed.src = `/video_feed?camera_id=${encodeURIComponent(this.currentCamera)}&t=${timestamp}`;
            
            videoFeed.onerror = () => {
                console.warn(`Failed to load video feed for ${this.currentCamera}`);
                videoFeed.src = '/api/placeholder/800/600';
            };
        }
    }

    initializeTheme() {
        document.body.setAttribute('data-theme', 'dark');
    }

    initializeNavigation() {
        this.navigateToPage('dashboard');
    }

    initializeClock() {
        this.updateClock();
        setInterval(() => this.updateClock(), 5000);
    }

    // FIXED: Initialize charts only when needed and with proper error handling
    initializeAnalyticsChartOptimized() {
        if (this.chartsInitialized.analytics) return;
        
        const analyticsCanvas = document.getElementById('analytics-chart');
        if (analyticsCanvas) {
            try {
                this.charts.analytics = new Chart(analyticsCanvas, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Detections',
                            data: [],
                            borderColor: '#2563eb',
                            backgroundColor: 'rgba(37, 99, 235, 0.1)',
                            tension: 0.4,
                            fill: true,
                            pointRadius: 2,
                            pointHoverRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                ticks: { stepSize: 1 }
                            },
                            x: {
                                grid: { color: 'rgba(0, 0, 0, 0.1)' }
                            }
                        }
                    }
                });
                this.chartsInitialized.analytics = true;
                console.log('✅ Analytics chart initialized');
            } catch (error) {
                console.error('❌ Failed to initialize analytics chart:', error);
            }
        }
    }

    initializeTrendsChartOptimized() {
        if (this.chartsInitialized.trends) return;
        
        const trendsCanvas = document.getElementById('trends-chart');
        if (trendsCanvas) {
            try {
                this.charts.trends = new Chart(trendsCanvas, {
                    type: 'bar',
                    data: {
                        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        datasets: [{
                            label: 'Daily Detections',
                            data: [0, 0, 0, 0, 0, 0, 0],
                            backgroundColor: '#2563eb',
                            borderRadius: 3,
                            borderSkipped: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true } }
                    }
                });
                this.chartsInitialized.trends = true;
                console.log('✅ Trends chart initialized');
            } catch (error) {
                console.error('❌ Failed to initialize trends chart:', error);
            }
        }
    }

    initializePerformanceChartOptimized() {
        if (this.chartsInitialized.performance) return;
        
        const performanceCanvas = document.getElementById('performance-chart');
        if (performanceCanvas) {
            try {
                this.charts.performance = new Chart(performanceCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: ['Front Gate', 'Main Entrance', 'Parking', 'Lobby'],
                        datasets: [{
                            data: [0, 0, 0, 0],
                            backgroundColor: ['#2563eb', '#f59e0b', '#10b981', '#06b6d4'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '60%',
                        animation: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { padding: 15 }
                            }
                        }
                    }
                });
                this.chartsInitialized.performance = true;
                console.log('✅ Performance chart initialized');
            } catch (error) {
                console.error('❌ Failed to initialize performance chart:', error);
            }
        }
    }

    async loadInitialDataOptimized() {
        try {
            this.showLoadingState(true);
            
            await this.updateSystemStatsOptimized();
            await this.updateDetectionsOptimized();
            
            setTimeout(async () => {
                await this.updateCameraStatusOptimized();
                await this.updateActivityStreamOptimized();
            }, 1000);
            
            this.showLoadingState(false);
            this.retryCount = 0;
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.handleDataLoadError(error);
        }
    }

    showLoadingState(isLoading) {
        const loadingElements = document.querySelectorAll('.loading-spinner');
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'flex' : 'none';
        });
    }

    handleDataLoadError(error) {
        this.retryCount++;
        
        if (this.retryCount < this.maxRetries) {
            console.log(`Retrying data load... (${this.retryCount}/${this.maxRetries})`);
            setTimeout(() => this.loadInitialDataOptimized(), 3000);
        } else {
            this.showNotification('Unable to load dashboard data. Check connection.', 'error');
        }
    }

    async updateSystemStatsOptimized() {
        if (this.activeRequests >= this.maxConcurrentRequests) {
            console.log('⏳ Skipping system stats update - too many active requests');
            return;
        }

        try {
            this.activeRequests++;
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch('/get_system_stats', {
                signal: controller.signal,
                cache: 'no-cache'
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const stats = await response.json();
            
            const activeCameras = document.getElementById('active-cameras');
            if (activeCameras) {
                activeCameras.textContent = `${stats.active_cameras}/${stats.total_cameras}`;
            }
            
            if (stats.uptime) {
                const uptimeElement = document.getElementById('system-uptime');
                if (uptimeElement) {
                    uptimeElement.textContent = this.formatUptime(stats.uptime);
                }
            }
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Error updating system stats:', error);
                this.setDefaultSystemStats();
            }
        } finally {
            this.activeRequests--;
        }
    }

    setDefaultSystemStats() {
        const activeCameras = document.getElementById('active-cameras');
        if (activeCameras) activeCameras.textContent = '0/4';
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    }

    async updateDetectionsOptimized() {
        if (this.activeRequests >= this.maxConcurrentRequests) {
            console.log('⏳ Skipping detections update - too many active requests');
            return;
        }

        try {
            this.activeRequests++;
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000);
            
            const response = await fetch('/get_all_detections', {
                signal: controller.signal,
                cache: 'no-cache'
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            this.updateDetectionCountersOptimized(data.total_counts);
            this.updateDetectionsTableOptimized(data.recent_detections || []);
            this.updateAnalyticsChartOptimized(data.recent_detections || []);
            this.updatePerformanceChartOptimized(data.total_counts);
            
            this.lastUpdateTime = Date.now();
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Error updating detections:', error);
                this.setDefaultDetectionData();
            }
        } finally {
            this.activeRequests--;
        }
    }

    updateDetectionCountersOptimized(totalCounts) {
        const totalDetections = document.getElementById('total-detections');
        if (totalDetections) {
            const total = totalCounts.total || 0;
            this.animateCounterOptimized(totalDetections, total);
        }
        
        const todayDetections = document.getElementById('today-detections');
        if (todayDetections) {
            const today = new Date().toISOString().split('T')[0];
            let todayCount = 0;
            this.animateCounterOptimized(todayDetections, todayCount);
        }
    }

    animateCounterOptimized(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const difference = targetValue - currentValue;
        
        if (Math.abs(difference) <= 1) {
            element.textContent = targetValue;
            return;
        }
        
        const increment = Math.ceil(difference / 10);
        const newValue = currentValue + increment;
        
        element.textContent = Math.abs(newValue - targetValue) < Math.abs(increment) ? targetValue : newValue;
        
        if (newValue !== targetValue) {
            requestAnimationFrame(() => this.animateCounterOptimized(element, targetValue));
        }
    }

    setDefaultDetectionData() {
        const totalDetections = document.getElementById('total-detections');
        const todayDetections = document.getElementById('today-detections');
        
        if (totalDetections) totalDetections.textContent = '0';
        if (todayDetections) todayDetections.textContent = '0';
    }

    updateDetectionsTableOptimized(detections) {
        const tbody = document.getElementById('detections-tbody');
        if (!tbody) return;
        
        const fragment = document.createDocumentFragment();
        
        if (detections.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="5" class="no-data">
                    <i class="fas fa-search"></i>
                    <p>No detections found</p>
                </td>
            `;
            fragment.appendChild(row);
        } else {
            const limitedDetections = detections.slice(0, 50);
            
            limitedDetections.forEach(detection => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${this.formatDateTime(detection.timestamp)}</td>
                    <td>${this.formatCameraName(detection.camera_id)}</td>
                    <td>
                        <span class="confidence-badge confidence-${this.getConfidenceLevel(detection.confidence)}">
                            ${Math.round(detection.confidence)}%
                        </span>
                    </td>
                    <td>
                        ${detection.image_path ? 
                            `<img src="/image/${detection.image_path}" class="thumbnail" alt="Detection" loading="lazy" onclick="window.ntDashboard.showDetectionModal('${detection.image_path}', '${detection.camera_id}', '${detection.timestamp}', ${detection.confidence})">` : 
                            '<span class="no-data">No image</span>'
                        }
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="action-btn view" title="View Details" onclick="window.ntDashboard.showDetectionModal('${detection.image_path}', '${detection.camera_id}', '${detection.timestamp}', ${detection.confidence})">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${detection.image_path ? 
                                `<button class="action-btn download" title="Download" onclick="window.ntDashboard.downloadDetection('${detection.image_path}')">
                                    <i class="fas fa-download"></i>
                                </button>` : ''
                            }
                            <button class="action-btn delete" title="Delete" onclick="window.ntDashboard.deleteDetectionOptimized(${detection.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                fragment.appendChild(row);
            });
        }
        
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
    }

    async updateActivityStreamOptimized() {
        try {
            const response = await fetch('/get_all_detections', {
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            const activityStream = document.getElementById('activity-stream');
            if (!activityStream) return;
            
            const recentDetections = data.recent_detections?.slice(0, 3) || [];
            
            if (recentDetections.length === 0) {
                activityStream.innerHTML = `
                    <div class="activity-placeholder">
                        <i class="fas fa-search"></i>
                        <p>Monitoring for activity...</p>
                    </div>
                `;
                return;
            }
            
            const fragment = document.createDocumentFragment();
            
            recentDetections.forEach(detection => {
                const activityItem = document.createElement('div');
                activityItem.className = 'activity-item';
                activityItem.innerHTML = `
                    <div class="activity-icon">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="activity-details">
                        <h4>Person Detected</h4>
                        <p>${this.formatCameraName(detection.camera_id)} - ${Math.round(detection.confidence)}%</p>
                        <span class="activity-time">${this.getTimeAgo(detection.timestamp)}</span>
                    </div>
                `;
                fragment.appendChild(activityItem);
            });
            
            activityStream.innerHTML = '';
            activityStream.appendChild(fragment);
            
        } catch (error) {
            console.error('Error updating activity stream:', error);
            this.setDefaultActivityStream();
        }
    }

    setDefaultActivityStream() {
        const activityStream = document.getElementById('activity-stream');
        if (activityStream) {
            activityStream.innerHTML = `
                <div class="activity-placeholder">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load activity</p>
                </div>
            `;
        }
    }

    updateAnalyticsChartOptimized(detections) {
        // Initialize chart if not already done and we're on dashboard
        if (!this.chartsInitialized.analytics) {
            this.initializeAnalyticsChartOptimized();
        }
        
        if (!this.charts.analytics || !detections) return;
        
        const hourlyData = this.groupDetectionsByHourOptimized(detections);
        
        this.charts.analytics.data.labels = hourlyData.labels;
        this.charts.analytics.data.datasets[0].data = hourlyData.data;
        this.charts.analytics.update('none');
    }

    updatePerformanceChartOptimized(totalCounts) {
        // Initialize chart if not already done and we're on reports page
        if (!this.chartsInitialized.performance) {
            this.initializePerformanceChartOptimized();
        }
        
        if (!this.charts.performance || !totalCounts) return;
        
        const cameraData = [
            totalCounts['Front Gate Camera'] || 0,
            totalCounts['Main Entrance'] || 0,
            totalCounts['Parking Area'] || 0,
            totalCounts['Lobby Camera'] || 0
        ];
        
        this.charts.performance.data.datasets[0].data = cameraData;
        this.charts.performance.update('none');
    }

    groupDetectionsByHourOptimized(detections) {
        const hours = [];
        const data = [];
        const now = new Date();
        
        for (let i = 11; i >= 0; i--) {
            const hour = new Date(now.getTime() - (i * 60 * 60 * 1000));
            hours.push(hour.getHours().toString().padStart(2, '0') + ':00');
            data.push(0);
        }
        
        detections.forEach(detection => {
            const detectionTime = new Date(detection.timestamp);
            const hoursDiff = Math.floor((now - detectionTime) / (1000 * 60 * 60));
            
            if (hoursDiff >= 0 && hoursDiff < 12) {
                const index = 11 - hoursDiff;
                if (index >= 0 && index < data.length) {
                    data[index]++;
                }
            }
        });
        
        return { labels: hours, data: data };
    }

    async updateCameraStatusOptimized() {
        const cameraCards = document.querySelectorAll('.camera-card');
        
        cameraCards.forEach((card) => {
            const statusElement = card.querySelector('.camera-status');
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-circle"></i> LIVE';
                statusElement.className = 'camera-status online';
            }
        });
    }

    switchCameraOptimized(cameraName) {
        if (!this.cameras[cameraName]) {
            console.warn(`Camera ${cameraName} not found`);
            return;
        }

        this.currentCamera = cameraName;
        
        document.querySelectorAll('.camera-card').forEach(card => {
            card.classList.toggle('active', card.dataset.cameraId === cameraName);
        });
        
        const cameraNameElement = document.getElementById('active-camera-name');
        if (cameraNameElement) {
            cameraNameElement.textContent = this.formatCameraName(cameraName);
        }
        
        this.updateMainVideoFeedOptimized();
        
        fetch(`/switch_camera/${encodeURIComponent(cameraName)}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.showNotification(`Switched to ${this.formatCameraName(cameraName)}`, 'success');
                } else {
                    throw new Error(data.message || 'Failed to switch camera');
                }
            })
            .catch(error => {
                console.error('Error switching camera:', error);
                this.showNotification('Error switching camera', 'error');
            });
    }

    showDetectionModal(imagePath, cameraId, timestamp, confidence) {
        const modal = document.getElementById('detection-modal');
        const modalImage = document.getElementById('modal-image');
        const modalTitle = document.getElementById('modal-title');
        const modalDetails = document.getElementById('modal-details');
        
        if (modal && modalImage && modalTitle && modalDetails) {
            modalTitle.textContent = 'Detection Details';
            modalImage.src = imagePath ? `/image/${imagePath}` : '/api/placeholder/400/300';
            modalImage.loading = 'lazy';
            
            modalDetails.innerHTML = `
                <div class="detection-details">
                    <h4>Detection Information</h4>
                    <p><strong>Camera:</strong> ${this.formatCameraName(cameraId)}</p>
                    <p><strong>Time:</strong> ${this.formatDateTime(timestamp)}</p>
                    <p><strong>Confidence:</strong> ${Math.round(confidence)}%</p>
                    <p><strong>Status:</strong> <span class="confidence-badge confidence-${this.getConfidenceLevel(confidence)}">${this.getConfidenceText(confidence)}</span></p>
                </div>
            `;
            
            modal.classList.add('active');
        }
    }

    downloadDetection(imagePath) {
        if (imagePath) {
            const link = document.createElement('a');
            link.href = `/image/${imagePath}`;
            link.download = imagePath.split('/').pop();
            link.click();
        }
    }

    async deleteDetectionOptimized(detectionId) {
        if (!confirm('Are you sure you want to delete this detection?')) return;

        try {
            const response = await fetch(`/delete_detection?id=${detectionId}`, { 
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                this.showNotification('Detection deleted successfully', 'success');
                this.refreshPanelDataThrottled();
            } else {
                throw new Error(result.message || 'Delete failed');
            }
        } catch (error) {
            console.error('Error deleting detection:', error);
            this.showNotification('Error deleting detection', 'error');
        }
    }

    refreshPanelDataThrottled() {
        if (this.refreshThrottleTimeout) {
            clearTimeout(this.refreshThrottleTimeout);
        }
        
        this.refreshThrottleTimeout = setTimeout(() => {
            this.updateDetectionsOptimized();
        }, this.updateThrottle);
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.premium-sidebar');
        const mainContent = document.querySelector('.premium-main');
        
        if (sidebar && mainContent) {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && typeof chart.resize === 'function') {
                        chart.resize();
                    }
                });
            }, 300);
        }
    }

    // FIXED: Navigation function with proper chart initialization
    navigateToPage(pageName) {
        console.log(`Navigating to: ${pageName}`);
        
        // Hide all content areas
        document.querySelectorAll('.content-area').forEach(area => {
            area.classList.remove('active');
        });
        
        // Show selected content area
        const targetArea = document.getElementById(`${pageName}-content`);
        if (targetArea) {
            targetArea.classList.add('active');
        }
        
        // Update navigation active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[href="#${pageName}"]`)?.closest('.nav-item');
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Update page title
        const pageTitle = document.getElementById('page-title');
        const currentPage = document.getElementById('current-page');
        
        const pageTitles = {
            'dashboard': 'Intelligence Dashboard',
            'surveillance': 'Live Surveillance',
            'detections': 'Detection History',
            'reports': 'Analytics & Reports'
        };
        
        if (pageTitle) pageTitle.textContent = pageTitles[pageName] || pageName;
        if (currentPage) currentPage.textContent = pageTitles[pageName] || pageName;
        
        // FIXED: Load page-specific data and initialize charts properly
        setTimeout(() => this.loadPageDataOptimized(pageName), 100);
    }

    // FIXED: Page data loading with proper chart handling
    loadPageDataOptimized(pageName) {
        console.log(`Loading data for page: ${pageName}`);
        
        switch(pageName) {
            case 'dashboard':
                // Initialize analytics chart if not done
                if (!this.chartsInitialized.analytics) {
                    setTimeout(() => this.initializeAnalyticsChartOptimized(), 200);
                }
                break;
                
            case 'surveillance':
                this.loadSurveillanceDataOptimized();
                break;
                
            case 'detections':
                this.updateDetectionsOptimized();
                break;
                
            case 'reports':
                this.loadReportsDataOptimized();
                break;
        }
    }

    loadSurveillanceDataOptimized() {
        const surveillanceGrid = document.getElementById('surveillance-grid');
        if (!surveillanceGrid) return;

        const fragment = document.createDocumentFragment();
        
        Object.keys(this.cameras).forEach(cameraName => {
            const cameraCard = document.createElement('div');
            cameraCard.className = 'surveillance-camera-card';
            
            cameraCard.innerHTML = `
                <div class="surveillance-camera-header">
                    <h3>
                        <i class="fas fa-video"></i>
                        ${this.formatCameraName(cameraName)}
                    </h3>
                    <span class="camera-status online">
                        <i class="fas fa-circle"></i>
                        LIVE
                    </span>
                </div>
                <div class="surveillance-camera-feed">
                    <img src="/video_feed?camera_id=${encodeURIComponent(cameraName)}&quality=medium" 
                         alt="${cameraName}"
                         loading="lazy"
                         onerror="this.src='/api/placeholder/480/270'">
                </div>
                <div class="surveillance-camera-footer">
                    <div class="camera-stats">
                        <div class="stat-item">
                            <i class="fas fa-users"></i>
                            <span class="stat-value">0</span>
                            <span>Detections</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-clock"></i>
                            <span class="stat-value">24/7</span>
                            <span>Active</span>
                        </div>
                    </div>
                </div>
            `;
            
            fragment.appendChild(cameraCard);
        });
        
        surveillanceGrid.innerHTML = '';
        surveillanceGrid.appendChild(fragment);
    }

    // FIXED: Reports data loading with proper chart initialization
    loadReportsDataOptimized() {
        console.log('Loading reports data...');
        
        // Initialize charts for reports page
        setTimeout(() => {
            if (!this.chartsInitialized.trends) {
                this.initializeTrendsChartOptimized();
            }
            if (!this.chartsInitialized.performance) {
                this.initializePerformanceChartOptimized();
            }
            
            // Load chart data after initialization
            setTimeout(() => {
                if (this.charts.trends) {
                    const weeklyData = this.generateWeeklyDataOptimized();
                    this.charts.trends.data.datasets[0].data = weeklyData;
                    this.charts.trends.update('none');
                }
            }, 300);
        }, 200);
    }

    generateWeeklyDataOptimized() {
        return Array.from({length: 7}, () => Math.floor(Math.random() * 30));
    }

    updateClock() {
        const now = new Date();
        
        const timeElement = document.getElementById('current-time');
        const dateElement = document.getElementById('current-date');
        
        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            });
        }
    }

    updateChartPeriod(period) {
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[data-period="${period}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        
        this.loadChartDataForPeriodOptimized(period);
    }

    async loadChartDataForPeriodOptimized(period) {
        try {
            const response = await fetch('/get_all_detections', {
                cache: 'no-cache'
            });
            const data = await response.json();
            
            let chartData;
            switch(period) {
                case '24h':
                    chartData = this.groupDetectionsByHourOptimized(data.recent_detections || []);
                    break;
                case '7d':
                    chartData = this.groupDetectionsByDayOptimized(data.recent_detections || [], 7);
                    break;
                case '30d':
                    chartData = this.groupDetectionsByDayOptimized(data.recent_detections || [], 30);
                    break;
                default:
                    chartData = this.groupDetectionsByHourOptimized(data.recent_detections || []);
            }
            
            if (this.charts.analytics) {
                this.charts.analytics.data.labels = chartData.labels;
                this.charts.analytics.data.datasets[0].data = chartData.data;
                this.charts.analytics.update('none');
            }
            
        } catch (error) {
            console.error('Error loading chart data:', error);
        }
    }

    groupDetectionsByDayOptimized(detections, days) {
        const labels = [];
        const data = [];
        const now = new Date();
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            data.push(0);
        }
        
        detections.forEach(detection => {
            const detectionTime = new Date(detection.timestamp);
            const daysDiff = Math.floor((now - detectionTime) / (1000 * 60 * 60 * 24));
            
            if (daysDiff >= 0 && daysDiff < days) {
                const index = days - 1 - daysDiff;
                if (index >= 0 && index < data.length) {
                    data[index]++;
                }
            }
        });
        
        return { labels, data };
    }

    changeVideoQuality(quality) {
        console.log(`Changing video quality to: ${quality}`);
        this.showNotification(`Video quality changed to ${quality.toUpperCase()}`, 'info');
        this.updateMainVideoFeedOptimized();
    }

    toggleNotifications() {
        const notificationBadge = document.getElementById('notification-count');
        if (notificationBadge) {
            const currentCount = parseInt(notificationBadge.textContent) || 0;
            notificationBadge.textContent = currentCount > 0 ? '0' : '3';
        }
        
        this.showNotification('Notifications panel (coming soon)', 'info');
    }

    filterDetections(searchTerm) {
        const rows = document.querySelectorAll('#detections-tbody tr');
        
        rows.forEach(row => {
            if (row.querySelector('.no-data')) return;
            
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm.toLowerCase()) ? '' : 'none';
        });
    }

    async filterByDate(dateValue) {
        if (!dateValue) {
            this.updateDetectionsOptimized();
            return;
        }
        
        try {
            const response = await fetch(`/get_detections_by_date?date=${dateValue}`);
            if (response.ok) {
                const data = await response.json();
                this.updateDetectionsTableOptimized(data.detections || []);
            }
        } catch (error) {
            console.error('Error filtering by date:', error);
            this.showNotification('Error filtering detections', 'error');
        }
    }

    closeModal() {
        const modals = document.querySelectorAll('.premium-modal.active');
        modals.forEach(modal => modal.classList.remove('active'));
    }

    showNotification(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="${icons[type]}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });
        
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 4000);
        
        const toasts = container.querySelectorAll('.toast');
        if (toasts.length > 3) {
            toasts[0].remove();
        }
    }

    startOptimizedAutoRefresh() {
        if (this.isAutoRefresh) {
            setInterval(() => {
                if (document.visibilityState === 'visible' && 
                    Date.now() - this.lastUpdateTime > this.refreshInterval &&
                    this.activeRequests < this.maxConcurrentRequests) {
                    
                    this.updateSystemStatsOptimized();
                    
                    setTimeout(() => {
                        this.updateDetectionsOptimized();
                    }, 1000);
                    
                    setTimeout(() => {
                        this.updateActivityStreamOptimized();
                    }, 2000);
                }
            }, this.refreshInterval);
        }
    }

    // Utility functions
    formatDateTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInSeconds = Math.floor((now - time) / 1000);
        
        if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    }

    getConfidenceLevel(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 60) return 'medium';
        return 'low';
    }

    getConfidenceText(confidence) {
        if (confidence >= 80) return 'High Confidence';
        if (confidence >= 60) return 'Medium Confidence';
        return 'Low Confidence';
    }

    // Debug functions
    debugInfo() {
        return {
            currentCamera: this.currentCamera,
            cameras: this.cameras,
            lastUpdateTime: new Date(this.lastUpdateTime).toLocaleString(),
            chartsInitialized: this.chartsInitialized,
            activeRequests: this.activeRequests,
            autoRefresh: this.isAutoRefresh
        };
    }

    resetDashboard() {
        this.retryCount = 0;
        this.lastUpdateTime = 0;
        this.activeRequests = 0;
        
        // Reset chart initialization flags
        this.chartsInitialized = {
            analytics: false,
            trends: false,
            performance: false
        };
        
        // Destroy existing charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
        
        this.loadInitialDataOptimized();
        this.showNotification('Dashboard reset', 'info');
    }
}

// Initialize optimized dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Hide loading screen
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 300);
        }, 500);
    }
    
    window.ntDashboard = new OptimizedNTVisionDashboard();
});

// Optimized page visibility handler
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.ntDashboard) {
        setTimeout(() => {
            if (window.ntDashboard.activeRequests === 0) {
                window.ntDashboard.updateSystemStatsOptimized();
            }
        }, 2000);
    }
});

// Optimized resize handler
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (window.ntDashboard && window.ntDashboard.charts) {
            Object.values(window.ntDashboard.charts).forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        }
    }, 300);
});

// Connection status handlers
window.addEventListener('online', () => {
    if (window.ntDashboard) {
        window.ntDashboard.showNotification('Connection restored', 'success');
        setTimeout(() => {
            window.ntDashboard.loadInitialDataOptimized();
        }, 1000);
    }
});

window.addEventListener('offline', () => {
    if (window.ntDashboard) {
        window.ntDashboard.showNotification('Connection lost', 'warning');
    }
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    if (window.ntDashboard && event.error.name !== 'AbortError') {
        window.ntDashboard.showNotification('An error occurred. Please refresh if issues persist.', 'error');
    }
});

// Export dashboard class
window.OptimizedNTVisionDashboard = OptimizedNTVisionDashboard;

// Console helper functions
window.debugDashboard = () => {
    return window.ntDashboard ? window.ntDashboard.debugInfo() : 'Dashboard not initialized';
};

window.resetDashboard = () => {
    if (window.ntDashboard) {
        window.ntDashboard.resetDashboard();
    }
};

// Performance monitoring
window.monitorPerformance = () => {
    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.duration > 100) {
                console.warn(`Slow operation: ${entry.name} took ${entry.duration.toFixed(2)}ms`);
            }
        }
    });
    
    observer.observe({ entryTypes: ['measure', 'navigation'] });
    console.log('Performance monitoring enabled');
};