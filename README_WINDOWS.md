# Proyecto Jorge Ambulatorio - Instalación Windows

Esta versión está preparada para probar en Windows con Python, Streamlit, Whisper local, OpenAI API, ficha clínica ambulatoria, diagnósticos CIE-10 y generación de mensajes HL7 v2 de prueba.

## Qué contiene

- `app.py`: aplicación principal Streamlit.
- `whisper_local.py`: transcripción local con faster-whisper.
- `prompts.py`: instrucciones clínicas para la nota IA.
- `cie10_seed.csv`: catálogo semilla CIE-10 orientado a neurología pediátrica.
- `requirements.txt`: dependencias Python.
- `.env.example`: plantilla para configurar la API key.
- `install_windows.bat`: crea el entorno virtual e instala dependencias.
- `run_windows.bat`: ejecuta la app.

## Requisitos previos

1. Windows 10 u 11.
2. Python 3.11 o 3.12 instalado desde python.org.
3. Marcar la opción **Add Python to PATH** durante la instalación.
4. Micrófono habilitado para aplicaciones de escritorio.
5. Una API key de OpenAI en el archivo `.env`.

## Instalación rápida

1. Descomprime el ZIP.
2. Entra a la carpeta `Proyecto Jorge`.
3. Haz doble clic en `install_windows.bat`.
4. Cuando termine, edita el archivo `.env` y reemplaza:

```env
OPENAI_API_KEY=pega_aqui_tu_api_key
```

por tu API key real.

5. Haz doble clic en `run_windows.bat`.
6. Se abrirá Streamlit en el navegador. Si no abre solo, entra a:

```text
http://localhost:8501
```

## Comandos manuales equivalentes

Desde PowerShell:

```powershell
cd "C:\ruta\a\Proyecto Jorge"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Si PowerShell bloquea la activación del entorno virtual, usa directamente:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Micrófono en Windows

La versión Windows usa `sounddevice` y `soundfile`, no `ffmpeg avfoundation`.

Si no graba:

1. En Windows abre **Configuración > Privacidad y seguridad > Micrófono**.
2. Activa el acceso al micrófono.
3. Activa el permiso para aplicaciones de escritorio.
4. En la app, abre **Herramientas de audio Windows** y presiona **Listar dispositivos de audio**.
5. Si necesitas forzar un dispositivo, edita `.env`:

```env
WINDOWS_AUDIO_DEVICE=1
```

Cambia `1` por el número del micrófono que aparece en la lista.

## Funcionalidades principales

1. Crear pacientes con datos demográficos mínimos.
2. Crear consultas ambulatorias.
3. Grabar conversación y dictado médico.
4. Transcribir localmente con Whisper.
5. Generar nota clínica con IA.
6. Registrar diagnósticos CIE-10.
7. Exportar nota en TXT o DOCX.
8. Generar mensajes HL7 v2.5 de prueba:
   - ADT^A04 para registro/check-in ambulatorio.
   - MDM^T02 para nota clínica.

## Importante sobre HL7

Esta versión genera archivos `.hl7` localmente, pero todavía no envía por MLLP/TCP ni procesa ACK/NACK. Para integrar con un HIS real se requiere:

- Host y puerto del motor de integración.
- Versión HL7 esperada.
- Reglas de identificación de paciente.
- Mapeo de campos PID, PV1, DG1, TXA y OBX.
- Ejemplos de mensajes aceptados por el HIS.
- Flujo de ACK/NACK esperado.

## Archivos generados

La app crea automáticamente:

```text
data\proyecto_jorge_ambulatorio.sqlite3
data\sessions
data\exports
```

Ahí quedan pacientes, consultas, audios, transcripciones, notas, DOCX/TXT y mensajes HL7 exportados.

## Ejecucion recomendada desde VS Code

Consulta tambien `README_WINDOWS_VSCODE.md`.

Comandos basicos:

```powershell
.\install_windows.bat
.\run_windows.bat
```

Ejecucion manual:

```powershell
.\.venv\Scripts\Activate
python -m streamlit run app.py
```
