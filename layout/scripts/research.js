    document.querySelectorAll('.fold-trigger').forEach(function(button) {
        button.addEventListener('click', function() {
            var detail = document.getElementById(button.getAttribute('aria-controls'));
            var isOpen = button.getAttribute('aria-expanded') === 'true';
            button.setAttribute('aria-expanded', String(!isOpen));
            if (detail) {
                detail.classList.toggle('open', !isOpen);
            }
        });
    });

    function applyConditionalResearchWrap() {
        var sections = Array.prototype.filter.call(document.querySelectorAll('.section'), function(section) {
            return section.querySelector('img') && section.querySelector('.section-text p');
        });
        if (!sections.length) {
            return;
        }

        sections.forEach(function(section) {
            section.classList.remove('wrap-flow');
        });

        // One square size for every icon, 90% as tall as the shortest paragraph.
        // Resizing the icons reflows the text, so repeat a few times to converge;
        // capped so narrow screens fall back to the wrap-flow layout below.
        var maxSize = Math.min(200, sections[0].getBoundingClientRect().width * 0.4);
        for (var i = 0; i < 4; i++) {
            var shortest = Infinity;
            sections.forEach(function(section) {
                shortest = Math.min(shortest, section.querySelector('.section-text p').getBoundingClientRect().height);
            });
            var size = Math.min(Math.max(shortest * 0.9, 80), maxSize);
            sections.forEach(function(section) {
                var image = section.querySelector('img');
                image.style.width = size + 'px';
                image.style.height = size + 'px';
            });
        }

        sections.forEach(function(section) {
            var image = section.querySelector('img');
            var textBlock = section.querySelector('.section-text p');

            var textStyle = window.getComputedStyle(textBlock);
            var lineHeight = parseFloat(textStyle.lineHeight);
            if (!lineHeight || Number.isNaN(lineHeight)) {
                lineHeight = parseFloat(textStyle.fontSize) * 1.75;
            }

            var textHeight = textBlock.getBoundingClientRect().height;
            var imageHeight = image.getBoundingClientRect().height;
            var threshold = imageHeight + (2 * lineHeight);

            if (textHeight > threshold) {
                section.classList.add('wrap-flow');
            }
        });
    }

    var wrapResizeTimer;
    function onWrapResize() {
        window.clearTimeout(wrapResizeTimer);
        wrapResizeTimer = window.setTimeout(applyConditionalResearchWrap, 80);
    }

    window.addEventListener('load', applyConditionalResearchWrap);
    window.addEventListener('resize', onWrapResize);
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(applyConditionalResearchWrap);
    }
