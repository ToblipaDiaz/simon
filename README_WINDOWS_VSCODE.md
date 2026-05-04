# Proyecto Jorge 2.0 - Windows desde VS Code

Esta version es para ejecutar localmente en Windows usando Visual Studio Code.

## 1. Abrir carpeta

1. Descomprime el ZIP.
2. Abre VS Code.
3. Ve a File > Open Folder.
4. Selecciona la carpeta `Proyecto Jorge 2.0`.

## 2. Abrir terminal integrada

En VS Code abre:

Terminal > New Terminal

Confirma que estas dentro de la carpeta correcta:

```powershell
pwd
```

Debes ver una ruta parecida a:

```powershell
C:\Users\padiaz\OneDrive - InterSystems Corporation\Escritorio\Proyecto Jorge 2.0
```

## 3. Instalar por primera vez

Ejecuta:

```powershell
.\install_windows.bat
```

Si PowerShell bloquea el BAT, ejecuta:

```powershell
cmd /c install_windows.bat
```

Esto crea `.venv`, instala dependencias y crea `.env` desde `.env.example` si no existe.

## 4. Configurar API Key

Abre el archivo `.env` en VS Code y completa:

```env
OPENAI_API_KEY=tu_api_key_real
```

Para probar login inicial local puedes usar:

```env
PJ_ADMIN_EMAIL=admin@gmail.com
PJ_ADMIN_PASSWORD=admin1234
```

## 5. Configurar correo Gmail para envio automatico

Para enviar el Word automaticamente al profesional, Gmail requiere App Password, no la password normal.

En `.env` configura:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password_de_gmail
SMTP_FROM=tu_correo@gmail.com
AUTO_EMAIL_ON_NOTE=true
```

Si no quieres probar correo al inicio, deja `AUTO_EMAIL_ON_NOTE=false`.

## 6. Ejecutar la app

Ejecuta:

```powershell
.\run_windows.bat
```

O manualmente:

```powershell
.\.venv\Scripts\Activate
python -m streamlit run app.py
```

Abre en el navegador:

```text
http://localhost:8501
```

## 7. Si el microfono no funciona

En la app abre Herramientas de audio Windows y lista los dispositivos.

Luego edita `.env`:

```env
WINDOWS_AUDIO_DEVICE=1
```

Cambia el numero por el indice correcto que muestre tu equipo.

## 8. Flujo esperado

1. Iniciar sesion.
2. Entrar como administrador con `admin@gmail.com` / `admin1234`.
3. Crear centros, medicos y usuarios.
4. Completar primer ingreso del profesional si corresponde.
5. Ir a agenda.
6. Crear paciente y cita.
7. Abrir consulta.
8. Grabar conversacion o dictado.
9. Procesar nota.
10. Exportar Word/TXT y generar HL7.
11. Si SMTP esta configurado, enviar automaticamente Word SOAP al correo del profesional.

## 9. Consideraciones

- La fecha de nacimiento permite seleccionar desde 01/01/1970.
- La app corre localmente; no es hosting productivo.
- HL7 queda generado como archivo para pruebas. Para integracion real con un HIS se debe agregar envio MLLP/TCP y reglas del motor de integracion.
