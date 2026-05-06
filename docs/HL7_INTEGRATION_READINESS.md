# HL7 Integration Readiness

## Alcance

Asistente Simon genera mensajes HL7 v2.5 para integracion con un motor externo
como InterSystems IRIS Interoperability, Mirth/NextGen Connect, Rhapsody,
Cloverleaf u otro. La aplicacion no integra de forma nativa con un HIS/RCE
especifico y no usa ingenieria inversa.

## Mensajes Soportados

- `ADT^A04`: registro/admisión ambulatoria.
- `MDM^T02`: documento clinico/nota SOAP.
- `ORU^R01`: estructura opcional para observaciones clinicas.
- `SIU^S12`: placeholder futuro para agenda/citas, pendiente de reglas formales.

Segmentos base: `MSH`, `EVN`, `PID`, `PV1`, `TXA`, `DG1`, `OBX`.

## Campos Minimos

- `MSH-10`: control id.
- `PID-3` o `PID-18`: identificador de paciente, si
  `HL7_REQUIRE_PATIENT_IDENTIFIER=true`.
- `PV1`: obligatorio para ADT, MDM y ORU.
- `TXA`: obligatorio para MDM.
- `OBX`: obligatorio en MDM cuando se envia nota clinica.

## Flujo Recomendado

1. IA genera borrador de nota clinica.
2. Profesional revisa y marca la nota como revisada.
3. La app genera mensaje HL7 en cola como `DRAFT`.
4. La validacion marca el mensaje como `READY`.
5. En modo `file`, se exporta archivo `.hl7` para pruebas del motor.
6. En modo futuro `mllp`, el motor/HIS retorna ACK/NACK.
7. La cola registra `SENT`, `ACKED`, `NACKED` o `ERROR`.

## Modo File

`HL7_MODE=file` guarda mensajes en `HL7_EXPORT_DIR`. Este es el modo recomendado
para pruebas con motor de integracion y validacion de mapeos.

## Modo MLLP Futuro

`HL7_MODE=mllp` requiere host, puerto, facility/app destino y acuerdo formal con
el receptor. Puede usar TLS si se configuran certificados. No debe activarse en
produccion sin ambiente de pruebas y reglas de ACK/NACK aprobadas.

## Seguridad

- `HL7_ENABLED=false` bloquea envios.
- `HL7_REQUIRE_REVIEW=true` impide envio si la nota no fue revisada por medico.
- No se imprimen payloads completos en logs normales.
- Se calcula SHA-256 del payload para trazabilidad sin exponer contenido.
- SMTP queda desactivado por defecto; no enviar datos clinicos por correo sin
  autorizacion institucional.
- `APP_ENV=production` bloquea contraseña admin por defecto.

## Limitaciones

Los mensajes son una base extensible, no una certificacion completa de perfil
HL7 para un HIS destino. Cada proveedor debe entregar campos obligatorios,
tablas, codigos, ejemplos aceptados y reglas de ACK.

## Checklist HIS Destino

- Aplicacion/facility emisora y receptora.
- Version HL7 y perfil esperado.
- Reglas de identificacion de paciente.
- Campos obligatorios por segmento.
- Codigos para profesional, centro, especialidad y tipo de visita.
- Reglas para CIE-10 y estados diagnosticos.
- Tipo de documento clinico aceptado.
- Canal de transporte: file, SFTP, MLLP, TLS.
- ACK/NACK esperado y manejo de errores.
- Ambiente de pruebas con pacientes ficticios.
- Contrato/API formal y autorizacion institucional.

