# 🧪 GestPyLab - Sistema de Gestión de Retiros de Muestras Veterinarias

Sistema web desarrollado en Django para gestionar solicitudes de retiro de muestras veterinarias, optimizando la asignación de retiradores por zonas geográficas.

## 📋 Características Principales

### ✨ Funcionalidades Implementadas

- **Gestión de Solicitantes**: Registro completo de veterinarias, médicos, técnicos, ayudantes y tutores
- **Solicitudes de Retiro**: Creación y seguimiento de solicitudes con asignación automática
- **Búsqueda Dinámica**: Autocompletado en tiempo real para selección de solicitantes
- **Exportación a PDF**: Generación de listas de retiro para impresión
- **Dashboard Interactivo**: Visualización de estadísticas y resumen por retirador
- **Gestión de Zonas**: Asignación inteligente de retiradores por zona geográfica
- **Admin Personalizado**: Panel de administración mejorado con acciones masivas
- **Notificaciones**: Sistema de alertas para datos faltantes

### 🔒 Seguridad

- Variables de entorno para credenciales sensibles
- Validaciones de datos en modelos y formularios
- Logging de operaciones críticas
- Manejo de errores robusto

### ⚡ Optimizaciones

- Queries optimizadas con `select_related` y `prefetch_related`
- Índices en base de datos para búsquedas rápidas
- Caché de consultas frecuentes
- Arquitectura de servicios para lógica de negocio

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.10 o superior
- PostgreSQL 12 o superior
- pip (gestor de paquetes de Python)
- Virtualenv (recomendado)

### Paso 1: Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd GestPyLab
```

### Paso 2: Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Base de Datos PostgreSQL

1. Crear base de datos en PostgreSQL:

```sql
CREATE DATABASE gestpylab_db;
CREATE USER postgres WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE gestpylab_db TO postgres;
```

2. Crear archivo `.env` en la raíz del proyecto:

```env
# Seguridad
SECRET_KEY=tu-secret-key-super-segura-aqui
DEBUG=True

# Base de Datos
DB_NAME=gestpylab_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

**Nota**: Puedes usar `.env.example` como plantilla.

### Paso 5: Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### Paso 6: Crear Superusuario

```bash
python manage.py createsuperuser
```

### Paso 7: Cargar Datos Iniciales (Opcional)

```bash
# Crear zonas iniciales
python manage.py shell
>>> from retiros.models import Zona
>>> Zona.objects.create(nombre="Valparaíso")
>>> Zona.objects.create(nombre="Viña del Mar")
>>> Zona.objects.create(nombre="Quilpué")
>>> Zona.objects.create(nombre="Villa Alemana")
>>> exit()
```

### Paso 8: Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Accede a: `http://localhost:8000`

---

## 📁 Estructura del Proyecto

```
GestPyLab/
├── gestpylab/              # Configuración principal del proyecto
│   ├── settings.py         # Configuración con variables de entorno
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Configuración WSGI
├── retiros/               # App principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas optimizadas
│   ├── forms.py           # Formularios
│   ├── admin.py           # Admin personalizado
│   ├── api.py             # Endpoints API
│   ├── services.py        # Lógica de negocio
│   ├── utils.py           # Utilidades (PDFs, notificaciones)
│   ├── urls.py            # URLs de la app
│   ├── static/            # Archivos estáticos
│   │   └── retiros/
│   │       ├── css/       # Estilos personalizados
│   │       └── js/        # JavaScript
│   └── templates/         # Templates HTML
│       └── retiros/
│           ├── base.html  # Template base
│           └── ...        # Otros templates
├── logs/                  # Logs del sistema
├── .env                   # Variables de entorno (no en git)
├── .env.example          # Plantilla de variables
├── .gitignore            # Archivos ignorados por git
├── requirements.txt      # Dependencias Python
├── TODO.md              # Plan de desarrollo
└── README.md            # Este archivo
```

---

## 🎯 Uso del Sistema

### 1. Acceder al Dashboard

Navega a `http://localhost:8000` para ver el dashboard principal con:
- Total de solicitudes pendientes
- Resumen por retirador
- Acciones rápidas

### 2. Agregar Solicitantes

1. Ir a `/admin/retiros/solicitante/`
2. Click en "Agregar Solicitante"
3. Completar datos (email y dirección son opcionales)
4. Guardar

### 3. Crear Solicitud de Retiro

1. Click en "Agregar Nueva Solicitud"
2. Usar búsqueda dinámica para seleccionar solicitante
3. Completar dirección (se autocompleta si está disponible)
4. Seleccionar fecha de retiro
5. Guardar (el retirador se asigna automáticamente)

### 4. Exportar Lista a PDF

- Desde lista de pendientes: Click en "Exportar PDF"
- Desde lista de retirador: Click en "Exportar PDF"

### 5. Marcar como Completado

- En cualquier lista, click en el botón verde ✓
- Confirmar la acción

### 6. Revisar Datos Faltantes

- En el dashboard, si hay solicitantes con datos incompletos, aparecerá un botón amarillo
- Click para ver el reporte en logs

---

## 🔧 Configuración Avanzada

### Horario de Agendamiento

Por defecto, solo se permiten solicitudes entre 11:00 y 14:00 hrs. Para modificar:

Editar `retiros/utils.py`:

```python
def validar_horario_agendamiento():
    hora_inicio = datetime.strptime('11:00', '%H:%M').time()
    hora_fin = datetime.strptime('14:00', '%H:%M').time()
    # Modificar según necesidad
```

### Personalizar Zonas

Agregar más zonas desde el admin o shell:

```python
python manage.py shell
>>> from retiros.models import Zona
>>> Zona.objects.create(nombre="Nueva Zona")
```

### Logging

Los logs se guardan en `logs/gestpylab.log`. Para modificar nivel de logging:

Editar `gestpylab/settings.py`:

```python
LOGGING = {
    'handlers': {
        'file': {
            'level': 'INFO',  # Cambiar a DEBUG, WARNING, ERROR
            ...
        }
    }
}
```

---

## 🧪 Testing (Pendiente)

```bash
# Ejecutar tests
python manage.py test retiros

# Con cobertura
coverage run --source='.' manage.py test retiros
coverage report
```

---

## 📊 Modelos de Datos

### Zona
- `nombre`: Nombre de la zona geográfica

### Solicitante
- `nombre`: Nombre completo
- `tipo`: Médico, Veterinaria, Técnico, Ayudante, Tutor
- `telefono`: Teléfono de contacto
- `email`: Email (opcional)
- `email_desconocido`: Marca si el email no se conoce
- `direccion_principal`: Dirección fija (opcional)
- `direccion_desconocida`: Marca si la dirección no se conoce
- `horario_atencion_inicio/fin`: Horarios (opcionales)
- `comentarios_horario_retiro`: Notas sobre horarios
- `zona`: Zona geográfica (FK)

### Retirador
- `nombre`: Nombre del retirador
- `tipo`: Fijo o Complementario
- `zonas_preferidas`: Zonas que cubre (M2M)

### SolicitudRetiro
- `solicitante`: Solicitante (FK)
- `direccion_retiro`: Dirección del retiro
- `usar_direccion_solicitante`: Boolean
- `fecha_retiro`: Fecha programada
- `retirador_asignado`: Retirador (FK, opcional)
- `estado`: Pendiente, Asignado, Completado, Cancelado
- `notas`: Observaciones

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abrir Pull Request

---

## 📝 Changelog

### Versión 1.0.0 (Actual)
- ✅ Sistema completo de gestión de retiros
- ✅ Búsqueda dinámica con autocompletado
- ✅ Exportación a PDF
- ✅ Admin personalizado
- ✅ Optimizaciones de rendimiento
- ✅ Seguridad con variables de entorno
- ✅ Arquitectura de servicios

### Próximas Versiones
- 🔄 Tests unitarios completos
- 🔄 Integración con WhatsApp (opcional)
- 🔄 Notificaciones automáticas con Celery
- 🔄 Dashboard con gráficos

---

## 📄 Licencia

Este proyecto es privado y de uso interno.

---

## 👥 Autor

Desarrollado para gestión de retiros de muestras veterinarias.

---

## 🆘 Soporte

Para reportar bugs o solicitar features, crear un issue en el repositorio.

---

## 📚 Documentación Adicional

- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ReportLab Documentation](https://www.reportlab.com/docs/)

---

**¡Gracias por usar GestPyLab! 🧪**
