# Proyecto Jorge Ambulatorio

Esta versión evoluciona el asistente local de dictado clínico hacia una ficha clínica ambulatoria básica.

## Qué incluye

1. Registro local de pacientes en SQLite.
2. Datos demográficos mínimos: MRN, nombre, apellidos, documento/RUN, fecha de nacimiento, sexo, contacto, tutor y dirección.
3. Consultas ambulatorias por paciente.
4. Reutilización del flujo IA existente:
   - grabación de conversación,
   - grabación de dictado médico,
   - transcripción local con Whisper,
   - estructuración de nota clínica con OpenAI API,
   - edición manual de nota,
   - exportación TXT/DOCX.
5. Diagnósticos CIE-10:
   - catálogo semilla orientado a neurología pediátrica,
   - búsqueda local,
   - registro de diagnósticos principal/secundario/antecedente/diferencial,
   - certeza: sospecha, confirmado o descartado.
6. Preparación HL7 v2:
   - ADT^A04 para registro ambulatorio/check-in.
   - MDM^T02 para envío de nota clínica/documento.
   - Segmentos principales: MSH, EVN, PID, PV1, TXA, DG1 y OBX.

## Límites importantes

Esta versión genera archivos .hl7 para pruebas de integración. Aún no envía por TCP/MLLP ni gestiona ACK/NACK.
Para conectar con un HIS real se necesita que el proveedor del HIS entregue:

- versión HL7 esperada,
- host y puerto MLLP,
- aplicación emisora y receptora,
- reglas de identificación de paciente,
- campos obligatorios por segmento,
- tabla de mapeo para sexo, ubicación, profesional y especialidad,
- reglas para diagnósticos CIE-10,
- tipo de mensaje esperado para documentos clínicos,
- ejemplos válidos aceptados por el motor de integración.

## Instalación Mac

Usar los mismos pasos del README_MAC.md.

Luego ejecutar:

```bash
./run_mac.sh
```

La base SQLite se crea automáticamente en:

```text
data/proyecto_jorge_ambulatorio.sqlite3
```

Las exportaciones se guardan en:

```text
data/exports
```
