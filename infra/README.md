# Infraestructura

Infraestructura base: reverse proxy, bases de datos, mensajeria, observabilidad, auth y storage.
Subcarpetas separan cada componente; `docker/` contiene la compose de desarrollo.

Proximos pasos: ajustar configuracion de redes, certificados y seguridad por entorno. La DB Postgres se inicializa con `infra/databases/postgres/init.sql` via docker-entrypoint.
