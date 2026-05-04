# Proyecto Jorge - versión macOS

Esta versión está preparada para Mac. Usa:

- `ffmpeg` para grabar audio desde el micrófono de macOS.
- `faster-whisper` local para transcribir gratis.
- OpenAI API para estructurar la nota clínica, visión de imágenes y chat.

## 1. Requisitos del sistema

Instala Homebrew si no lo tienes:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Instala Python y ffmpeg:

```bash
brew install python@3.11 ffmpeg
```

## 2. Preparar el proyecto

En Terminal, entra a la carpeta del proyecto:

```bash
cd "RUTA/Proyecto Jorge"
```

Crea el entorno virtual:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## 3. Crear el archivo .env

Copia el ejemplo:

```bash
cp .env.example .env
```

Edita `.env` y pega la API key:

```bash
OPENAI_API_KEY=tu_api_key
MAC_AUDIO_DEVICE=:0
```

## 4. Ejecutar

```bash
source .venv/bin/activate
streamlit run app.py
```

También puedes usar:

```bash
./run_mac.sh
```

## 5. Permiso de micrófono

macOS puede pedir permiso para Terminal/iTerm.

Si no graba:

1. Abre la app.
2. Entra a “Herramientas de audio macOS”.
3. Presiona “Listar dispositivos de audio”.
4. Cambia `MAC_AUDIO_DEVICE` en `.env` a `:1`, `:2`, etc.
5. Reinicia Streamlit.

## 6. Importante

El archivo `.env` no debe compartirse porque contiene la API key.
La carpeta `.venv` no se incluye; se crea localmente en cada Mac.
