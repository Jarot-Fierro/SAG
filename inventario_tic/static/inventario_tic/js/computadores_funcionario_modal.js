document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('funcionarioModalForm');
    const select = document.getElementById('responsable_computador');
    const modal = document.getElementById('funcionarioModal');
    if (!form || !select || !modal) return;
    const errors = document.getElementById('funcionarioModalErrors');
    const submit = form.querySelector('[type="submit"]');
    let saving = false;
    modal.addEventListener('shown.bs.modal', () => form.elements.nombre.focus());
    modal.addEventListener('hidden.bs.modal', () => {
        form.reset();
        errors.textContent = '';
        errors.classList.add('d-none');
    });
    modal.addEventListener('hide.bs.modal', event => { if (saving) event.preventDefault(); });
    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (saving) return;
        saving = true;
        submit.disabled = true;
        errors.classList.add('d-none');
        try {
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
                headers: {'X-CSRFToken': form.elements.csrfmiddlewaretoken.value, 'Accept': 'application/json'}
            });
            if (!(response.headers.get('content-type') || '').includes('application/json')) {
                throw new Error('La sesión expiró o el servidor no está disponible. Recargue la página.');
            }
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(Object.values(data.errors || {}).flat().join(' ') || 'No se pudo crear el funcionario.');
            }
            if (select.tomselect) {
                select.tomselect.addOption({value: String(data.id), text: data.nombre});
                select.tomselect.setValue(String(data.id));
            } else {
                select.add(new Option(data.nombre, String(data.id), true, true));
                select.dispatchEvent(new Event('change', {bubbles: true}));
            }
            saving = false;
            bootstrap.Modal.getOrCreateInstance(modal).hide();
            if (data.coincidencias && typeof Swal !== 'undefined') {
                Swal.fire({icon: 'info', title: 'Funcionario creado', text: 'Hay otros funcionarios con el mismo nombre. Verifique la selección antes de guardar la recepción.'});
            }
        } catch (error) {
            errors.textContent = error.message || 'No se pudo crear el funcionario.';
            errors.classList.remove('d-none');
        } finally {
            saving = false;
            submit.disabled = false;
        }
    });
});
