# Gesico Technical Test - Expedientes API

API REST para la gestión de expedientes de recuperación de deuda: CRUD sobre
expedientes, conversión de divisas del importe adeudado y generación de un PDF
resumen por expediente.

> Los datos de este proyecto son ficticios y de demostración. No contiene
> información personal ni expedientes reales.

## Tecnologías

- Django + Django REST Framework
- PostgreSQL
- Docker / Docker Compose
- WeasyPrint (generación de PDF)
- [Frankfurter](https://frankfurter.dev) (tipos de cambio, API pública sin clave)

## Puesta en marcha

```bash
cp .env.example .env
# edita .env y sustituye DJANGO_SECRET_KEY por un valor real
docker compose up --build
```

Con eso basta: el contenedor `web` espera a que PostgreSQL esté realmente
disponible (healthcheck), aplica las migraciones automáticamente y levanta el
servidor en `http://localhost:8000`.

## Variables de entorno

Ver `.env.example`. Ninguna credencial se incluye en el repositorio; `.env`
está excluido en `.gitignore`.

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django. Genera una propia, no uses la de ejemplo. |
| `DJANGO_DEBUG` | `True` en desarrollo, `False` en producción. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por comas. |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credenciales de la base de datos. |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Host y puerto de PostgreSQL (`db` / `5432` dentro de Docker Compose). |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/expedientes/` | Lista de expedientes |
| POST | `/api/expedientes/` | Crear expediente |
| GET | `/api/expedientes/{id}/` | Detalle de un expediente |
| PUT/PATCH | `/api/expedientes/{id}/` | Actualizar un expediente |
| DELETE | `/api/expedientes/{id}/` | Eliminar un expediente |
| GET | `/api/expedientes/{id}/convertir/?currency=USD` | Convierte el importe adeudado a otra divisa |
| GET | `/api/expedientes/{id}/pdf/` | Descarga la ficha del expediente en PDF |

### Ejemplos

```bash
curl -X POST http://localhost:8000/api/expedientes/ \
  -H "Content-Type: application/json" \
  -d '{"debtor_name": "Juan Perez Garcia", "tax_id": "12345678Z", "debt_amount": "1250.00", "currency": "EUR", "court": "Juzgado n.3 de A Coruna"}'

curl "http://localhost:8000/api/expedientes/1/convertir/?currency=USD"

curl http://localhost:8000/api/expedientes/1/pdf/ --output expediente.pdf
```

> Nota: se evitan tildes/eñes en los ejemplos de `curl` a propósito. En Windows
> (tanto Git Bash como PowerShell), pasar caracteres acentuados directamente en
> un `-d` puede romperse por la codificación por defecto de la consola. La API
> sí acepta y devuelve UTF-8 correctamente (probado); es solo el ejemplo de
> terminal el que se simplifica para que funcione igual en cualquier sistema.

## Integración externa

La conversión de divisas usa la API pública de [Frankfurter](https://frankfurter.dev)
(`api.frankfurter.dev/v2`), que no requiere API key ni autenticación. Frankfurter
v2 solo expone un endpoint de tasa (`/v2/rate/{base}/{quote}`), no de conversión
directa, así que el importe se multiplica por la tasa en `exchange_service.py`
usando `Decimal` en todo el cálculo para evitar errores de redondeo con `float`.

Errores de esta integración se traducen a respuestas HTTP controladas:

| Situación | Código |
|---|---|
| Moneda solicitada no soportada | 400 |
| Expediente inexistente | 404 |
| El proveedor externo responde con error o datos inválidos | 502 |
| El proveedor externo no responde a tiempo (timeout) | 504 |

## Generación de PDF

`pdf_service.py` renderiza una plantilla HTML con los datos del expediente y
usa WeasyPrint para convertirla a PDF. Las dependencias de sistema que
WeasyPrint necesita (Pango, HarfBuzz) se instalan dentro de la imagen Docker,
por lo que no es necesario instalar nada adicional en la máquina del evaluador.

## Pruebas

```bash
docker compose exec web coverage run manage.py test
docker compose exec web coverage report
```

Las pruebas cubren: CRUD completo, validación de importe no positivo, 404 en
expediente inexistente, conversión de divisas con la llamada externa mockeada
(éxito, timeout, error del proveedor, respuesta malformada, moneda no
soportada, parámetro ausente y conversión entre la misma moneda), y que el
endpoint de PDF devuelve `application/pdf` con contenido válido (cabecera
`%PDF`). 18 tests, 99% de cobertura.

## Manejo de errores

Las validaciones del modelo (importe positivo, moneda soportada) y los
recursos inexistentes se apoyan en el comportamiento estándar de Django REST
Framework (400 y 404 automáticos vía serializer y `get_object()`). El manejo
explícito de errores se reserva para los puntos donde puede fallar algo
externo o técnico: la llamada a Frankfurter y la generación del PDF.

## Seguridad

- Sin credenciales en el repositorio: `.env` está en `.gitignore`, solo se
  versiona `.env.example` con valores de ejemplo.
- `DJANGO_DEBUG=False` en cualquier entorno que no sea desarrollo local.
- Sin autenticación de usuarios: no forma parte del alcance de esta prueba. En
  un entorno real, los endpoints de expedientes deberían protegerse mediante
  autenticación y autorización.

## Decisiones de diseño

- **Django REST Framework**: el enunciado pide un endpoint CRUD sobre una
  entidad; DRF permite implementar serialización, validación, routing y
  respuestas HTTP sobre el modelo sin construir esa infraestructura a mano.
- **PostgreSQL + Docker Compose** en vez de SQLite: la oferta valora
  específicamente la experiencia con PostgreSQL, y con Docker el arranque
  sigue siendo un único comando (`docker compose up --build`).
- **Referencia del expediente por UUID corto** (`EXP-XXXXXXXX`) en vez de un
  contador secuencial: evita problemas de concurrencia o reutilización de
  referencias si se borran expedientes, sin añadir complejidad.
- **Servicios separados** (`exchange_service.py`, `pdf_service.py`): el
  ViewSet no conoce los detalles HTTP del proveedor de divisas ni de la
  generación del PDF, lo que permite mockear ambos en los tests sin tocar la
  vista.
- **El endpoint `/convertir/` mantiene nombre en español** aunque el resto de
  identificadores del código están en inglés, para que la URL siga siendo
  reconocible dentro del dominio de negocio de la empresa.
- **Sin validación de checksum de DNI/NIF**: solo se valida longitud máxima.
  No es el objetivo de la prueba y añadiría complejidad fuera de alcance.
- **`opened_at` como fecha automática de creación**, sin distinguir de un
  posible `created_at`/`updated_at`: para el alcance de esta prueba no se pidió
  esa distinción y se ha simplificado conscientemente.
- **Sin Celery, Redis, autenticación ni funcionalidades de IA**: el enunciado
  no las pide y añadirlas sería sobreingeniería para una prueba de 2 días,
  aunque el puesto se llame "Desarrollo de IA".

## Limitaciones y posibles mejoras

- No hay autenticación ni control de acceso sobre los endpoints.
- La lista de monedas soportadas está limitada a EUR/USD/GBP; Frankfurter
  soporta más divisas y podría ampliarse fácilmente.
- No hay paginación configurable ni filtros de búsqueda sobre el listado de
  expedientes más allá de los que ofrece DRF por defecto.
- No se ha añadido caché sobre las tasas de cambio; en un entorno con más
  volumen convendría cachear las respuestas de Frankfurter durante unos
  minutos para reducir llamadas externas.
