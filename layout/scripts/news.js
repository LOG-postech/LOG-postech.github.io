// Show the first page.initial items (data/news/config.toml); "Show more" adds page.step.
(function () {
    var items = document.querySelectorAll('#news-list .news-item');
    var more = document.getElementById('news-more');
    var visibleCount = Math.min(LOG.config.news.page.initial, items.length);

    function updateVisibility() {
        Array.prototype.forEach.call(items, function (item, index) {
            item.hidden = index >= visibleCount;
        });
        more.hidden = visibleCount >= items.length;
    }

    more.addEventListener('click', function () {
        var firstNewItem = items[visibleCount];
        visibleCount = Math.min(visibleCount + LOG.config.news.page.step, items.length);
        updateVisibility();
        // Continue reading at the newly revealed news, even on the final batch.
        if (firstNewItem) {
            firstNewItem.setAttribute('tabindex', '-1');
            firstNewItem.focus({ preventScroll: true });
        }
    });

    updateVisibility();
})();
