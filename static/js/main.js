// main.js — students will add JavaScript here as features are built

(function () {
    var btn = document.getElementById('open-video-modal');
    var modal = document.getElementById('video-modal');
    if (!btn || !modal) return;

    var iframe = document.getElementById('video-modal-iframe');
    var videoUrl = modal.getAttribute('data-video-url');
    var overlay = modal.querySelector('.video-modal-overlay');
    var closeBtn = modal.querySelector('.video-modal-close');

    function open() {
        iframe.src = videoUrl + '?autoplay=1';
        modal.hidden = false;
    }

    function close() {
        modal.hidden = true;
        iframe.src = 'about:blank';
    }

    btn.addEventListener('click', open);
    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', close);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !modal.hidden) close();
    });
})();
