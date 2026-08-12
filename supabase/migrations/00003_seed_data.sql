-- Orkesta Ritmo - Seed Data
-- Fiscal parameters, tax tables, and IVA questionnaire graph.

-- ============================================================
-- EJERCICIO 2025
-- ============================================================

INSERT INTO ejercicios (id, anio, uma_mensual, uma_diaria) VALUES
    ('a0000000-0000-0000-0000-000000002025', 2025, 3471.90, 113.14);

-- RESICO tarifa mensual 2025
INSERT INTO tarifas_resico (ejercicio_id, limite_superior, tasa, orden) VALUES
    ('a0000000-0000-0000-0000-000000002025', 25000.00, 0.0100, 1),
    ('a0000000-0000-0000-0000-000000002025', 50000.00, 0.0110, 2),
    ('a0000000-0000-0000-0000-000000002025', 83888.33, 0.0150, 3),
    ('a0000000-0000-0000-0000-000000002025', 208333.33, 0.0200, 4),
    ('a0000000-0000-0000-0000-000000002025', 291666.66, 0.0250, 5);

-- Art 96 tarifa mensual 2025
INSERT INTO tarifas_art96 (ejercicio_id, limite_inferior, limite_superior, cuota_fija, porcentaje, orden) VALUES
    ('a0000000-0000-0000-0000-000000002025', 0.01, 844.59, 0.00, 0.0192, 1),
    ('a0000000-0000-0000-0000-000000002025', 844.60, 7168.51, 16.22, 0.0640, 2),
    ('a0000000-0000-0000-0000-000000002025', 7168.52, 12598.02, 420.95, 0.1088, 3),
    ('a0000000-0000-0000-0000-000000002025', 12598.03, 14644.64, 1011.68, 0.1600, 4),
    ('a0000000-0000-0000-0000-000000002025', 14644.65, 17533.64, 1339.14, 0.1792, 5),
    ('a0000000-0000-0000-0000-000000002025', 17533.65, 35362.83, 1856.84, 0.2136, 6),
    ('a0000000-0000-0000-0000-000000002025', 35362.84, 55736.68, 5665.16, 0.2352, 7),
    ('a0000000-0000-0000-0000-000000002025', 55736.69, 106410.50, 10457.09, 0.3000, 8),
    ('a0000000-0000-0000-0000-000000002025', 106410.51, 141880.66, 25659.23, 0.3200, 9),
    ('a0000000-0000-0000-0000-000000002025', 141880.67, 425641.99, 37009.69, 0.3400, 10),
    ('a0000000-0000-0000-0000-000000002025', 425642.00, NULL, 133488.54, 0.3500, 11);

-- ============================================================
-- CUESTIONARIO IVA - Grafo declarativo
-- ============================================================

-- Entry nodes
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('P1', 'Confirma tu régimen fiscal para comenzar.', 'filtro'),
    ('A1', 'Describe la actividad principal por la que emites facturas.', 'pregunta'),
    ('A2', '¿De dónde viene el ingreso de esta actividad?', 'pregunta');

-- A2 options
INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('a2000000-0000-0000-0000-000000000001', 'A2', 'Vendo productos o mercancía', 1),
    ('a2000000-0000-0000-0000-000000000002', 'A2', 'Presto un servicio profesional o técnico', 2),
    ('a2000000-0000-0000-0000-000000000003', 'A2', 'Rento un inmueble o un bien', 3),
    ('a2000000-0000-0000-0000-000000000004', 'A2', 'Mi cliente o proveedor está en el extranjero', 4),
    ('a2000000-0000-0000-0000-000000000005', 'A2', 'Otros ingresos', 5),
    ('a2000000-0000-0000-0000-000000000006', 'A2', 'No estoy seguro', 6);

-- Venta branch
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('V0', '¿El producto que vendes está terminado para el consumidor final?', 'pregunta'),
    ('V1', '¿Qué tipo de producto vendes?', 'pregunta'),
    ('V2', '¿Tu producto se exporta o se vende en territorio nacional?', 'pregunta'),
    ('V-ALI', '¿Tu producto es alguno de estos: alimentos no preparados, bebidas no alcohólicas, agua, hielo, o medicinas?', 'pregunta'),
    ('V-AGRO', '¿Tu producto es agropecuario no industrializado (frutas, verduras, granos en estado natural)?', 'pregunta'),
    ('V-AGRO-EQ', '¿Tu producto es maquinaria o equipo para uso exclusivamente agropecuario?', 'pregunta'),
    ('V-LIB', '¿Vendes libros, periódicos o revistas?', 'pregunta'),
    ('V-INM', '¿El bien que vendes es un inmueble (terreno, casa, local)?', 'pregunta'),
    ('V-USADO', '¿El bien es usado y lo vendes como particular, no como negocio habitual?', 'pregunta'),
    ('V-FIN', '¿Tu operación incluye intereses o financiamiento?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'V0', 'Sí, es un producto terminado', 1),
    ('b0000000-0000-0000-0000-000000000002', 'V0', 'No, es materia prima o insumo', 2),
    ('b1000000-0000-0000-0000-000000000001', 'V1', 'Alimentos o bebidas', 1),
    ('b1000000-0000-0000-0000-000000000002', 'V1', 'Productos agropecuarios', 2),
    ('b1000000-0000-0000-0000-000000000003', 'V1', 'Libros o publicaciones', 3),
    ('b1000000-0000-0000-0000-000000000004', 'V1', 'Inmuebles', 4),
    ('b1000000-0000-0000-0000-000000000005', 'V1', 'Otro tipo de producto', 5),
    ('b2000000-0000-0000-0000-000000000001', 'V2', 'Se vende en México', 1),
    ('b2000000-0000-0000-0000-000000000002', 'V2', 'Se exporta al extranjero', 2),
    ('ba010000-0000-0000-0000-000000000001', 'V-ALI', 'Sí', 1),
    ('ba010000-0000-0000-0000-000000000002', 'V-ALI', 'No', 2),
    ('ba020000-0000-0000-0000-000000000001', 'V-AGRO', 'Sí', 1),
    ('ba020000-0000-0000-0000-000000000002', 'V-AGRO', 'No', 2),
    ('ba030000-0000-0000-0000-000000000001', 'V-AGRO-EQ', 'Sí', 1),
    ('ba030000-0000-0000-0000-000000000002', 'V-AGRO-EQ', 'No', 2),
    ('ba040000-0000-0000-0000-000000000001', 'V-LIB', 'Sí', 1),
    ('ba040000-0000-0000-0000-000000000002', 'V-LIB', 'No', 2),
    ('ba050000-0000-0000-0000-000000000001', 'V-INM', 'Sí, es terreno destinado a construcción de vivienda', 1),
    ('ba050000-0000-0000-0000-000000000002', 'V-INM', 'Sí, es casa habitación', 2),
    ('ba050000-0000-0000-0000-000000000003', 'V-INM', 'Sí, otro tipo de inmueble', 3),
    ('ba050000-0000-0000-0000-000000000004', 'V-INM', 'No', 4),
    ('ba060000-0000-0000-0000-000000000001', 'V-USADO', 'Sí', 1),
    ('ba060000-0000-0000-0000-000000000002', 'V-USADO', 'No', 2),
    ('ba070000-0000-0000-0000-000000000001', 'V-FIN', 'Sí', 1),
    ('ba070000-0000-0000-0000-000000000002', 'V-FIN', 'No', 2);

-- Servicios branch
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('S0', '¿Qué tipo de servicio prestas?', 'pregunta'),
    ('S1', '¿Tu servicio se presta en territorio nacional o en el extranjero?', 'pregunta'),
    ('S-AGRO', '¿Tu servicio está directamente relacionado con la actividad agropecuaria (siembra, cosecha, recolección)?', 'pregunta'),
    ('S-EDU', '¿Tu servicio es educativo con reconocimiento oficial de validez (RVOE)?', 'pregunta'),
    ('S-TRANS', '¿Prestas servicio de transporte público terrestre de personas?', 'pregunta'),
    ('S-FIN', '¿Tu servicio involucra intermediación financiera, seguros o fianzas?', 'pregunta'),
    ('S-MED', '¿Prestas servicios médicos, dentales u hospitalarios?', 'pregunta'),
    ('S-CASA', '¿Tu servicio es de construcción de vivienda de interés social?', 'pregunta'),
    ('S-AUTOR', '¿Tu ingreso es por regalías o derechos de autor?', 'pregunta'),
    ('S-EXT', '¿Tu servicio se presta a un cliente en el extranjero?', 'pregunta'),
    ('S-EXT-TIPO', '¿Qué tipo de servicio prestas al extranjero?', 'pregunta'),
    ('S-EXT-REQ', '¿El servicio se aprovecha íntegramente en el extranjero y el pago se recibe en México?', 'pregunta'),
    ('S-EXT-TI', '¿Es un servicio de tecnología de la información (desarrollo de software, hosting, etc.)?', 'pregunta'),
    ('S-EXT-PF', '¿Prestas el servicio como persona física sin establecimiento permanente en el extranjero?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('50000000-0000-0000-0000-000000000001', 'S0', 'Servicio profesional independiente', 1),
    ('50000000-0000-0000-0000-000000000002', 'S0', 'Servicio agropecuario', 2),
    ('50000000-0000-0000-0000-000000000003', 'S0', 'Servicio educativo', 3),
    ('50000000-0000-0000-0000-000000000004', 'S0', 'Transporte', 4),
    ('50000000-0000-0000-0000-000000000005', 'S0', 'Servicios financieros', 5),
    ('50000000-0000-0000-0000-000000000006', 'S0', 'Servicios médicos', 6),
    ('50000000-0000-0000-0000-000000000007', 'S0', 'Construcción de vivienda', 7),
    ('50000000-0000-0000-0000-000000000008', 'S0', 'Regalías o derechos de autor', 8),
    ('50000000-0000-0000-0000-000000000009', 'S0', 'Otro servicio', 9),
    ('51000000-0000-0000-0000-000000000001', 'S1', 'En México', 1),
    ('51000000-0000-0000-0000-000000000002', 'S1', 'En el extranjero', 2),
    ('5a010000-0000-0000-0000-000000000001', 'S-AGRO', 'Sí', 1),
    ('5a010000-0000-0000-0000-000000000002', 'S-AGRO', 'No', 2),
    ('5a020000-0000-0000-0000-000000000001', 'S-EDU', 'Sí, tiene RVOE', 1),
    ('5a020000-0000-0000-0000-000000000002', 'S-EDU', 'No tiene RVOE', 2),
    ('5a030000-0000-0000-0000-000000000001', 'S-TRANS', 'Sí', 1),
    ('5a030000-0000-0000-0000-000000000002', 'S-TRANS', 'No', 2),
    ('5a040000-0000-0000-0000-000000000001', 'S-FIN', 'Sí', 1),
    ('5a040000-0000-0000-0000-000000000002', 'S-FIN', 'No', 2),
    ('5a050000-0000-0000-0000-000000000001', 'S-MED', 'Sí', 1),
    ('5a050000-0000-0000-0000-000000000002', 'S-MED', 'No', 2),
    ('5a060000-0000-0000-0000-000000000001', 'S-CASA', 'Sí', 1),
    ('5a060000-0000-0000-0000-000000000002', 'S-CASA', 'No', 2),
    ('5a070000-0000-0000-0000-000000000001', 'S-AUTOR', 'Sí', 1),
    ('5a070000-0000-0000-0000-000000000002', 'S-AUTOR', 'No', 2),
    ('5a080000-0000-0000-0000-000000000001', 'S-EXT', 'Sí', 1),
    ('5a080000-0000-0000-0000-000000000002', 'S-EXT', 'No', 2),
    ('5a090000-0000-0000-0000-000000000001', 'S-EXT-TIPO', 'Servicio técnico o profesional', 1),
    ('5a090000-0000-0000-0000-000000000002', 'S-EXT-TIPO', 'Servicio de TI', 2),
    ('5a090000-0000-0000-0000-000000000003', 'S-EXT-TIPO', 'Otro servicio', 3),
    ('5a0a0000-0000-0000-0000-000000000001', 'S-EXT-REQ', 'Sí', 1),
    ('5a0a0000-0000-0000-0000-000000000002', 'S-EXT-REQ', 'No', 2),
    ('5a0b0000-0000-0000-0000-000000000001', 'S-EXT-TI', 'Sí', 1),
    ('5a0b0000-0000-0000-0000-000000000002', 'S-EXT-TI', 'No', 2),
    ('5a0c0000-0000-0000-0000-000000000001', 'S-EXT-PF', 'Sí', 1),
    ('5a0c0000-0000-0000-0000-000000000002', 'S-EXT-PF', 'No', 2);

-- Renta branch
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('R0', '¿Qué tipo de bien rentas?', 'pregunta'),
    ('R1', '¿El inmueble está destinado a casa habitación?', 'pregunta'),
    ('R-EXT', '¿Rentas el bien a un arrendatario en el extranjero?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('40000000-0000-0000-0000-000000000001', 'R0', 'Inmueble (casa, departamento, local, oficina)', 1),
    ('40000000-0000-0000-0000-000000000002', 'R0', 'Bien mueble (maquinaria, equipo, vehículo)', 2),
    ('41000000-0000-0000-0000-000000000001', 'R1', 'Sí, es casa habitación', 1),
    ('41000000-0000-0000-0000-000000000002', 'R1', 'No, es uso comercial o industrial', 2),
    ('4a010000-0000-0000-0000-000000000001', 'R-EXT', 'Sí', 1),
    ('4a010000-0000-0000-0000-000000000002', 'R-EXT', 'No', 2);

-- Importación branch
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('I0', '¿Qué importas?', 'pregunta'),
    ('I-BIEN', '¿El bien importado es tangible o intangible?', 'pregunta'),
    ('I-SERV', '¿El servicio importado se aprovecha en territorio nacional?', 'pregunta'),
    ('I-RENTA', '¿Rentas un bien del extranjero para usarlo en México?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('10000000-0000-0000-0000-000000000001', 'I0', 'Bienes (productos, mercancía)', 1),
    ('10000000-0000-0000-0000-000000000002', 'I0', 'Servicios', 2),
    ('10000000-0000-0000-0000-000000000003', 'I0', 'Renta de bienes del extranjero', 3),
    ('1a010000-0000-0000-0000-000000000001', 'I-BIEN', 'Tangible', 1),
    ('1a010000-0000-0000-0000-000000000002', 'I-BIEN', 'Intangible (software, licencias)', 2),
    ('1a020000-0000-0000-0000-000000000001', 'I-SERV', 'Sí', 1),
    ('1a020000-0000-0000-0000-000000000002', 'I-SERV', 'No', 2),
    ('1a030000-0000-0000-0000-000000000001', 'I-RENTA', 'Sí', 1),
    ('1a030000-0000-0000-0000-000000000002', 'I-RENTA', 'No', 2);

-- Otros ingresos
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('O0', '¿Puedes describir la naturaleza de este ingreso? (intereses, premios, etc.)', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('0a000000-0000-0000-0000-000000000001', 'O0', 'Intereses bancarios', 1),
    ('0a000000-0000-0000-0000-000000000002', 'O0', 'Premios o sorteos', 2),
    ('0a000000-0000-0000-0000-000000000003', 'O0', 'Otro tipo de ingreso', 3);

-- Cierre
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('C1', 'Resultado preliminar de la clasificación de IVA para esta actividad.', 'resultado'),
    ('C2', '¿Tienes otra actividad por la que emitas facturas?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('c2000000-0000-0000-0000-000000000001', 'C2', 'Sí, tengo otra actividad', 1),
    ('c2000000-0000-0000-0000-000000000002', 'C2', 'No, es la única', 2);

-- ============================================================
-- TRANSITIONS (key paths through the questionnaire)
-- ============================================================

-- A2 → branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('A2', 'a2000000-0000-0000-0000-000000000001', 'V0'),
    ('A2', 'a2000000-0000-0000-0000-000000000002', 'S0'),
    ('A2', 'a2000000-0000-0000-0000-000000000003', 'R0'),
    ('A2', 'a2000000-0000-0000-0000-000000000004', 'I0'),
    ('A2', 'a2000000-0000-0000-0000-000000000005', 'O0');

-- V0 → V1 or V2
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V0', 'b0000000-0000-0000-0000-000000000001', 'V1'),
    ('V0', 'b0000000-0000-0000-0000-000000000002', 'V1');

-- V1 → specific product branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V1', 'b1000000-0000-0000-0000-000000000001', 'V-ALI'),
    ('V1', 'b1000000-0000-0000-0000-000000000002', 'V-AGRO'),
    ('V1', 'b1000000-0000-0000-0000-000000000003', 'V-LIB'),
    ('V1', 'b1000000-0000-0000-0000-000000000004', 'V-INM'),
    ('V1', 'b1000000-0000-0000-0000-000000000005', 'V2');

-- V2 → C1 with export check
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V2', 'b2000000-0000-0000-0000-000000000001', 'C1'),
    ('V2', 'b2000000-0000-0000-0000-000000000002', 'C1');

-- Product leaf nodes → C1
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V-ALI', 'ba010000-0000-0000-0000-000000000001', 'C1'),
    ('V-ALI', 'ba010000-0000-0000-0000-000000000002', 'V2'),
    ('V-AGRO', 'ba020000-0000-0000-0000-000000000001', 'C1'),
    ('V-AGRO', 'ba020000-0000-0000-0000-000000000002', 'V-AGRO-EQ'),
    ('V-AGRO-EQ', 'ba030000-0000-0000-0000-000000000001', 'C1'),
    ('V-AGRO-EQ', 'ba030000-0000-0000-0000-000000000002', 'V2'),
    ('V-LIB', 'ba040000-0000-0000-0000-000000000001', 'C1'),
    ('V-LIB', 'ba040000-0000-0000-0000-000000000002', 'V2'),
    ('V-INM', 'ba050000-0000-0000-0000-000000000001', 'C1'),
    ('V-INM', 'ba050000-0000-0000-0000-000000000002', 'C1'),
    ('V-INM', 'ba050000-0000-0000-0000-000000000003', 'C1'),
    ('V-INM', 'ba050000-0000-0000-0000-000000000004', 'V2');

-- S0 → specific service branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('S0', '50000000-0000-0000-0000-000000000001', 'S1'),
    ('S0', '50000000-0000-0000-0000-000000000002', 'S-AGRO'),
    ('S0', '50000000-0000-0000-0000-000000000003', 'S-EDU'),
    ('S0', '50000000-0000-0000-0000-000000000004', 'S-TRANS'),
    ('S0', '50000000-0000-0000-0000-000000000005', 'S-FIN'),
    ('S0', '50000000-0000-0000-0000-000000000006', 'S-MED'),
    ('S0', '50000000-0000-0000-0000-000000000007', 'S-CASA'),
    ('S0', '50000000-0000-0000-0000-000000000008', 'S-AUTOR'),
    ('S0', '50000000-0000-0000-0000-000000000009', 'S1');

-- S1 → C1 or S-EXT
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('S1', '51000000-0000-0000-0000-000000000001', 'C1'),
    ('S1', '51000000-0000-0000-0000-000000000002', 'S-EXT');

-- Service leaf nodes → C1
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('S-AGRO', '5a010000-0000-0000-0000-000000000001', 'C1'),
    ('S-AGRO', '5a010000-0000-0000-0000-000000000002', 'S1'),
    ('S-EDU', '5a020000-0000-0000-0000-000000000001', 'C1'),
    ('S-EDU', '5a020000-0000-0000-0000-000000000002', 'C1'),
    ('S-TRANS', '5a030000-0000-0000-0000-000000000001', 'C1'),
    ('S-TRANS', '5a030000-0000-0000-0000-000000000002', 'S1'),
    ('S-FIN', '5a040000-0000-0000-0000-000000000001', 'C1'),
    ('S-FIN', '5a040000-0000-0000-0000-000000000002', 'S1'),
    ('S-MED', '5a050000-0000-0000-0000-000000000001', 'C1'),
    ('S-MED', '5a050000-0000-0000-0000-000000000002', 'S1'),
    ('S-CASA', '5a060000-0000-0000-0000-000000000001', 'C1'),
    ('S-CASA', '5a060000-0000-0000-0000-000000000002', 'S1'),
    ('S-AUTOR', '5a070000-0000-0000-0000-000000000001', 'C1'),
    ('S-AUTOR', '5a070000-0000-0000-0000-000000000002', 'S1'),
    ('S-EXT', '5a080000-0000-0000-0000-000000000001', 'S-EXT-REQ'),
    ('S-EXT', '5a080000-0000-0000-0000-000000000002', 'C1'),
    ('S-EXT-REQ', '5a0a0000-0000-0000-0000-000000000001', 'S-EXT-TIPO'),
    ('S-EXT-REQ', '5a0a0000-0000-0000-0000-000000000002', 'C1'),
    ('S-EXT-TIPO', '5a090000-0000-0000-0000-000000000001', 'C1'),
    ('S-EXT-TIPO', '5a090000-0000-0000-0000-000000000002', 'S-EXT-TI'),
    ('S-EXT-TIPO', '5a090000-0000-0000-0000-000000000003', 'C1'),
    ('S-EXT-TI', '5a0b0000-0000-0000-0000-000000000001', 'C1'),
    ('S-EXT-TI', '5a0b0000-0000-0000-0000-000000000002', 'C1');

-- R0 → R1 or R-EXT
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('R0', '40000000-0000-0000-0000-000000000001', 'R1'),
    ('R0', '40000000-0000-0000-0000-000000000002', 'C1');

INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('R1', '41000000-0000-0000-0000-000000000001', 'C1'),
    ('R1', '41000000-0000-0000-0000-000000000002', 'C1');

-- I0 → sub-branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('I0', '10000000-0000-0000-0000-000000000001', 'I-BIEN'),
    ('I0', '10000000-0000-0000-0000-000000000002', 'I-SERV'),
    ('I0', '10000000-0000-0000-0000-000000000003', 'I-RENTA');

INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('I-BIEN', '1a010000-0000-0000-0000-000000000001', 'C1'),
    ('I-BIEN', '1a010000-0000-0000-0000-000000000002', 'C1'),
    ('I-SERV', '1a020000-0000-0000-0000-000000000001', 'C1'),
    ('I-SERV', '1a020000-0000-0000-0000-000000000002', 'C1'),
    ('I-RENTA', '1a030000-0000-0000-0000-000000000001', 'C1'),
    ('I-RENTA', '1a030000-0000-0000-0000-000000000002', 'C1');

-- O0 → C1
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('O0', '0a000000-0000-0000-0000-000000000001', 'C1'),
    ('O0', '0a000000-0000-0000-0000-000000000002', 'C1'),
    ('O0', '0a000000-0000-0000-0000-000000000003', 'C1');

-- C2 → loop or done
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('C2', 'c2000000-0000-0000-0000-000000000001', 'A1'),
    ('C2', 'c2000000-0000-0000-0000-000000000002', 'C1');

