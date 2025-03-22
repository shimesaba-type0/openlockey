/**
 * OpenLockey ダークモード切り替えスクリプト
 */

document.addEventListener('DOMContentLoaded', function() {
    // ダークモードトグルボタンの取得
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    if (darkModeToggle) {
        // ローカルストレージからダークモード設定を取得
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        
        // 初期状態の設定
        if (isDarkMode) {
            document.body.setAttribute('data-bs-theme', 'dark');
            updateDarkModeIcon(true);
        } else {
            document.body.setAttribute('data-bs-theme', 'light');
            updateDarkModeIcon(false);
        }
        
        // ダークモードトグルボタンのクリックイベント
        darkModeToggle.addEventListener('click', function() {
            toggleDarkMode();
        });
    }
    
    // システムのダークモード設定の変更を検知
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    prefersDarkScheme.addEventListener('change', function(e) {
        // ユーザーが明示的に設定していない場合のみ、システム設定に従う
        if (localStorage.getItem('darkMode') === null) {
            const isDark = e.matches;
            document.body.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
            updateDarkModeIcon(isDark);
        }
    });
});

/**
 * ダークモードを切り替える
 */
function toggleDarkMode() {
    const isDarkMode = document.body.getAttribute('data-bs-theme') === 'dark';
    
    if (isDarkMode) {
        // ライトモードに切り替え
        document.body.setAttribute('data-bs-theme', 'light');
        localStorage.setItem('darkMode', 'false');
        updateDarkModeIcon(false);
    } else {
        // ダークモードに切り替え
        document.body.setAttribute('data-bs-theme', 'dark');
        localStorage.setItem('darkMode', 'true');
        updateDarkModeIcon(true);
    }
}

/**
 * ダークモードアイコンを更新する
 * @param {boolean} isDark - ダークモードかどうか
 */
function updateDarkModeIcon(isDark) {
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    if (darkModeToggle) {
        // アイコンの更新
        if (!darkModeToggle.querySelector('.bi-sun')) {
            // アイコン要素がまだ存在しない場合は作成
            darkModeToggle.innerHTML = isDark 
                ? '<i class="bi bi-sun"></i>'
                : '<i class="bi bi-moon"></i>';
        }
        
        // ボタンのテキストを更新（テキストがある場合）
        const buttonText = darkModeToggle.textContent.trim();
        if (buttonText) {
            darkModeToggle.innerHTML = isDark 
                ? '<i class="bi bi-sun"></i> ライトモード切替'
                : '<i class="bi bi-moon"></i> ダークモード切替';
        }
    }
}

/**
 * 初期ダークモード設定
 * システム設定に基づいて初期状態を設定する
 */
function initializeDarkMode() {
    // ローカルストレージに設定がない場合のみ、システム設定に従う
    if (localStorage.getItem('darkMode') === null) {
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        const isDark = prefersDarkScheme.matches;
        
        document.body.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
        updateDarkModeIcon(isDark);
    }
}

// ページロード時に初期設定を適用
initializeDarkMode();

