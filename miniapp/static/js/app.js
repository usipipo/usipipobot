/**
 * uSipipo Mini App - Main JavaScript
 *
 * Integración con Telegram WebApp SDK y lógica de la aplicación.
 *
 * ============================================================================
 * ROUTING GUIDE - Which URL prefix to use?
 * ============================================================================
 *
 * We have TWO parallel route systems:
 *
 * 1. /miniapp/... (Direct Web Navigation)
 *    - Use for: window.location.href, <a> links, browser navigation
 *    - Example: window.location.href = '/miniapp/dashboard'
 *    - Example: <a href="/miniapp/purchase">Comprar</a>
 *
 * 2. /miniapp/api/... (AJAX/Fetch API Calls)
 *    - Use for: fetch(), XMLHttpRequest, dynamic data loading
 *    - Example: fetch('/miniapp/api/user')
 *    - Example: fetch('/miniapp/api/create-stars-invoice', {method: 'POST'})
 *
 * 3. /api/v1/miniapp/... (Versioned API - External Use)
 *    - Use for: External API integrations, SDKs, backward compatibility
 *    - NOT used in frontend JavaScript (use #2 instead)
 *    - Example: External services, API clients, programmatic access
 *
 * ============================================================================
 */

(function() {
    'use strict';

    const tg = window.Telegram?.WebApp;

    if (tg) {
        tg.ready();
        tg.expand();

        tg.setHeaderColor('#0a0a0f');
        tg.setBackgroundColor('#0a0a0f');
        tg.enableClosingConfirmation();

        console.log('🤖 Telegram Mini App initialized');
        console.log('Platform:', tg.platform);
        console.log('Version:', tg.version);
        console.log('Color Scheme:', tg.colorScheme);

        // NOTE: Using /miniapp/... for navigation (NOT /api/v1/miniapp/...)
        // This is the direct web route for browser navigation
        document.addEventListener('backButtonClicked', function() {
            if (window.location.pathname !== '/miniapp/dashboard') {
                window.history.back();
            } else {
                tg.close();
            }
        });

        tg.BackButton.show();
        tg.BackButton.onClick(function() {
            // NOTE: Using /miniapp/... for navigation check (NOT /api/v1/miniapp/...)
            if (window.location.pathname !== '/miniapp/dashboard') {
                window.history.back();
            }
        });
    }

    function getInitData() {
        if (tg && tg.initData) {
            return tg.initData;
        }

        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('tgWebAppData') || '';
    }

    function appendInitDataToLinks() {
        const initData = getInitData();
        if (!initData) return;

        // Append initData to links that use /miniapp/... or /api/v1/miniapp/...
        // This ensures authentication is preserved during navigation
        document.querySelectorAll('a[href^="/miniapp/"], a[href^="/api/v1/miniapp/"]').forEach(link => {
            const url = new URL(link.href, window.location.origin);
            url.searchParams.set('tgWebAppData', initData);
            link.href = url.toString();
        });
    }

    function appendInitDataToForms() {
        const initData = getInitData();
        if (!initData) return;

        document.querySelectorAll('form').forEach(form => {
            let input = form.querySelector('input[name="tgWebAppData"]');
            if (!input) {
                input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'tgWebAppData';
                form.appendChild(input);
            }
            input.value = initData;
        });
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async function apiRequest(url, options = {}) {
        const initData = getInitData();
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (initData) {
            headers['X-Telegram-Init-Data'] = initData;
        }

        const urlObj = new URL(url, window.location.origin);
        if (initData && !urlObj.searchParams.has('tgWebAppData')) {
            urlObj.searchParams.set('tgWebAppData', initData);
        }

        try {
            const response = await fetch(urlObj.toString(), {
                ...options,
                headers
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: 'Error de conexión' };
        }
    }

    function showAlert(message) {
        if (tg) {
            tg.showAlert(message);
        } else {
            alert(message);
        }
    }

    function showConfirm(message) {
        return new Promise((resolve) => {
            if (tg) {
                tg.showConfirm(message, resolve);
            } else {
                resolve(confirm(message));
            }
        });
    }

    function hapticFeedback(type = 'impact') {
        if (tg && tg.HapticFeedback) {
            switch (type) {
                case 'impact':
                    tg.HapticFeedback.impactOccurred('medium');
                    break;
                case 'notification':
                    tg.HapticFeedback.notificationOccurred('success');
                    break;
                case 'selection':
                    tg.HapticFeedback.selectionChanged();
                    break;
            }
        }
    }

    // ========================================================================
    // LATENCY WIDGET - Server Latency Monitoring
    // ========================================================================

    let latencyData = {
        history: [],
        lastUpdate: null,
        pollInterval: null
    };

    async function fetchLatency() {
        try {
            const response = await apiRequest('/api/v1/miniapp/latency');

            if (response.status === 'ok') {
                updateLatencyWidget(response);
                hideLatencyError();
            } else {
                showLatencyError();
            }
        } catch (error) {
            console.error('Latency fetch error:', error);
            showLatencyError();
        }
    }

    function updateLatencyWidget(data) {
        const { current, history, quality_score, status_icon, status_label } = data;
        const pingMs = current.ping_ms;

        // Hide loading, show content
        document.getElementById('latency-loading').style.display = 'none';
        document.getElementById('latency-error').style.display = 'none';
        document.getElementById('latency-content').style.display = 'block';

        // Update value with color
        const valueEl = document.getElementById('latency-value');
        valueEl.textContent = pingMs.toFixed(0);
        valueEl.className = 'latency-value ' + getLatencyClass(quality_score);

        // Update badge
        const badge = document.getElementById('latency-badge');
        const badgeIcon = document.getElementById('latency-status-icon');
        const badgeLabel = document.getElementById('latency-status-label');

        badge.className = 'latency-badge ' + getLatencyClass(quality_score);
        badgeIcon.textContent = status_icon;
        badgeLabel.textContent = status_label;

        // Update sparkline
        renderSparkline(history);

        // Update timestamp
        latencyData.lastUpdate = new Date();
        latencyData.history = history;
        updateLatencyAge();

        // Haptic feedback on successful update
        hapticFeedback('selection');
    }

    function getLatencyClass(qualityScore) {
        if (qualityScore >= 75) return 'excellent';
        if (qualityScore >= 50) return 'normal';
        return 'poor';
    }

    function renderSparkline(history) {
        const svg = document.getElementById('latency-sparkline');
        const width = 280;
        const height = 60;
        const padding = 4;

        if (!history || history.length === 0) {
            svg.innerHTML = '';
            return;
        }

        const pingValues = history.map(h => h.ping_ms);
        const minPing = Math.min(...pingValues);
        const maxPing = Math.max(...pingValues);
        const range = maxPing - minPing || 1;

        // Generate path points
        const points = pingValues.map((ping, i) => {
            const x = (i / (pingValues.length - 1)) * (width - padding * 2) + padding;
            const y = height - padding - ((ping - minPing) / range) * (height - padding * 2);
            return `${x},${y}`;
        });

        const pathD = `M ${points.join(' L ')}`;
        const qualityClass = getLatencyClass(
            history[history.length - 1]?.quality_score || 50
        );

        // Create or update path
        let path = svg.querySelector('path');
        if (!path) {
            path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            svg.appendChild(path);
        }

        path.setAttribute('d', pathD);
        path.setAttribute('class', qualityClass);

        // Update SVG class
        svg.className = 'latency-sparkline ' + qualityClass;
    }

    function updateLatencyAge() {
        if (!latencyData.lastUpdate) return;

        const now = new Date();
        const diff = Math.floor((now - latencyData.lastUpdate) / 1000);
        document.getElementById('latency-age').textContent = diff;
    }

    function showLatencyError() {
        document.getElementById('latency-loading').style.display = 'none';
        document.getElementById('latency-error').style.display = 'flex';
        document.getElementById('latency-content').style.display = 'none';
    }

    function hideLatencyError() {
        document.getElementById('latency-error').style.display = 'none';
    }

    function startLatencyPolling() {
        // Fetch immediately
        fetchLatency();

        // Poll every 60 seconds
        latencyData.pollInterval = setInterval(fetchLatency, 60000);

        // Update age counter every second
        setInterval(updateLatencyAge, 1000);

        // Cleanup on pagehide
        window.addEventListener('pagehide', () => {
            if (latencyData.pollInterval) {
                clearInterval(latencyData.pollInterval);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        appendInitDataToLinks();
        appendInitDataToForms();

        document.querySelectorAll('.btn, .nav-item, .fab').forEach(el => {
            el.addEventListener('click', () => hapticFeedback('selection'));
        });

        const progressFills = document.querySelectorAll('.progress-fill');
        progressFills.forEach(fill => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 100);
        });

        // Iniciar widget de latencia si estamos en el dashboard
        if (document.getElementById('latency-widget')) {
            startLatencyPolling();
        }
    });

    window.MiniApp = {
        tg,
        getInitData,
        appendInitDataToLinks,
        appendInitDataToForms,
        formatBytes,
        formatDate,
        apiRequest,
        showAlert,
        showConfirm,
        hapticFeedback,
        // Latency widget functions
        fetchLatency,
        startLatencyPolling,
        renderSparkline
    };

})();
