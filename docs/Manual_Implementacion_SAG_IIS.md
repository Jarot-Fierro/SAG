# Implementación de SAG (Django) en IIS + Waitress + NSSM

## 1. Objetivo

Este documento describe, desde cero, cómo desplegar **SAG**, un sistema Django, en un servidor Windows utilizando:

- Git para obtener el código fuente.
- Python y un entorno virtual (`venv`).
- Django y las dependencias del proyecto.
- Waitress como servidor WSGI.
- NSSM para ejecutar Waitress como servicio de Windows.
- IIS como servidor web frontal.
- URL Rewrite + Application Request Routing (ARR) para realizar el Reverse Proxy.
- IIS para servir archivos estáticos y multimedia.
- MariaDB/MySQL como base de datos.

La arquitectura final será:

```text
Usuario
   │
   ▼
IIS (80/443)
   │
   ├── /SAG/static/  → archivos estáticos
   │
   ├── /SAG/media/   → archivos multimedia
   │
   └── /SAG/         → Reverse Proxy
                         │
                         ▼
                 Waitress :8003
                         │
                         ▼
                 config.wsgi:application
                         │
                         ▼
                      Django
                         │
                         ▼
                    MariaDB/MySQL
```

---

# 2. Requisitos previos

Antes de comenzar, el servidor debe contar con:

- Windows Server/Windows.
- Git.
- Python.
- Acceso al repositorio Git.
- Acceso a la base de datos.
- Credenciales de la base de datos.
- NSSM.
- IIS.
- URL Rewrite.
- Application Request Routing (ARR).
- Permisos administrativos.

Para este ejemplo utilizaremos:

```text
Ruta del proyecto:
C:\inetpub\SAG

Entorno virtual:
C:\inetpub\SAG\venv

Puerto de Waitress:
8003

Nombre del servicio:
sag

Módulo WSGI:
config.wsgi:application
```

> **Importante:** estos valores son ejemplos. Si el puerto, nombre del servicio o ruta cambian, deben modificarse
> también en IIS y en la configuración de Django.

---

# 3. Obtener el código fuente

## 3.1 Crear/usar la carpeta `C:\inetpub`

El proyecto se desplegará dentro de:

```text
C:\inetpub
```

Por ejemplo:

```text
C:\inetpub\SAG
```

## 3.2 Clonar el repositorio

Abrir PowerShell o CMD y dirigirse a:

```powershell
cd C:\inetpub
```

Clonar el repositorio:

```powershell
git clone <URL_DEL_REPOSITORIO> SAG
```

Ejemplo:

```powershell
git clone https://servidor/repositorio/SAG.git SAG
```

Al finalizar debe existir:

```text
C:\inetpub\SAG
```

y dentro de ella el proyecto Django.

---

# 4. Crear el entorno virtual

Es recomendable aislar las librerías de Python del sistema.

Entrar al proyecto:

```powershell
cd C:\inetpub\SAG
```

Crear el entorno virtual:

```powershell
python -m venv venv
```

Esto generará:

```text
C:\inetpub\SAG\venv
```

## 4.1 Activar el entorno virtual

En PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución de scripts, ejecutar:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

y luego:

```powershell
.\venv\Scripts\Activate.ps1
```

Debe aparecer algo similar a:

```text
(venv) PS C:\inetpub\SAG>
```

---

# 5. Instalar las dependencias del sistema

Una vez activado el entorno virtual, actualizar pip:

```powershell
python -m pip install --upgrade pip
```

Luego instalar las dependencias del proyecto.

Si existe `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Esto instalará Django y las demás librerías necesarias para SAG.

---

# 6. Instalar Waitress

Waitress será el servidor WSGI que ejecutará Django.

Dentro del entorno virtual:

```powershell
pip install waitress
```

Se puede verificar con:

```powershell
pip show waitress
```

También es recomendable comprobar que Django esté correctamente instalado:

```powershell
python -m django --version
```

---

# 7. Configurar las variables de entorno

El proyecto debe tener su archivo:

```text
C:\inetpub\SAG\.env
```

Este archivo debe contener las variables necesarias para el ambiente de producción.

Por ejemplo:

```env
DEBUG=False

SECRET_KEY=CLAVE_SECRETA

DB_NAME=sag
DB_USER=sag
DB_PASSWORD=CLAVE_BASE_DATOS
DB_HOST=10.8.85.100
DB_PORT=3306

APP_URL_PREFIX=/SAG
FORCE_SCRIPT_NAME=/SAG

STATIC_URL=/SAG/static/
MEDIA_URL=/SAG/media/
```

Los nombres exactos dependen de cómo esté implementado `settings.py`.

## 7.1 Configuración de la base de datos

La configuración de Django debe tomar los valores desde las variables de entorno.

Ejemplo conceptual:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "3306"),
    }
}
```

### Importante

`DB_HOST` no debe quedar como `None`.

Por ejemplo:

```env
DB_HOST=10.8.85.100
```

o, si la base de datos está en el mismo servidor:

```env
DB_HOST=127.0.0.1
```

---

# 8. Configurar el prefijo utilizado por IIS

En este despliegue SAG será publicado bajo:

```text
/SAG/
```

Por lo tanto, Django debe conocer ese prefijo.

Por ejemplo:

```env
APP_URL_PREFIX=/SAG
FORCE_SCRIPT_NAME=/SAG
```

Y la configuración de archivos puede ser:

```python
STATIC_URL = "/SAG/static/"
MEDIA_URL = "/SAG/media/"
```

El resultado esperado será:

```text
https://servidor/SAG/
https://servidor/SAG/static/
https://servidor/SAG/media/
```

> El prefijo debe coincidir con la aplicación virtual configurada posteriormente en IIS.

---

# 9. Ejecutar las migraciones

Antes de poner el sistema en funcionamiento, ejecutar:

```powershell
python manage.py migrate
```

Si SAG utiliza datos iniciales mediante comandos de seed, fixtures u otro mecanismo, ejecutarlos en este momento.

Por ejemplo, si el proyecto posee un comando propio:

```powershell
python manage.py seed
```

El comando exacto dependerá del proyecto.

---

# 10. Crear el usuario administrador

Si corresponde a la instalación inicial:

```powershell
python manage.py createsuperuser
```

Completar los datos solicitados.

---

# 11. Generar los archivos estáticos

Ejecutar:

```powershell
python manage.py collectstatic --noinput
```

Django recopilará los archivos estáticos de las aplicaciones en `STATIC_ROOT`.

Es importante comprobar que `STATIC_ROOT` esté correctamente configurado.

Por ejemplo:

```python
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Después de ejecutar `collectstatic`, debe existir una carpeta similar a:

```text
C:\inetpub\SAG\staticfiles
```

---

# 12. Realizar una prueba de Django antes de IIS

Antes de crear el servicio, conviene comprobar que Django funciona.

Ejecutar:

```powershell
python manage.py check
```

Si no existen errores, probar la aplicación directamente con Waitress.

Desde:

```text
C:\inetpub\SAG
```

ejecutar:

```powershell
waitress-serve --host=0.0.0.0 --port=8003 config.wsgi:application
```

La consola debería indicar que Waitress está escuchando en el puerto `8003`.

Probar desde el mismo servidor:

```text
http://127.0.0.1:8003
```

Si Django requiere el prefijo `/SAG`, probar:

```text
http://127.0.0.1:8003/SAG/
```

> Si esta prueba falla, **no continuar con IIS**. Primero hay que corregir Django/Waitress.

Para detener Waitress:

```text
Ctrl + C
```

---

# 13. Instalar NSSM

NSSM permite ejecutar Waitress como un servicio de Windows.

Por ejemplo, podemos tener:

```text
C:\nssm-2.24\win64\nssm.exe
```

Comprobar que existe:

```powershell
dir C:\nssm-2.24\win64
```

Debe aparecer:

```text
nssm.exe
```

---

# 14. Crear el servicio de SAG

Abrir **CMD como administrador**.

También se puede utilizar `Windows + R` y escribir:

```text
cmd
```

pero para crear el servicio se recomienda abrir la consola con permisos de administrador.

Ejecutar:

```cmd
C:\nssm-2.24\win64\nssm.exe install SAG
```

Se abrirá la ventana de configuración de NSSM.

## 14.1 Nombre del servicio

Utilizar:

```text
sag
```

o:

```text
SAG
```

Windows no diferencia mayúsculas/minúsculas en este nombre.

## 14.2 Path

Indicar:

```text
C:\inetpub\SAG\venv\Scripts\waitress-serve.exe
```

## 14.3 Startup directory

Indicar:

```text
C:\inetpub\SAG
```

## 14.4 Arguments

Indicar:

```text
--host=0.0.0.0 --port=8003 config.wsgi:application
```

La configuración final queda:

| Parámetro         | Valor                                                |
|-------------------|------------------------------------------------------|
| Service name      | `SAG`                                                |
| Path              | `C:\inetpub\SAG\venv\Scripts\waitress-serve.exe`     |
| Startup directory | `C:\inetpub\SAG`                                     |
| Arguments         | `--host=0.0.0.0 --port=8003 config.wsgi:application` |
| Puerto            | `8003`                                               |
| WSGI              | `config.wsgi:application`                            |

Presionar:

```text
Install service
```

---

# 15. Configurar el inicio automático

Una vez creado el servicio, puede configurarse para iniciar automáticamente con Windows.

Desde CMD como administrador:

```cmd
sc config SAG start= auto
```

También se puede configurar desde:

```text
services.msc
```

Buscar:

```text
SAG
```

y establecer:

```text
Tipo de inicio: Automático
```

---

# 16. Iniciar el servicio

Desde CMD:

```cmd
C:\nssm-2.24\win64\nssm.exe start SAG
```

Comprobar el estado:

```cmd
C:\nssm-2.24\win64\nssm.exe status SAG
```

El resultado esperado es:

```text
SERVICE_RUNNING
```

También se puede comprobar con:

```cmd
sc query SAG
```

---

# 17. Comprobar Waitress

Antes de configurar IIS, comprobar que el puerto está escuchando:

```cmd
netstat -ano | findstr :8003
```

Debe aparecer una conexión escuchando en el puerto:

```text
0.0.0.0:8003
```

o equivalente.

También se puede probar desde el servidor:

```text
http://127.0.0.1:8003
```

Si funciona, Waitress + Django están correctamente configurados.

---

# 18. Instalar IIS

Abrir PowerShell **como administrador**.

Ejecutar:

```powershell
Enable-WindowsOptionalFeature -Online `
    -FeatureName IIS-WebServerRole, `
                  IIS-WebServer, `
                  IIS-CommonHttpFeatures, `
                  IIS-DefaultDocument, `
                  IIS-DirectoryBrowsing, `
                  IIS-HttpErrors, `
                  IIS-StaticContent, `
                  IIS-RequestFiltering, `
                  IIS-ManagementConsole, `
                  IIS-CGI `
    -All
```

Reiniciar Windows si el sistema lo solicita.

Después se puede abrir IIS mediante:

```text
Windows + R
```

y:

```text
inetmgr
```

---

# 19. Instalar componentes necesarios para Reverse Proxy

Para que IIS pueda actuar como Reverse Proxy se necesitan:

1. URL Rewrite.
2. Application Request Routing (ARR).

## 19.1 URL Rewrite

Descargar e instalar **IIS URL Rewrite** desde el sitio oficial:

https://www.iis.net/downloads/microsoft/url-rewrite

URL Rewrite permite crear reglas como:

```text
/SAG/
```

→

```text
http://10.8.85.141:8003/
```

## 19.2 Application Request Routing

Instalar **Application Request Routing (ARR)** compatible con la versión de IIS.

Después de instalar ARR, abrir:

```text
IIS Manager
```

Seleccionar el servidor y entrar en:

```text
Application Request Routing Cache
```

Luego:

```text
Server Proxy Settings
```

Activar:

```text
Enable proxy
```

Guardar los cambios.

> Sin esta opción IIS no funcionará correctamente como Reverse Proxy.

---

# 20. Instalar PHP para IIS (si el servidor también lo requiere)

Si el mismo servidor debe ejecutar aplicaciones PHP, se debe configurar PHP mediante FastCGI.

En IIS ya se instaló:

```text
IIS-CGI
```

que es necesario para este escenario.

Se debe instalar una versión de PHP compatible con el sistema, normalmente utilizando la distribución **NTS (Non Thread
Safe)** para IIS/FastCGI.

El ejecutable utilizado por IIS será:

```text
php-cgi.exe
```

La configuración de PHP es independiente de SAG.

> PHP no es necesario para ejecutar Django. Solo debe instalarse si el servidor también alojará sistemas PHP.

---

# 21. Crear la aplicación virtual SAG en IIS

Abrir:

```text
inetmgr
```

En IIS:

```text
Sites
└── Default Web Site
```

Hacer clic derecho sobre:

```text
Default Web Site
```

y seleccionar:

```text
Add Application...
```

Configurar:

```text
Alias:
SAG
```

Ruta física:

```text
C:\inetpub\SAG
```

La estructura quedará:

```text
Default Web Site
└── SAG
```

Por lo tanto, el sistema será accesible mediante:

```text
http://servidor/SAG/
```

---

# 22. Dar permisos a la carpeta

La cuenta utilizada por IIS debe poder leer la aplicación.

Seleccionar:

```text
C:\inetpub\SAG
```

→ Propiedades

→ Seguridad

Agregar o verificar los permisos correspondientes para IIS.

Como mínimo, el proceso debe poder:

- Leer archivos de la aplicación.
- Acceder a los archivos estáticos.
- Acceder a los archivos multimedia.
- Escribir en directorios que Django necesite modificar durante la ejecución.

> No se recomienda entregar permisos de escritura a toda la aplicación si no son necesarios. Los permisos de escritura
> deben limitarse a las carpetas que realmente los requieren.

---

# 23. Configurar el Reverse Proxy

Dentro de:

```text
C:\inetpub\SAG
```

crear o modificar:

```text
web.config
```

La configuración base será:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxyInboundRule1" stopProcessing="true">
                    <match url="(.*)"/>
                    <conditions>
                        <add input="{CACHE_URL}" pattern="^(https?)://"/>
                    </conditions>
                    <action type="Rewrite" url="{C}://10.8.85.141:8003/{R:1}"/>
                </rule>
            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

### Importante: puerto

El puerto:

```text
8003
```

debe ser exactamente el mismo configurado en NSSM:

```text
--host=0.0.0.0 --port=8003
```

Si se cambia el puerto del servicio, también debe cambiarse en `web.config`.

Por ejemplo:

```text
Waitress → 8003
IIS     → 8003
```

---

# 24. Consideración importante sobre la IP del Reverse Proxy

En el ejemplo se utiliza:

```text
10.8.85.141:8003
```

Esta IP debe corresponder al destino donde realmente está escuchando Waitress.

Si IIS y Waitress están en el **mismo servidor**, es preferible utilizar:

```text
127.0.0.1:8003
```

Por ejemplo:

```xml

<action type="Rewrite" url="{C}://127.0.0.1:8003/{R:1}"/>
```

Esto evita exponer innecesariamente el puerto de Waitress en la red.

Si Waitress está en otro servidor, entonces se debe utilizar la IP de ese servidor.

---

# 25. Configurar archivos estáticos

Django no debería utilizar Waitress para servir los archivos estáticos en producción.

Primero ejecutar:

```powershell
python manage.py collectstatic --noinput
```

Por ejemplo:

```text
C:\inetpub\SAG\staticfiles
```

debe contener los archivos recopilados.

---

# 26. Crear el directorio virtual `static` en IIS

Dentro de:

```text
Default Web Site
└── SAG
```

crear un **Virtual Directory**.

Configuración:

```text
Alias:
static
```

Ruta física:

```text
C:\inetpub\SAG\staticfiles
```

De esta forma:

```text
/SAG/static/
```

apuntará directamente a:

```text
C:\inetpub\SAG\staticfiles
```

---

# 27. Regla de exclusión para static

La regla Reverse Proxy no debe enviar los archivos estáticos hacia Django.

En IIS se puede agregar una regla para excluir:

```text
/SAG/static/
```

La condición indicada en la configuración utilizada para este despliegue es:

```text
Entrada:
{REQUEST_URI}

Tipo:
No coincide con el patrón

Patrón:
^/SAG/static/
```

La idea es:

```text
/SAG/static/
       │
       ▼
IIS
       │
       ▼
C:\inetpub\SAG\staticfiles
```

y no:

```text
/SAG/static/
       │
       ▼
Waitress
       │
       ▼
Django
```

---

# 28. Configurar archivos multimedia

El mismo procedimiento debe realizarse para:

```text
media
```

Crear un Virtual Directory:

```text
Alias:
media
```

Ruta física:

```text
C:\inetpub\SAG\media
```

De esta forma:

```text
/SAG/media/
```

apuntará directamente a:

```text
C:\inetpub\SAG\media
```

---

# 29. Regla de exclusión para media

En IIS crear una regla equivalente a la de static.

Configurar:

```text
Entrada:
{REQUEST_URI}

Tipo:
No coincide con el patrón

Patrón:
^/SAG/media/
```

El objetivo es:

```text
/SAG/media/
      │
      ▼
IIS
      │
      ▼
C:\inetpub\SAG\media
```

en lugar de enviar los archivos a Django.

---

# 30. Orden de las reglas de IIS

El orden de las reglas es importante.

Las exclusiones de:

```text
/SAG/static/
```

y:

```text
/SAG/media/
```

deben procesarse antes de la regla general del Reverse Proxy.

La regla general:

```text
(.*)
```

es muy amplia y puede capturar todas las solicitudes si se encuentra antes de las exclusiones.

Conceptualmente:

```text
/SAG/static/*
       ↓
   ARCHIVO IIS

/SAG/media/*
       ↓
   ARCHIVO IIS

/SAG/*
       ↓
 Reverse Proxy
       ↓
 Waitress
       ↓
 Django
```

---

# 31. Verificar `web.config`

Una configuración final puede tener reglas de exclusión antes del Reverse Proxy.

Por ejemplo:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>

                <!-- STATIC -->
                <rule name="StaticFiles" stopProcessing="true">
                    <match url="^static/(.*)"/>
                    <action type="Rewrite"
                            url="C:\inetpub\SAG\staticfiles\{R:1}"/>
                </rule>

                <!-- MEDIA -->
                <rule name="MediaFiles" stopProcessing="true">
                    <match url="^media/(.*)"/>
                    <action type="Rewrite"
                            url="C:\inetpub\SAG\media\{R:1}"/>
                </rule>

                <!-- REVERSE PROXY -->
                <rule name="ReverseProxyInboundRule1" stopProcessing="true">
                    <match url="(.*)"/>
                    <conditions>
                        <add input="{CACHE_URL}" pattern="^(https?)://"/>
                    </conditions>
                    <action type="Rewrite"
                            url="{C}://127.0.0.1:8003/{R:1}"/>
                </rule>

            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

> **Nota:** si se utilizan Virtual Directories separados para `static` y `media`, no necesariamente se deben implementar
> estas reglas de reescritura de archivos de la misma forma. Lo importante es que las solicitudes de archivos no terminen
> en la regla general del Reverse Proxy.

---

# 32. Configurar Django para archivos estáticos y media

Verificar en `settings.py`:

```python
STATIC_URL = "/SAG/static/"
MEDIA_URL = "/SAG/media/"
```

Y las rutas físicas correspondientes:

```python
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
```

La configuración exacta debe respetar la estructura actual del proyecto.

---

# 33. Configuración de hosts y seguridad

En producción, revisar:

```python
DEBUG = False
```

Configurar correctamente:

```python
ALLOWED_HOSTS = [
    "nombre-servidor",
    "IP-SERVIDOR",
]
```

Si se utiliza HTTPS, revisar también:

```python
CSRF_TRUSTED_ORIGINS
```

Por ejemplo:

```python
CSRF_TRUSTED_ORIGINS = [
    "https://servidor.ejemplo.cl",
]
```

Los valores reales dependen del dominio utilizado.

---


Después de realizar modificaciones importantes, se puede reiniciar IIS:

```cmd
iisreset
```

También se puede reiniciar desde IIS Manager.

---

# 37. Reiniciar el servicio SAG

Para reiniciar Waitress mediante NSSM:

```cmd
C:\nssm-2.24\win64\nssm.exe restart SAG
```

Comprobar:

```cmd
C:\nssm-2.24\win64\nssm.exe status SAG
```

---

# 38. Actualizar SAG posteriormente

Cuando exista una nueva versión del sistema:

## 38.1 Detener el servicio

```cmd
C:\nssm-2.24\win64\nssm.exe stop SAG
```

## 38.2 Actualizar código

Desde:

```text
C:\inetpub\SAG
```

ejecutar:

```powershell
git pull
```

## 38.3 Activar el entorno virtual

```powershell
.\venv\Scripts\Activate.ps1
```

## 38.4 Actualizar dependencias

Si cambió `requirements.txt`:

```powershell
pip install -r requirements.txt
```

## 38.5 Ejecutar migraciones

```powershell
python manage.py migrate
```

## 38.6 Recopilar estáticos

```powershell
python manage.py collectstatic --noinput
```

## 38.7 Iniciar nuevamente SAG

```cmd
C:\nssm-2.24\win64\nssm.exe start SAG
```

---

# 40. Arquitectura final

La instalación completa queda de la siguiente manera:

```text
                         INTERNET
                            │
                            ▼
                    ┌────────────────┐
                    │      IIS       │
                    │    :80 / :443  │
                    └───────┬────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       /SAG/static/   /SAG/media/       /SAG/*
             │              │              │
             ▼              ▼              ▼
       staticfiles         media       URL Rewrite
                                           │
                                           ▼
                                    Application
                                    Request Routing
                                           │
                                           ▼
                                  127.0.0.1:8003
                                           │
                                           ▼
                                     Waitress
                                           │
                                           ▼
                               config.wsgi:application
                                           │
                                           ▼
                                        Django
                                           │
                                           ▼
                                    MariaDB/MySQL
```

---

# 41. Resumen rápido de comandos

## Clonar

```powershell
cd C:\inetpub
git clone <URL_DEL_REPOSITORIO> SAG
cd SAG
```

## Crear entorno virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install waitress
```

## Comprobar Django

```powershell
python manage.py check
```

## Migraciones

```powershell
python manage.py migrate
```

## Static

```powershell
python manage.py collectstatic --noinput
```

## Probar Waitress

```powershell
waitress-serve --host=0.0.0.0 --port=8003 config.wsgi:application
```

## Crear servicio

```cmd
C:\nssm-2.24\win64\nssm.exe install SAG
```

Configuración:

```text
Path:
C:\inetpub\SAG\venv\Scripts\waitress-serve.exe

Startup directory:
C:\inetpub\SAG

Arguments:
--host=0.0.0.0 --port=8003 config.wsgi:application
```

## Iniciar servicio

```cmd
C:\nssm-2.24\win64\nssm.exe start SAG
```

## Ver estado

```cmd
C:\nssm-2.24\win64\nssm.exe status SAG
```

## Reiniciar

```cmd
C:\nssm-2.24\win64\nssm.exe restart SAG
```

## Detener

```cmd
C:\nssm-2.24\win64\nssm.exe stop SAG
```

## IIS

Abrir:

```text
inetmgr
```

o:

```text
Windows + R → inetmgr
```

## Reiniciar IIS

```cmd
iisreset
```

---

# 44. Estructura esperada del servidor

Al finalizar, una estructura típica será:

```text
C:\
└── inetpub\
    └── SAG\
        ├── config\
        │   ├── settings.py
        │   ├── urls.py
        │   └── wsgi.py
        │
        ├── venv\
        │   └── Scripts\
        │       └── waitress-serve.exe
        │
        ├── staticfiles\
        │
        ├── media\
        │
        ├── manage.py
        ├── requirements.txt
        ├── .env
        └── web.config
```

El servicio de Windows:

```text
SAG
```

ejecuta:

```text
C:\inetpub\SAG\venv\Scripts\waitress-serve.exe
```

con:

```text
--host=0.0.0.0 --port=8003 config.wsgi:application
```

e IIS publica:

```text
/SAG/
```

hacia el servidor Django.

---

# 45. Resultado

Una vez finalizada la configuración, el usuario no debería acceder directamente a:

```text
http://servidor:8003
```

sino a:

```text
https://servidor/SAG/
```

IIS recibe la solicitud, sirve directamente los archivos estáticos/media y deriva las solicitudes dinámicas mediante
Reverse Proxy hacia Waitress.

De esta forma, SAG queda ejecutándose como un servicio de Windows y se inicia automáticamente junto con el servidor.
