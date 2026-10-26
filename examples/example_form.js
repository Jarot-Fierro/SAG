document.addEventListener('DOMContentLoaded', function () {
    const telefonoInput = document.getElementById('id_numero_telefonico');
    if (!telefonoInput) return;

    // Formatear Teléfono: +569XXXXXXXX
    function formatTelefono(value) {
        let nums = value.replace(/\D/g, '');
        if (nums.startsWith('569')) {
            nums = nums.slice(3);
        } else if (nums.startsWith('9')) {
            nums = nums.slice(1);
        }

        // Solo tomar los últimos 8 dígitos si hay más
        if (nums.length > 8) {
            nums = nums.slice(-8);
        }

        return nums ? '+569' + nums : '';
    }

    telefonoInput.value = formatTelefono(telefonoInput.value);

    telefonoInput.addEventListener('input', function () {
        this.value = formatTelefono(this.value);
    });

    telefonoInput.addEventListener('blur', function () {
        this.value = formatTelefono(this.value);
    });

});
document.querySelectorAll('.tom-select').forEach((el) => {
    new TomSelect(el, {
        render: {
            no_results: function () {
                return '<div class="no-results">No se encontraron resultados</div>';
            }
        }
    });
});
