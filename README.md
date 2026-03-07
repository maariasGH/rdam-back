RDAM Santa Fe - Backend Oficial
Este es el backend oficial del sistema de gestión de trámites RDAM. Desarrollado con FastAPI, SQLAlchemy y PostgreSQL.

🚀 Características

Simuladas (Futuro Desarrollo Completo cuando se integre el FrontEnd):
Autenticación: JWT con validación de tokens y OTP vía Mailtrap.

Seguridad: Integración con Google reCAPTCHA v3.

Pagos: Integración con Mock de PlusPagos.

Completas:
Certificados: Generación automática de PDFs con ReportLab.

🛠️ Instalación y Configuración
1. Requisitos Previos
Python 3.10+

PostgreSQL instalado y corriendo.

2. Clonar el repositorio
Bash
git clone https://github.com/tu-usuario/rdam-backend.git
cd rdam-backend

3. Instalar dependencias
Ejecuta el siguiente comando para instalar todas las librerías necesarias:

Bash
pip install fastapi uvicorn sqlalchemy pydantic[email] reportlab requests python-multipart pycryptodome psycopg2-binary python-jose[cryptography] python-dotenv mailtrap

4. Variables de Entorno
Crea un archivo .env dentro de la carpeta app/ con el siguiente contenido:

Fragmento de código
SECRET_KEY=tu_clave_secreta_super_larga
SMTP_USER=tu_usuario_mailtrap
SMTP_PASS=tu_password_mailtrap
SMTP_SERVER=smtp.mailtrap.io
SMTP_PORT=2525
API_TOKEN=tu_token_mailtrap
MERCHANT_GUID=tu_guid_comercio
PLUSPAGOS_URL=url_del_mock_pluspagos
RECAPTCHA_SECRET_KEY=tu_clave_google_recaptcha

🏃‍♂️ Cómo ejecutar el proyecto
Iniciar el servidor:

Bash
uvicorn app.main:app --reload

Acceder a la documentación:
Una vez iniciado, entra en http://localhost:8000/docs. Allí podrás probar todos los endpoints usando la interfaz de Swagger UI.

🧪 Pruebas con Postman
Para facilitar las pruebas, hemos incluido una colección.

Importa el archivo RDAM_Collection.json en Postman.

Asegúrate de configurar la variable base_url como http://localhost:8000.

Para endpoints protegidos, primero verifica el código del ciudadano, copia el access_token y pégalo en el header Authorization (formato: Bearer <TOKEN>).

📝 Notas de Desarrollo
Captcha: En desarrollo, puedes usar el token token_prueba_123 para saltar la validación de Google reCAPTCHA.

Base de Datos: El sistema creará las tablas automáticamente al iniciar gracias a models.Base.metadata.create_all.