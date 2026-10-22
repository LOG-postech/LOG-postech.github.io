(function () {
    var stage = document.getElementById("photoStage");
    var errorBox = document.getElementById("photoError");
    var image = document.getElementById("photoImage");
    var imageLink = document.getElementById("photoImageLink");
    var caption = document.getElementById("photoCaption");
    var status = document.getElementById("photoStatus");
    var prevLink = document.getElementById("photoPrev");
    var nextLink = document.getElementById("photoNext");
    var requested = new URLSearchParams(window.location.search).get("image");
    var currentPath = normalizeImagePath(requested);

    function normalizeImagePath(value) {
        if (!value) return "";
        var clean = value.split("#")[0];
        try {
            clean = new URL(clean, window.location.href).pathname;
        } catch (e) {}
        clean = clean.replace(/^\/+/, "");
        // Gallery photos live in data/gallery/photos/ (they used to be stories/).
        var idx = clean.indexOf("data/gallery/photos/");
        if (idx >= 0) return clean.slice(idx);
        idx = clean.indexOf("stories/");
        return idx >= 0 ? "data/gallery/photos/" + clean.slice(idx + "stories/".length) : clean;
    }

    function buildViewerHref(path) {
        return "photo.html?image=" + encodeURIComponent(normalizeImagePath(path));
    }

    function setNav(link, item, label) {
        if (!item) {
            link.removeAttribute("href");
            link.classList.add("is-disabled");
            link.setAttribute("aria-disabled", "true");
            link.setAttribute("aria-label", label);
            return;
        }

        link.setAttribute("href", buildViewerHref(item.imagePath));
        link.classList.remove("is-disabled");
        link.removeAttribute("aria-disabled");
        link.setAttribute("aria-label", label + ": " + (item.caption || item.alt || item.imagePath));
    }

    function setFallbackImage(path) {
        image.setAttribute("src", path);
        image.setAttribute("alt", path.split("/").pop());
        imageLink.setAttribute("href", path);
        caption.textContent = path.split("/").pop();
        status.textContent = "";
    }

    function showMissingState() {
        stage.hidden = true;
        errorBox.hidden = false;
    }

    function render(items, currentIndex) {
        var current = items[currentIndex];
        var prev = currentIndex > 0 ? items[currentIndex - 1] : null;
        var next = currentIndex < items.length - 1 ? items[currentIndex + 1] : null;
        var label = current.caption || current.alt || current.imagePath.split("/").pop();

        image.setAttribute("src", current.imagePath);
        image.setAttribute("alt", current.alt || label);
        imageLink.setAttribute("href", current.imagePath);
        caption.textContent = label;
        status.textContent = (currentIndex + 1) + " / " + items.length;
        document.title = label + " | Lee Optimization Group";

        setNav(prevLink, prev, "Previous photo");
        setNav(nextLink, next, "Next photo");
    }

    if (!currentPath) {
        showMissingState();
        return;
    }

    setFallbackImage(currentPath);

    // Every gallery photo, in gallery order (static/js/site.js reads them from data/).
    var items = LOG.gallery.photos.map(function (p) {
        return { imagePath: p.full, alt: p.alt, caption: p.caption };
    });
    var currentIndex = items.findIndex(function (item) {
        return item.imagePath === currentPath;
    });
    if (currentIndex === -1) {
        setNav(prevLink, null, "Previous photo");
        setNav(nextLink, null, "Next photo");
    } else {
        render(items, currentIndex);
    }

    window.addEventListener("keydown", function (event) {
        if (event.key === "ArrowLeft" && prevLink.getAttribute("href")) {
            window.location.href = prevLink.getAttribute("href");
        }

        if (event.key === "ArrowRight" && nextLink.getAttribute("href")) {
            window.location.href = nextLink.getAttribute("href");
        }
    });
})();
