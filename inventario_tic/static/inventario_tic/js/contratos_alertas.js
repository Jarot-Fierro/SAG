document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('contratosVencimientoModal');
    if (!modal || modal.dataset.autoabrir !== 'true') return;
    // Esperar si la página ya abrió otro modal, por ejemplo para corregir un formulario.
    function mostrar() {
        const abierto = document.querySelector('.modal.show');
        if (abierto) {
            abierto.addEventListener('hidden.bs.modal', mostrar, {once: true});
            return;
        }
        bootstrap.Modal.getOrCreateInstance(modal).show();
    }
    setTimeout(mostrar, 0);
});
