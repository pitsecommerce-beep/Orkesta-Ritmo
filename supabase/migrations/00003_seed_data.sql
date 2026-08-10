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
    ('v0000000-0000-0000-0000-000000000001', 'V0', 'Sí, es un producto terminado', 1),
    ('v0000000-0000-0000-0000-000000000002', 'V0', 'No, es materia prima o insumo', 2),
    ('v1000000-0000-0000-0000-000000000001', 'V1', 'Alimentos o bebidas', 1),
    ('v1000000-0000-0000-0000-000000000002', 'V1', 'Productos agropecuarios', 2),
    ('v1000000-0000-0000-0000-000000000003', 'V1', 'Libros o publicaciones', 3),
    ('v1000000-0000-0000-0000-000000000004', 'V1', 'Inmuebles', 4),
    ('v1000000-0000-0000-0000-000000000005', 'V1', 'Otro tipo de producto', 5),
    ('v2000000-0000-0000-0000-000000000001', 'V2', 'Se vende en México', 1),
    ('v2000000-0000-0000-0000-000000000002', 'V2', 'Se exporta al extranjero', 2),
    ('vali0000-0000-0000-0000-000000000001', 'V-ALI', 'Sí', 1),
    ('vali0000-0000-0000-0000-000000000002', 'V-ALI', 'No', 2),
    ('vagr0000-0000-0000-0000-000000000001', 'V-AGRO', 'Sí', 1),
    ('vagr0000-0000-0000-0000-000000000002', 'V-AGRO', 'No', 2),
    ('vaeq0000-0000-0000-0000-000000000001', 'V-AGRO-EQ', 'Sí', 1),
    ('vaeq0000-0000-0000-0000-000000000002', 'V-AGRO-EQ', 'No', 2),
    ('vlib0000-0000-0000-0000-000000000001', 'V-LIB', 'Sí', 1),
    ('vlib0000-0000-0000-0000-000000000002', 'V-LIB', 'No', 2),
    ('vinm0000-0000-0000-0000-000000000001', 'V-INM', 'Sí, es terreno destinado a construcción de vivienda', 1),
    ('vinm0000-0000-0000-0000-000000000002', 'V-INM', 'Sí, es casa habitación', 2),
    ('vinm0000-0000-0000-0000-000000000003', 'V-INM', 'Sí, otro tipo de inmueble', 3),
    ('vinm0000-0000-0000-0000-000000000004', 'V-INM', 'No', 4),
    ('vuso0000-0000-0000-0000-000000000001', 'V-USADO', 'Sí', 1),
    ('vuso0000-0000-0000-0000-000000000002', 'V-USADO', 'No', 2),
    ('vfin0000-0000-0000-0000-000000000001', 'V-FIN', 'Sí', 1),
    ('vfin0000-0000-0000-0000-000000000002', 'V-FIN', 'No', 2);

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
    ('s0000000-0000-0000-0000-000000000001', 'S0', 'Servicio profesional independiente', 1),
    ('s0000000-0000-0000-0000-000000000002', 'S0', 'Servicio agropecuario', 2),
    ('s0000000-0000-0000-0000-000000000003', 'S0', 'Servicio educativo', 3),
    ('s0000000-0000-0000-0000-000000000004', 'S0', 'Transporte', 4),
    ('s0000000-0000-0000-0000-000000000005', 'S0', 'Servicios financieros', 5),
    ('s0000000-0000-0000-0000-000000000006', 'S0', 'Servicios médicos', 6),
    ('s0000000-0000-0000-0000-000000000007', 'S0', 'Construcción de vivienda', 7),
    ('s0000000-0000-0000-0000-000000000008', 'S0', 'Regalías o derechos de autor', 8),
    ('s0000000-0000-0000-0000-000000000009', 'S0', 'Otro servicio', 9),
    ('s1000000-0000-0000-0000-000000000001', 'S1', 'En México', 1),
    ('s1000000-0000-0000-0000-000000000002', 'S1', 'En el extranjero', 2),
    ('sagr0000-0000-0000-0000-000000000001', 'S-AGRO', 'Sí', 1),
    ('sagr0000-0000-0000-0000-000000000002', 'S-AGRO', 'No', 2),
    ('sedu0000-0000-0000-0000-000000000001', 'S-EDU', 'Sí, tiene RVOE', 1),
    ('sedu0000-0000-0000-0000-000000000002', 'S-EDU', 'No tiene RVOE', 2),
    ('stra0000-0000-0000-0000-000000000001', 'S-TRANS', 'Sí', 1),
    ('stra0000-0000-0000-0000-000000000002', 'S-TRANS', 'No', 2),
    ('sfin0000-0000-0000-0000-000000000001', 'S-FIN', 'Sí', 1),
    ('sfin0000-0000-0000-0000-000000000002', 'S-FIN', 'No', 2),
    ('smed0000-0000-0000-0000-000000000001', 'S-MED', 'Sí', 1),
    ('smed0000-0000-0000-0000-000000000002', 'S-MED', 'No', 2),
    ('scas0000-0000-0000-0000-000000000001', 'S-CASA', 'Sí', 1),
    ('scas0000-0000-0000-0000-000000000002', 'S-CASA', 'No', 2),
    ('saut0000-0000-0000-0000-000000000001', 'S-AUTOR', 'Sí', 1),
    ('saut0000-0000-0000-0000-000000000002', 'S-AUTOR', 'No', 2),
    ('sext0000-0000-0000-0000-000000000001', 'S-EXT', 'Sí', 1),
    ('sext0000-0000-0000-0000-000000000002', 'S-EXT', 'No', 2),
    ('sextt000-0000-0000-0000-000000000001', 'S-EXT-TIPO', 'Servicio técnico o profesional', 1),
    ('sextt000-0000-0000-0000-000000000002', 'S-EXT-TIPO', 'Servicio de TI', 2),
    ('sextt000-0000-0000-0000-000000000003', 'S-EXT-TIPO', 'Otro servicio', 3),
    ('sextr000-0000-0000-0000-000000000001', 'S-EXT-REQ', 'Sí', 1),
    ('sextr000-0000-0000-0000-000000000002', 'S-EXT-REQ', 'No', 2),
    ('sexti000-0000-0000-0000-000000000001', 'S-EXT-TI', 'Sí', 1),
    ('sexti000-0000-0000-0000-000000000002', 'S-EXT-TI', 'No', 2),
    ('sextf000-0000-0000-0000-000000000001', 'S-EXT-PF', 'Sí', 1),
    ('sextf000-0000-0000-0000-000000000002', 'S-EXT-PF', 'No', 2);

-- Renta branch
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('R0', '¿Qué tipo de bien rentas?', 'pregunta'),
    ('R1', '¿El inmueble está destinado a casa habitación?', 'pregunta'),
    ('R-EXT', '¿Rentas el bien a un arrendatario en el extranjero?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('r0000000-0000-0000-0000-000000000001', 'R0', 'Inmueble (casa, departamento, local, oficina)', 1),
    ('r0000000-0000-0000-0000-000000000002', 'R0', 'Bien mueble (maquinaria, equipo, vehículo)', 2),
    ('r1000000-0000-0000-0000-000000000001', 'R1', 'Sí, es casa habitación', 1),
    ('r1000000-0000-0000-0000-000000000002', 'R1', 'No, es uso comercial o industrial', 2),
    ('rext0000-0000-0000-0000-000000000001', 'R-EXT', 'Sí', 1),
    ('rext0000-0000-0000-0000-000000000002', 'R-EXT', 'No', 2);

-- Importación branch
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('I0', '¿Qué importas?', 'pregunta'),
    ('I-BIEN', '¿El bien importado es tangible o intangible?', 'pregunta'),
    ('I-SERV', '¿El servicio importado se aprovecha en territorio nacional?', 'pregunta'),
    ('I-RENTA', '¿Rentas un bien del extranjero para usarlo en México?', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('i0000000-0000-0000-0000-000000000001', 'I0', 'Bienes (productos, mercancía)', 1),
    ('i0000000-0000-0000-0000-000000000002', 'I0', 'Servicios', 2),
    ('i0000000-0000-0000-0000-000000000003', 'I0', 'Renta de bienes del extranjero', 3),
    ('ibien000-0000-0000-0000-000000000001', 'I-BIEN', 'Tangible', 1),
    ('ibien000-0000-0000-0000-000000000002', 'I-BIEN', 'Intangible (software, licencias)', 2),
    ('iserv000-0000-0000-0000-000000000001', 'I-SERV', 'Sí', 1),
    ('iserv000-0000-0000-0000-000000000002', 'I-SERV', 'No', 2),
    ('irent000-0000-0000-0000-000000000001', 'I-RENTA', 'Sí', 1),
    ('irent000-0000-0000-0000-000000000002', 'I-RENTA', 'No', 2);

-- Otros ingresos
INSERT INTO cuestionario_nodos (id, texto, tipo) VALUES
    ('O0', '¿Puedes describir la naturaleza de este ingreso? (intereses, premios, etc.)', 'pregunta');

INSERT INTO cuestionario_opciones (id, nodo_id, texto, orden) VALUES
    ('o0000000-0000-0000-0000-000000000001', 'O0', 'Intereses bancarios', 1),
    ('o0000000-0000-0000-0000-000000000002', 'O0', 'Premios o sorteos', 2),
    ('o0000000-0000-0000-0000-000000000003', 'O0', 'Otro tipo de ingreso', 3);

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
    ('V0', 'v0000000-0000-0000-0000-000000000001', 'V1'),
    ('V0', 'v0000000-0000-0000-0000-000000000002', 'V1');

-- V1 → specific product branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V1', 'v1000000-0000-0000-0000-000000000001', 'V-ALI'),
    ('V1', 'v1000000-0000-0000-0000-000000000002', 'V-AGRO'),
    ('V1', 'v1000000-0000-0000-0000-000000000003', 'V-LIB'),
    ('V1', 'v1000000-0000-0000-0000-000000000004', 'V-INM'),
    ('V1', 'v1000000-0000-0000-0000-000000000005', 'V2');

-- V2 → C1 with export check
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V2', 'v2000000-0000-0000-0000-000000000001', 'C1'),
    ('V2', 'v2000000-0000-0000-0000-000000000002', 'C1');

-- Product leaf nodes → C1
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('V-ALI', 'vali0000-0000-0000-0000-000000000001', 'C1'),
    ('V-ALI', 'vali0000-0000-0000-0000-000000000002', 'V2'),
    ('V-AGRO', 'vagr0000-0000-0000-0000-000000000001', 'C1'),
    ('V-AGRO', 'vagr0000-0000-0000-0000-000000000002', 'V-AGRO-EQ'),
    ('V-AGRO-EQ', 'vaeq0000-0000-0000-0000-000000000001', 'C1'),
    ('V-AGRO-EQ', 'vaeq0000-0000-0000-0000-000000000002', 'V2'),
    ('V-LIB', 'vlib0000-0000-0000-0000-000000000001', 'C1'),
    ('V-LIB', 'vlib0000-0000-0000-0000-000000000002', 'V2'),
    ('V-INM', 'vinm0000-0000-0000-0000-000000000001', 'C1'),
    ('V-INM', 'vinm0000-0000-0000-0000-000000000002', 'C1'),
    ('V-INM', 'vinm0000-0000-0000-0000-000000000003', 'C1'),
    ('V-INM', 'vinm0000-0000-0000-0000-000000000004', 'V2');

-- S0 → specific service branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('S0', 's0000000-0000-0000-0000-000000000001', 'S1'),
    ('S0', 's0000000-0000-0000-0000-000000000002', 'S-AGRO'),
    ('S0', 's0000000-0000-0000-0000-000000000003', 'S-EDU'),
    ('S0', 's0000000-0000-0000-0000-000000000004', 'S-TRANS'),
    ('S0', 's0000000-0000-0000-0000-000000000005', 'S-FIN'),
    ('S0', 's0000000-0000-0000-0000-000000000006', 'S-MED'),
    ('S0', 's0000000-0000-0000-0000-000000000007', 'S-CASA'),
    ('S0', 's0000000-0000-0000-0000-000000000008', 'S-AUTOR'),
    ('S0', 's0000000-0000-0000-0000-000000000009', 'S1');

-- S1 → C1 or S-EXT
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('S1', 's1000000-0000-0000-0000-000000000001', 'C1'),
    ('S1', 's1000000-0000-0000-0000-000000000002', 'S-EXT');

-- Service leaf nodes → C1
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('S-AGRO', 'sagr0000-0000-0000-0000-000000000001', 'C1'),
    ('S-AGRO', 'sagr0000-0000-0000-0000-000000000002', 'S1'),
    ('S-EDU', 'sedu0000-0000-0000-0000-000000000001', 'C1'),
    ('S-EDU', 'sedu0000-0000-0000-0000-000000000002', 'C1'),
    ('S-TRANS', 'stra0000-0000-0000-0000-000000000001', 'C1'),
    ('S-TRANS', 'stra0000-0000-0000-0000-000000000002', 'S1'),
    ('S-FIN', 'sfin0000-0000-0000-0000-000000000001', 'C1'),
    ('S-FIN', 'sfin0000-0000-0000-0000-000000000002', 'S1'),
    ('S-MED', 'smed0000-0000-0000-0000-000000000001', 'C1'),
    ('S-MED', 'smed0000-0000-0000-0000-000000000002', 'S1'),
    ('S-CASA', 'scas0000-0000-0000-0000-000000000001', 'C1'),
    ('S-CASA', 'scas0000-0000-0000-0000-000000000002', 'S1'),
    ('S-AUTOR', 'saut0000-0000-0000-0000-000000000001', 'C1'),
    ('S-AUTOR', 'saut0000-0000-0000-0000-000000000002', 'S1'),
    ('S-EXT', 'sext0000-0000-0000-0000-000000000001', 'S-EXT-REQ'),
    ('S-EXT', 'sext0000-0000-0000-0000-000000000002', 'C1'),
    ('S-EXT-REQ', 'sextr000-0000-0000-0000-000000000001', 'S-EXT-TIPO'),
    ('S-EXT-REQ', 'sextr000-0000-0000-0000-000000000002', 'C1'),
    ('S-EXT-TIPO', 'sextt000-0000-0000-0000-000000000001', 'C1'),
    ('S-EXT-TIPO', 'sextt000-0000-0000-0000-000000000002', 'S-EXT-TI'),
    ('S-EXT-TIPO', 'sextt000-0000-0000-0000-000000000003', 'C1'),
    ('S-EXT-TI', 'sexti000-0000-0000-0000-000000000001', 'C1'),
    ('S-EXT-TI', 'sexti000-0000-0000-0000-000000000002', 'C1');

-- R0 → R1 or R-EXT
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('R0', 'r0000000-0000-0000-0000-000000000001', 'R1'),
    ('R0', 'r0000000-0000-0000-0000-000000000002', 'C1');

INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('R1', 'r1000000-0000-0000-0000-000000000001', 'C1'),
    ('R1', 'r1000000-0000-0000-0000-000000000002', 'C1');

-- I0 → sub-branches
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('I0', 'i0000000-0000-0000-0000-000000000001', 'I-BIEN'),
    ('I0', 'i0000000-0000-0000-0000-000000000002', 'I-SERV'),
    ('I0', 'i0000000-0000-0000-0000-000000000003', 'I-RENTA');

INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('I-BIEN', 'ibien000-0000-0000-0000-000000000001', 'C1'),
    ('I-BIEN', 'ibien000-0000-0000-0000-000000000002', 'C1'),
    ('I-SERV', 'iserv000-0000-0000-0000-000000000001', 'C1'),
    ('I-SERV', 'iserv000-0000-0000-0000-000000000002', 'C1'),
    ('I-RENTA', 'irent000-0000-0000-0000-000000000001', 'C1'),
    ('I-RENTA', 'irent000-0000-0000-0000-000000000002', 'C1');

-- O0 → C1
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('O0', 'o0000000-0000-0000-0000-000000000001', 'C1'),
    ('O0', 'o0000000-0000-0000-0000-000000000002', 'C1'),
    ('O0', 'o0000000-0000-0000-0000-000000000003', 'C1');

-- C2 → loop or done
INSERT INTO cuestionario_transiciones (nodo_origen, opcion_id, nodo_destino) VALUES
    ('C2', 'c2000000-0000-0000-0000-000000000001', 'A1'),
    ('C2', 'c2000000-0000-0000-0000-000000000002', 'C1');

-- ============================================================
-- DEMO SEED: RESICO PF contributor
-- ============================================================

INSERT INTO tenants (id, rfc, nombre, tipo_persona, regimen, tipo_deduccion, presenta_anual, onboarding_completado) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'XAXX010101001', 'María García López (Demo RESICO)', 'fisica', 'RESICO_PF', 'ciega', false, true);

INSERT INTO tenants (id, rfc, nombre, tipo_persona, regimen, tipo_deduccion, presenta_anual, onboarding_completado) VALUES
    ('d0000000-0000-0000-0000-000000000002', 'XAXX010101002', 'José Hernández Ruiz (Demo Arrendamiento)', 'fisica', 'ARRENDAMIENTO', 'ciega', false, true);

-- Demo periods for RESICO PF - 2025
INSERT INTO periodos (tenant_id, impuesto, tipo_periodo, ejercicio, numero_periodo, fecha_limite, estado) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'ISR', 'mensual', 2025, 1, '2025-02-17', 'presentado'),
    ('d0000000-0000-0000-0000-000000000001', 'IVA', 'mensual', 2025, 1, '2025-02-17', 'presentado'),
    ('d0000000-0000-0000-0000-000000000001', 'ISR', 'mensual', 2025, 2, '2025-03-17', 'presentado'),
    ('d0000000-0000-0000-0000-000000000001', 'IVA', 'mensual', 2025, 2, '2025-03-17', 'presentado'),
    ('d0000000-0000-0000-0000-000000000001', 'ISR', 'mensual', 2025, 3, '2025-04-17', 'calculado'),
    ('d0000000-0000-0000-0000-000000000001', 'IVA', 'mensual', 2025, 3, '2025-04-17', 'calculado');

-- Demo periods for Arrendamiento - 2025
INSERT INTO periodos (tenant_id, impuesto, tipo_periodo, ejercicio, numero_periodo, fecha_limite, estado) VALUES
    ('d0000000-0000-0000-0000-000000000002', 'ISR', 'mensual', 2025, 1, '2025-02-17', 'presentado'),
    ('d0000000-0000-0000-0000-000000000002', 'IVA', 'mensual', 2025, 1, '2025-02-17', 'presentado'),
    ('d0000000-0000-0000-0000-000000000002', 'ISR', 'mensual', 2025, 2, '2025-03-17', 'borrador'),
    ('d0000000-0000-0000-0000-000000000002', 'IVA', 'mensual', 2025, 2, '2025-03-17', 'borrador');

-- Demo activity for RESICO PF
INSERT INTO actividades (id, tenant_id, descripcion, resultado, cuestionario_completado) VALUES
    ('act00000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 'Venta de productos electrónicos', 'IVA16', true);

-- Demo activity for Arrendamiento
INSERT INTO actividades (id, tenant_id, descripcion, resultado, cuestionario_completado) VALUES
    ('act00000-0000-0000-0000-000000000002', 'd0000000-0000-0000-0000-000000000002', 'Renta de local comercial', 'IVA16', true);
