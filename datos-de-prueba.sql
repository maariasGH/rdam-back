-- Insertar Administrador (registrador_id = NULL porque es el primero)
INSERT INTO usuarios (nombre_completo, login, password_hash, rol, estado) 
VALUES ('Administrador Jefe', 'admin_root', 'hash1', 'ADMINISTRADOR', 'Activo');

-- Insertar Operador (registrado por el admin con id 1)
INSERT INTO usuarios (nombre_completo, login, password_hash, rol, estado, registrador_id) 
VALUES ('Operador Turno Mañana', 'ope_m', 'hash2', 'OPERADOR', 'Activo', 1);

-- Trámite PENDIENTE creado por el ciudadano (id 3)
INSERT INTO tramites (cuil, nombre_solicitante, email_contacto, estado, ciudad_solicitante)
VALUES ('20301234567', 'Juan Pérez', 'juan@mail.com', 'PENDIENTE', 'Buenos Aires');

-- Trámite PAGADO
INSERT INTO tramites (cuil, nombre_solicitante, email_contacto, estado, ciudad_solicitante)
VALUES ('27405556661', 'Maria Garcia', 'maria@mail.com', 'PAGADA', 'Córdoba');

-- Registro de pago para el trámite 2
INSERT INTO pagos (tramite_id, external_reference, monto, pagado, fecha_pago)
VALUES (2, 'REF_PAY_998877', 1250.00, true, NOW());

-- Certificado emitido por el operador (id 2) para el trámite 2
INSERT INTO certificados (tramite_id, usuario_id, url_archivo_s3)
VALUES (2, 2, 's3://bucket-certificados/cert_001.pdf');

-- Insertar un código válido por 15 minutos para el ciudadano Juan Pérez
INSERT INTO codigos_temporales (email, codigo, expiracion)
VALUES ('juan@mail.com', '123456', NOW() + INTERVAL '15 minutes');

-- Insertar un código que ya expiró (para probar la lógica de error)
INSERT INTO codigos_temporales (email, codigo, expiracion)
VALUES ('maria@mail.com', '999888', NOW() - INTERVAL '1 hour');