// 搜索框防抖
const searchInput = document.querySelector('.search-form input');
let searchTimeout;

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            e.target.form.submit();
        }, 500);
    });
} 