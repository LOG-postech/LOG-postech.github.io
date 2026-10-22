    var toggle = document.querySelector('.menu-toggle');
    var drawer = document.getElementById('navDrawer');
    var overlay = document.getElementById('navOverlay');
    var close = document.getElementById('drawerClose');

    function openDrawer() {
        drawer.classList.add('open');
        overlay.classList.add('open');
    }
    function closeDrawer() {
        drawer.classList.remove('open');
        overlay.classList.remove('open');
    }

    toggle.addEventListener('click', function() { drawer.classList.contains('open') ? closeDrawer() : openDrawer(); });
    close.addEventListener('click', closeDrawer);
    overlay.addEventListener('click', closeDrawer);
