/**
 * OpenLockey メインJavaScriptファイル
 */

document.addEventListener('DOMContentLoaded', function() {
    // アラートの自動消去
    setupAlertDismissal();
    
    // ツールチップの初期化
    initializeTooltips();
    
    // テーブルの行クリックイベント
    setupTableRowClickEvents();
    
    // フォームバリデーション
    setupFormValidation();
    
    // セッションタイムアウト監視
    setupSessionTimeout();
});

/**
 * アラートの自動消去
 */
function setupAlertDismissal() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        // 5秒後に自動的に消える
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * ツールチップの初期化
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * テーブルの行クリックイベント
 */
function setupTableRowClickEvents() {
    const clickableTables = document.querySelectorAll('table.table-hover');
    clickableTables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            if (row.dataset.href) {
                row.style.cursor = 'pointer';
                row.addEventListener('click', function(e) {
                    // ボタンやリンクがクリックされた場合は、行のクリックイベントを発火させない
                    if (e.target.closest('button, a, .no-row-click')) {
                        return;
                    }
                    
                    window.location.href = this.dataset.href;
                });
            }
        });
    });
}

/**
 * フォームバリデーション
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * セッションタイムアウト監視
 */
function setupSessionTimeout() {
    // セッションタイムアウトの設定（72時間 = 259200000ミリ秒）
    const sessionTimeout = 259200000;
    
    // ローカルストレージからセッション開始時間を取得
    let sessionStartTime = localStorage.getItem('sessionStartTime');
    
    // セッション開始時間がない場合は現在時刻を設定
    if (!sessionStartTime) {
        sessionStartTime = new Date().getTime();
        localStorage.setItem('sessionStartTime', sessionStartTime);
    }
    
    // 定期的にセッションの有効期限をチェック
    setInterval(() => {
        const currentTime = new Date().getTime();
        const elapsedTime = currentTime - sessionStartTime;
        
        // セッションタイムアウトに近づいたら警告を表示
        if (elapsedTime > (sessionTimeout - 3600000)) { // 1時間前に警告
            const remainingTime = Math.floor((sessionTimeout - elapsedTime) / 60000);
            
            // 警告がまだ表示されていない場合のみ表示
            if (!document.getElementById('session-timeout-warning')) {
                const alertsDiv = document.getElementById('alerts');
                if (alertsDiv) {
                    alertsDiv.innerHTML += `
                        <div id="session-timeout-warning" class="alert alert-warning alert-dismissible fade show alert-permanent" role="alert">
                            <strong>セッション有効期限の警告:</strong> あと約${remainingTime}分でセッションが終了します。作業内容を保存し、再ログインしてください。
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="閉じる"></button>
                        </div>
                    `;
                }
            }
        }
        
        // セッションタイムアウトを超えた場合はログアウト
        if (elapsedTime > sessionTimeout) {
            localStorage.removeItem('sessionStartTime');
            window.location.href = '/logout?reason=timeout';
        }
    }, 300000); // 5分ごとにチェック
    
    // ユーザーのアクティビティを検出してセッション開始時間をリセット
    const resetSessionTimer = () => {
        sessionStartTime = new Date().getTime();
        localStorage.setItem('sessionStartTime', sessionStartTime);
    };
    
    // クリック、キー入力、スクロールでセッションタイマーをリセット
    document.addEventListener('click', resetSessionTimer);
    document.addEventListener('keypress', resetSessionTimer);
    document.addEventListener('scroll', resetSessionTimer);
}

/**
 * ユーティリティ関数
 */

/**
 * 日付をフォーマットする
 * @param {Date|string} date - フォーマットする日付
 * @param {string} format - 日付フォーマット（例: 'YYYY/MM/DD HH:mm'）
 * @returns {string} フォーマットされた日付文字列
 */
function formatDate(date, format = 'YYYY/MM/DD HH:mm') {
    const d = new Date(date);
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * 文字列を安全にエスケープする
 * @param {string} str - エスケープする文字列
 * @returns {string} エスケープされた文字列
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * APIリクエストを送信する
 * @param {string} url - リクエスト先URL
 * @param {Object} options - fetchオプション
 * @returns {Promise<Object>} レスポンスデータ
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'APIリクエストエラー');
        }
        
        return data;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

/**
 * フォームデータをJSONオブジェクトに変換する
 * @param {HTMLFormElement} form - フォーム要素
 * @returns {Object} フォームデータのJSONオブジェクト
 */
function formToJson(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

/**
 * 通知を表示する
 * @param {string} message - 通知メッセージ
 * @param {string} type - 通知タイプ（success, danger, warning, info）
 */
function showNotification(message, type = 'info') {
    const alertsDiv = document.getElementById('alerts');
    if (alertsDiv) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = 'alert';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="閉じる"></button>
        `;
        
        alertsDiv.appendChild(alert);
        
        // 5秒後に自動的に消える
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    }
}

