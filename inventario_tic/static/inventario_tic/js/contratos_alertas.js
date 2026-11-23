document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('contratosVencimientoModal');
    if (!modal) return;
    // Esperar si la página ya abrió otro modal, por ejemplo para corregir un formulario.
    function mostrar() {
        if (!document.querySelector('.modal.show')) bootstrap.Modal.getOrCreateInstance(modal).show();
    }
    setTimeout(mostrar, 0);
});
