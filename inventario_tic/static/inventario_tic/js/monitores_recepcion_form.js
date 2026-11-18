document.addEventListener('DOMContentLoaded', function () {
    if (typeof TomSelect === 'undefined') return;
    document.querySelectorAll('.tom-select').forEach(function (element) {
        if (!element.tomselect) new TomSelect(element);
    });
});
