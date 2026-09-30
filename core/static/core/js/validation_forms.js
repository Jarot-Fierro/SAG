/**
 * Script de validación para AdminLTE 4
 * Basado en la validación nativa de Bootstrap 5
 * Soporta: .needs-validation y .needs-validation-tooltip
 */

(() => {
    'use strict';

    // ============================================
    // 1. CONFIGURACIÓN
    // ============================================
    const CONFIG = {
        // Selectores de formularios que serán validados
        selectors: '.needs-validation, .needs-validation-tooltip',

        // Clase que se añade después de la validación
        validatedClass: 'was-validated',

        // Opciones para validación en tiempo real
        realTime: true, // true = valida mientras escribes
        realTimeEvents: ['input', 'change', 'blur'], // eventos para validación en tiempo real
    };

    // ============================================
    // 2. FUNCIÓN PRINCIPAL DE VALIDACIÓN
    // ============================================
    function setupValidation() {
        const forms = document.querySelectorAll(CONFIG.selectors);

        if (forms.length === 0) {
            console.warn('No se encontraron formularios con validación.');
            return;
        }

        forms.forEach(form => {
            // --- A. Validación al enviar (comportamiento estándar de Bootstrap) ---
            form.addEventListener('submit', function (event) {
                if (!this.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                this.classList.add(CONFIG.validatedClass);
            }, false);

            // --- B. Validación en tiempo real (opcional) ---
            if (CONFIG.realTime) {
                const inputs = form.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    CONFIG.realTimeEvents.forEach(eventType => {
                        input.addEventListener(eventType, function () {
                            // Solo validar si el formulario ya fue validado antes
                            if (form.classList.contains(CONFIG.validatedClass)) {
                                // Forzar re-validación
                                if (this.checkValidity()) {
                                    this.classList.remove('is-invalid');
                                    this.classList.add('is-valid');
                                } else {
                                    this.classList.remove('is-valid');
                                    this.classList.add('is-invalid');
                                }
                            }
                        });
                    });
                });
            }

            // --- C. Resetear validación al hacer clic en "Reset" ---
            const resetButton = form.querySelector('button[type="reset"]');
            if (resetButton) {
                resetButton.addEventListener('click', function () {
                    form.classList.remove(CONFIG.validatedClass);
                    // Limpiar estados de validación
                    form.querySelectorAll('.is-valid, .is-invalid').forEach(el => {
                        el.classList.remove('is-valid', 'is-invalid');
                    });
                });
            }
        });
    }

    // ============================================
    // 3. EJECUTAR CUANDO EL DOM ESTÉ LISTO
    // ============================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupValidation);
    } else {
        setupValidation();
    }

    // ============================================
    // 4. FUNCIONES UTILITARIAS ADICIONALES
    // ============================================

    /**
     * Validar un campo específico manualmente
     * @param {HTMLElement} campo - El elemento input/select/textarea
     * @param {HTMLElement} form - El formulario padre (opcional)
     */
    window.validarCampo = function (campo, form) {
        const parentForm = form || campo.closest('form');
        if (!parentForm) return;

        if (campo.checkValidity()) {
            campo.classList.remove('is-invalid');
            campo.classList.add('is-valid');
        } else {
            campo.classList.remove('is-valid');
            campo.classList.add('is-invalid');
        }
    };

    /**
     * Resetear todos los campos de un formulario
     * @param {HTMLElement} form - El formulario a resetear
     */
    window.resetearValidacion = function (form) {
        form.classList.remove('was-validated');
        form.querySelectorAll('.is-valid, .is-invalid').forEach(el => {
            el.classList.remove('is-valid', 'is-invalid');
        });
    };

})();