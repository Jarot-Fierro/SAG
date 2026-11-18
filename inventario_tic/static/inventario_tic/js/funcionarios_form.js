document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form.needs-validation');
    if (!form) return;
    form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            form.classList.add('was-validated');
        }
    });
});
