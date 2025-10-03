/**
 * Búsqueda dinámica de solicitantes con autocompletado
 * GestPyLab - Sistema de Retiros
 */

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('busqueda-solicitante');
    const selectSolicitante = document.getElementById('id_solicitante');
    const resultsContainer = document.getElementById('resultados-busqueda');
    const infoContainer = document.getElementById('info-solicitante');
    
    if (!searchInput || !selectSolicitante) {
        console.log('Elementos de búsqueda no encontrados');
        return;
    }
    
    let timeoutId = null;
    let selectedSolicitante = null;
    
    // Evento de búsqueda con debounce
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        // Limpiar timeout anterior
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
        
        // Si la búsqueda está vacía, limpiar resultados
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
            infoContainer.innerHTML = '';
            return;
        }
        
        // Mostrar indicador de carga
        resultsContainer.innerHTML = '<div class="list-group-item"><i class="fas fa-spinner fa-spin"></i> Buscando...</div>';
        resultsContainer.style.display = 'block';
        
        // Realizar búsqueda después de 300ms
        timeoutId = setTimeout(() => {
            buscarSolicitantes(query);
        }, 300);
    });
    
    // Función para realizar la búsqueda
    function buscarSolicitantes(query) {
        fetch(`/api/buscar-solicitantes/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                mostrarResultados(data);
            })
            .catch(error => {
                console.error('Error en búsqueda:', error);
                resultsContainer.innerHTML = '<div class="list-group-item text-danger">Error al buscar. Intente nuevamente.</div>';
            });
    }
    
    // Función para mostrar resultados
    function mostrarResultados(data) {
        if (data.error) {
            resultsContainer.innerHTML = `<div class="list-group-item text-danger">${data.error}</div>`;
            return;
        }
        
        if (data.results.length === 0) {
            resultsContainer.innerHTML = '<div class="list-group-item text-muted">No se encontraron resultados</div>';
            return;
        }
        
        let html = '';
        data.results.forEach(solicitante => {
            const estadoClass = solicitante.tiene_datos_completos ? 'success' : 'warning';
            const estadoIcon = solicitante.tiene_datos_completos ? '✓' : '⚠';
            
            html += `
                <a href="#" class="list-group-item list-group-item-action resultado-item" data-id="${solicitante.id}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${solicitante.nombre}</h6>
                        <small class="badge bg-${estadoClass}">${estadoIcon} ${solicitante.estado}</small>
                    </div>
                    <p class="mb-1">
                        <small>
                            <strong>${solicitante.tipo}</strong> | 
                            <i class="fas fa-map-marker-alt"></i> ${solicitante.zona} | 
                            <i class="fas fa-phone"></i> ${solicitante.telefono}
                        </small>
                    </p>
                    <small class="text-muted">
                        <i class="fas fa-envelope"></i> ${solicitante.email} | 
                        <i class="fas fa-home"></i> ${solicitante.direccion.substring(0, 40)}${solicitante.direccion.length > 40 ? '...' : ''}
                    </small>
                </a>
            `;
        });
        
        resultsContainer.innerHTML = html;
        
        // Agregar eventos de click a los resultados
        document.querySelectorAll('.resultado-item').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const solicitanteId = this.dataset.id;
                seleccionarSolicitante(solicitanteId);
            });
        });
    }
    
    // Función para seleccionar un solicitante
    function seleccionarSolicitante(solicitanteId) {
        fetch(`/api/solicitante/${solicitanteId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error al cargar solicitante: ' + data.error);
                    return;
                }
                
                // Actualizar el select
                selectSolicitante.value = solicitanteId;
                
                // Actualizar el input de búsqueda
                searchInput.value = data.nombre;
                
                // Ocultar resultados
                resultsContainer.style.display = 'none';
                
                // Mostrar información del solicitante
                mostrarInfoSolicitante(data);
                
                // Autocompletar dirección si está disponible
                autocompletarDireccion(data);
                
                selectedSolicitante = data;
            })
            .catch(error => {
                console.error('Error al obtener solicitante:', error);
                alert('Error al cargar los datos del solicitante');
            });
    }
    
    // Función para mostrar información del solicitante
    function mostrarInfoSolicitante(data) {
        const estadoClass = data.tiene_datos_completos ? 'success' : 'warning';
        const estadoText = data.tiene_datos_completos ? 'Datos completos' : 'Datos incompletos';
        
        let warnings = [];
        if (data.email_desconocido) warnings.push('Email desconocido');
        if (data.direccion_desconocida) warnings.push('Dirección desconocida');
        
        const warningsHtml = warnings.length > 0 
            ? `<div class="alert alert-warning mt-2 mb-0"><small><i class="fas fa-exclamation-triangle"></i> ${warnings.join(', ')}</small></div>`
            : '';
        
        infoContainer.innerHTML = `
            <div class="card mt-3">
                <div class="card-body">
                    <h6 class="card-title">
                        ${data.nombre} 
                        <span class="badge bg-${estadoClass}">${estadoText}</span>
                    </h6>
                    <p class="card-text mb-1">
                        <small>
                            <strong>Tipo:</strong> ${data.tipo} | 
                            <strong>Zona:</strong> ${data.zona.nombre}<br>
                            <strong>Teléfono:</strong> ${data.telefono}<br>
                            <strong>Email:</strong> ${data.email || '(Desconocido)'}<br>
                            <strong>Dirección:</strong> ${data.direccion_principal || '(Desconocida)'}<br>
                            <strong>Horario:</strong> ${data.horario_completo}
                        </small>
                    </p>
                    ${warningsHtml}
                </div>
            </div>
        `;
    }
    
    // Función para autocompletar dirección
    function autocompletarDireccion(data) {
        const usarDireccionCheckbox = document.getElementById('id_usar_direccion_solicitante');
        const direccionTextarea = document.getElementById('id_direccion_retiro');
        
        if (usarDireccionCheckbox && direccionTextarea) {
            if (data.direccion_principal && !data.direccion_desconocida) {
                usarDireccionCheckbox.checked = true;
                direccionTextarea.value = data.direccion_principal;
                direccionTextarea.disabled = true;
            } else {
                usarDireccionCheckbox.checked = false;
                direccionTextarea.value = '';
                direccionTextarea.disabled = false;
            }
        }
    }
    
    // Cerrar resultados al hacer click fuera
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.style.display = 'none';
        }
    });
    
    // Manejar checkbox de usar dirección del solicitante
    const usarDireccionCheckbox = document.getElementById('id_usar_direccion_solicitante');
    const direccionTextarea = document.getElementById('id_direccion_retiro');
    
    if (usarDireccionCheckbox && direccionTextarea) {
        usarDireccionCheckbox.addEventListener('change', function() {
            if (this.checked && selectedSolicitante) {
                if (selectedSolicitante.direccion_principal) {
                    direccionTextarea.value = selectedSolicitante.direccion_principal;
                    direccionTextarea.disabled = true;
                } else {
                    alert('El solicitante no tiene dirección registrada');
                    this.checked = false;
                }
            } else {
                direccionTextarea.disabled = false;
                if (!this.checked) {
                    direccionTextarea.value = '';
                }
            }
        });
    }
});
