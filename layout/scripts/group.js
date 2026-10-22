// Faces on the news and publication pages link here as #<photo file name>
// (the anchor static/js/site.js links faces to), so new members need no id.
(function () {
    Array.prototype.forEach.call(document.querySelectorAll('.member-item img'), function (img) {
        img.closest('.member-item').id = img.getAttribute('src').split('/').pop().replace(/\.[^.]*$/, '');
    });
    var target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (target && target.classList.contains('member-item')) {
        target.scrollIntoView({ block: 'center' });
        target.classList.add('member-highlight');
    }
})();



/* Page through the gallery preview, pageSize photos at a time. */
(function () {
    var box = document.querySelector('.gallery-preview');
    var prevButton = document.querySelector('[data-gallery-dir="prev"]');
    var nextButton = document.querySelector('[data-gallery-dir="next"]');
    var pageSize = LOG.config.gallery.preview.count;
    var currentPage = 0;
    var items = [];

    if (!box || !prevButton || !nextButton) return;

    function updateButtons() {
        var lastPage = Math.max(Math.ceil(items.length / pageSize) - 1, 0);
        prevButton.disabled = currentPage === 0;
        nextButton.disabled = currentPage >= lastPage;
    }

    function renderPage() {
        var start = currentPage * pageSize;
        var end = start + pageSize;
        var frag = document.createDocumentFragment();

        items.slice(start, end).forEach(function (item) {
            var cell = document.createElement('div');
            cell.className = 'gallery-preview-item';
            cell.appendChild(item.cloneNode(true));
            frag.appendChild(cell);
        });

        if (frag.childNodes.length) {
            box.textContent = '';
            box.appendChild(frag);
        }

        updateButtons();
    }

    prevButton.addEventListener('click', function () {
        if (currentPage === 0) return;
        currentPage -= 1;
        renderPage();
    });

    nextButton.addEventListener('click', function () {
        var lastPage = Math.max(Math.ceil(items.length / pageSize) - 1, 0);
        if (currentPage >= lastPage) return;
        currentPage += 1;
        renderPage();
    });

    // Every gallery photo, in gallery order (static/js/site.js reads them from data/).
    items = LOG.gallery.photos.map(function (p) {
        var link = document.createElement('a');
        link.setAttribute('href', 'photo.html?image=' + p.full);

        var pic = document.createElement('img');
        pic.setAttribute('src', p.thumb);
        pic.setAttribute('alt', p.alt);
        pic.setAttribute('loading', 'lazy');
        link.appendChild(pic);

        var span = document.createElement('span');
        span.className = 'tooltip';
        span.textContent = p.caption;
        link.appendChild(span);
        return link;
    });

    if (items.length) {
        currentPage = 0;
        renderPage();
    }
})();
