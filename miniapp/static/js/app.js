/**
 * uSipipo Mini App - Main JavaScript
 *
 * Integración con Telegram WebApp SDK y lógica de la aplicación.
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

        document.addEventListener('backButtonClicked', function() {
            if (window.location.pathname !== '/api/v1/miniapp/dashboard') {
                window.history.back();
            } else {
                tg.close();
            }
        });

        tg.BackButton.show();
        tg.BackButton.onClick(function() {
            if (window.location.pathname !== '/api/v1/miniapp/dashboard') {
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

        document.querySelectorAll('a[href^="/api/v1/miniapp/"]').forEach(link => {
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
        hapticFeedback
    };

})();
