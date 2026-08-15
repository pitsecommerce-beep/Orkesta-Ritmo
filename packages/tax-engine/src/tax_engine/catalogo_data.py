"""
Datos iniciales del catalogo normativo versionado.

Carga tarifas, UMA, e indicadores verificados para 2025 y 2026.
Los valores del Anexo 8 de la RMF 2026 se calcularon aplicando el factor de
actualizacion 1.1321 (publicado DOF 28/12/2025) a los valores base de 2025.
Deben verificarse contra el PDF original del Anexo 8 cuando el acceso a
sat.gob.mx este disponible.

Valores UMA verificados contra DOF 9/01/2026:
  - $113.14 diario vigente hasta 31/01/2026
  - $117.31 diario vigente del 01/02/2026 al 31/01/2027

Reglas marcadas PENDIENTE_CONTADOR: ver notas en cada regla.
"""

import datetime
from decimal import Decimal, ROUND_HALF_UP

from tax_engine.catalogo import (
    CatalogoNormativo,
    EstadoConfirmacion,
    Indicador,
    Jerarquia,
    NormaFuente,
    ReglaFiscal,
    ReglaVersion,
    Tarifa,
    TarifaTramo,
    TipoIndicador,
    TipoNorma,
    TipoTarifa,
)


def _redondear_centavos(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _actualizar_art96(tramos_base: list[dict], factor: Decimal) -> list[TarifaTramo]:
    """Aplica factor de actualizacion a una tarifa Art. 96."""
    resultado = []
    for t in tramos_base:
        li = _redondear_centavos(t["li"] * factor)
        ls = _redondear_centavos(t["ls"] * factor) if t["ls"] is not None else None
        cf = _redondear_centavos(t["cf"] * factor)
        resultado.append(TarifaTramo(
            orden=t["orden"],
            limite_inferior=li,
            limite_superior=ls,
            cuota_fija=cf,
            porcentaje=t["pct"],
        ))
    return resultado


# ---------------------------------------------------------------------------
# Datos base Art. 96 2025 (fuente: Anexo 8 RMF 2025)
# ---------------------------------------------------------------------------

_ART96_BASE_2025 = [
    {"orden": 1, "li": Decimal("0.01"), "ls": Decimal("746.04"), "cf": Decimal("0.00"), "pct": Decimal("1.92")},
    {"orden": 2, "li": Decimal("746.05"), "ls": Decimal("6332.05"), "cf": Decimal("14.32"), "pct": Decimal("6.40")},
    {"orden": 3, "li": Decimal("6332.06"), "ls": Decimal("11128.01"), "cf": Decimal("371.83"), "pct": Decimal("10.88")},
    {"orden": 4, "li": Decimal("11128.02"), "ls": Decimal("12935.82"), "cf": Decimal("893.63"), "pct": Decimal("16.00")},
    {"orden": 5, "li": Decimal("12935.83"), "ls": Decimal("15487.71"), "cf": Decimal("1182.88"), "pct": Decimal("17.92")},
    {"orden": 6, "li": Decimal("15487.72"), "ls": Decimal("31236.49"), "cf": Decimal("1640.18"), "pct": Decimal("21.36")},
    {"orden": 7, "li": Decimal("31236.50"), "ls": Decimal("49233.00"), "cf": Decimal("5004.12"), "pct": Decimal("23.52")},
    {"orden": 8, "li": Decimal("49233.01"), "ls": Decimal("93993.90"), "cf": Decimal("9236.89"), "pct": Decimal("30.00")},
    {"orden": 9, "li": Decimal("93993.91"), "ls": Decimal("125325.20"), "cf": Decimal("22665.17"), "pct": Decimal("32.00")},
    {"orden": 10, "li": Decimal("125325.21"), "ls": Decimal("375975.61"), "cf": Decimal("32691.18"), "pct": Decimal("34.00")},
    {"orden": 11, "li": Decimal("375975.62"), "ls": None, "cf": Decimal("117912.32"), "pct": Decimal("35.00")},
]

# Art. 152 anual 2025
_ART152_BASE_2025 = [
    {"orden": 1, "li": Decimal("0.01"), "ls": Decimal("8952.49"), "cf": Decimal("0.00"), "pct": Decimal("1.92")},
    {"orden": 2, "li": Decimal("8952.50"), "ls": Decimal("75984.55"), "cf": Decimal("171.88"), "pct": Decimal("6.40")},
    {"orden": 3, "li": Decimal("75984.56"), "ls": Decimal("133536.07"), "cf": Decimal("4461.94"), "pct": Decimal("10.88")},
    {"orden": 4, "li": Decimal("133536.08"), "ls": Decimal("155229.80"), "cf": Decimal("10723.55"), "pct": Decimal("16.00")},
    {"orden": 5, "li": Decimal("155229.81"), "ls": Decimal("185852.57"), "cf": Decimal("14194.54"), "pct": Decimal("17.92")},
    {"orden": 6, "li": Decimal("185852.58"), "ls": Decimal("374837.88"), "cf": Decimal("19682.13"), "pct": Decimal("21.36")},
    {"orden": 7, "li": Decimal("374837.89"), "ls": Decimal("590795.99"), "cf": Decimal("60049.40"), "pct": Decimal("23.52")},
    {"orden": 8, "li": Decimal("590796.00"), "ls": Decimal("1127926.84"), "cf": Decimal("110842.74"), "pct": Decimal("30.00")},
    {"orden": 9, "li": Decimal("1127926.85"), "ls": Decimal("1503902.46"), "cf": Decimal("271981.99"), "pct": Decimal("32.00")},
    {"orden": 10, "li": Decimal("1503902.47"), "ls": Decimal("4511707.37"), "cf": Decimal("392294.17"), "pct": Decimal("34.00")},
    {"orden": 11, "li": Decimal("4511707.38"), "ls": None, "cf": Decimal("1414947.85"), "pct": Decimal("35.00")},
]

# Factor de actualizacion publicado en Anexo 8 RMF 2026, DOF 28/12/2025
_FACTOR_2026 = Decimal("1.1321")


def construir_catalogo() -> CatalogoNormativo:
    """Construye el catalogo normativo con todos los datos verificados de 2025/2026."""
    cat = CatalogoNormativo()

    # ===================================================================
    # Normas fuente
    # ===================================================================

    cat.agregar_norma(NormaFuente(
        id="LISR_2025",
        tipo=TipoNorma.LEY,
        identificador="Ley del Impuesto sobre la Renta",
        fecha_publicacion_dof=datetime.date(2024, 11, 12),
        descripcion="LISR vigente para ejercicio 2025-2026",
    ))
    cat.agregar_norma(NormaFuente(
        id="ANEXO8_RMF_2025",
        tipo=TipoNorma.ANEXO_RMF,
        identificador="Anexo 8 de la RMF 2025",
        fecha_publicacion_dof=datetime.date(2024, 12, 29),
        descripcion="Tarifas de ISR ejercicio 2025",
    ))
    cat.agregar_norma(NormaFuente(
        id="ANEXO8_RMF_2026",
        tipo=TipoNorma.ANEXO_RMF,
        identificador="Anexo 8 de la RMF 2026",
        fecha_publicacion_dof=datetime.date(2025, 12, 28),
        url="https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/anexos/Anexo-8-RMF-2026_DOF-28122025.pdf",
        descripcion="Tarifas de ISR ejercicio 2026, factor actualizacion 1.1321",
    ))
    cat.agregar_norma(NormaFuente(
        id="DOF_UMA_2025",
        tipo=TipoNorma.DOF,
        identificador="DOF UMA 2025",
        fecha_publicacion_dof=datetime.date(2025, 1, 10),
        descripcion="Valor UMA 2025: $113.14 diario",
    ))
    cat.agregar_norma(NormaFuente(
        id="DOF_UMA_2026",
        tipo=TipoNorma.DOF,
        identificador="DOF UMA 2026",
        fecha_publicacion_dof=datetime.date(2026, 1, 9),
        descripcion="Valor UMA 2026: $117.31 diario",
    ))
    cat.agregar_norma(NormaFuente(
        id="LIF_2026",
        tipo=TipoNorma.LEY_INGRESOS,
        identificador="Ley de Ingresos de la Federacion para el ejercicio 2026",
        fecha_publicacion_dof=datetime.date(2025, 11, 13),
        descripcion="LIF 2026 - Art. 25 fr. VI sustituye tasa Art. 113-A fr. III LISR",
    ))
    cat.agregar_norma(NormaFuente(
        id="LIVA_2025",
        tipo=TipoNorma.LEY,
        identificador="Ley del Impuesto al Valor Agregado",
        fecha_publicacion_dof=datetime.date(2024, 11, 12),
        descripcion="LIVA vigente",
    ))

    # ===================================================================
    # Reglas fiscales (claves estables)
    # ===================================================================

    _reglas = [
        ReglaFiscal("RESICO_PF.LIMITE_INGRESOS_ANUAL", "Limite de ingresos anuales para RESICO PF", "RESICO_PF"),
        ReglaFiscal("ARRENDAMIENTO.DEDUCCION_OPCIONAL_PCT", "Porcentaje de deduccion opcional Art. 115", "ARRENDAMIENTO"),
        ReglaFiscal("ARRENDAMIENTO.RETENCION_ISR_PCT", "Retencion ISR cuando arrendatario es PM Art. 116", "ARRENDAMIENTO"),
        ReglaFiscal("ARRENDAMIENTO.RETENCION_IVA_FRACCION", "Fraccion de IVA retenido Art. 1-A LIVA", "ARRENDAMIENTO"),
        ReglaFiscal("ARRENDAMIENTO.UMBRAL_TRIMESTRAL_UMA", "Umbral en UMA elevadas al mes para opcion trimestral", "ARRENDAMIENTO"),
        ReglaFiscal("PLATAFORMAS.RETENCION_ISR_TRANSPORTE", "Retencion ISR transporte/entrega Art. 113-A fr. I", "PLATAFORMAS"),
        ReglaFiscal("PLATAFORMAS.RETENCION_ISR_HOSPEDAJE", "Retencion ISR hospedaje Art. 113-A fr. II", "PLATAFORMAS"),
        ReglaFiscal("PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS", "Retencion ISR enajenacion/servicios Art. 113-A fr. III", "PLATAFORMAS"),
        ReglaFiscal("PLATAFORMAS.RETENCION_IVA_CON_RFC", "Retencion IVA con RFC Art. 18-J LIVA", "PLATAFORMAS"),
        ReglaFiscal("PLATAFORMAS.RETENCION_IVA_SIN_RFC", "Retencion IVA sin RFC Art. 18-J LIVA", "PLATAFORMAS"),
        ReglaFiscal("PLATAFORMAS.LIMITE_PAGO_DEFINITIVO", "Limite ingresos anuales opcion pago definitivo Art. 113-B", "PLATAFORMAS"),
    ]
    for r in _reglas:
        cat.agregar_regla(r)

    # ===================================================================
    # Versiones de reglas
    # ===================================================================

    # --- RESICO PF ---
    cat.agregar_version(ReglaVersion(
        id="RESICO_PF.LIMITE_2025",
        regla_clave="RESICO_PF.LIMITE_INGRESOS_ANUAL",
        valor=Decimal("3500000"),
        unidad="MXN",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 113-E LISR",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))

    # --- Arrendamiento ---
    cat.agregar_version(ReglaVersion(
        id="ARREND.DEDUCCION_OPT",
        regla_clave="ARRENDAMIENTO.DEDUCCION_OPCIONAL_PCT",
        valor=Decimal("35"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 115 LISR",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    cat.agregar_version(ReglaVersion(
        id="ARREND.RETENCION_ISR",
        regla_clave="ARRENDAMIENTO.RETENCION_ISR_PCT",
        valor=Decimal("10"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 116 LISR",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    cat.agregar_version(ReglaVersion(
        id="ARREND.RETENCION_IVA",
        regla_clave="ARRENDAMIENTO.RETENCION_IVA_FRACCION",
        valor=Decimal(2) / Decimal(3),
        unidad="fraccion de IVA",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LIVA_2025",
        articulo="Art. 1-A LIVA",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    # Confirmacion pendiente #3: umbral trimestral
    cat.agregar_version(ReglaVersion(
        id="ARREND.UMBRAL_TRIM",
        regla_clave="ARRENDAMIENTO.UMBRAL_TRIMESTRAL_UMA",
        valor=Decimal("10"),
        unidad="UMA elevadas al mes",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 116 LISR",
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #3: el umbral de la opcion trimestral es 10 UMA "
            "elevadas al mes (lo que dice el proyecto hoy) o un valor anual (lo que "
            "dicen varias fuentes secundarias)?"
        ),
    ))

    # --- Plataformas Tecnologicas ---
    cat.agregar_version(ReglaVersion(
        id="PLAT.ISR_TRANSPORTE_BASE",
        regla_clave="PLATAFORMAS.RETENCION_ISR_TRANSPORTE",
        valor=Decimal("2.1"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 113-A fr. I LISR",
        jerarquia=Jerarquia.BASE,
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    cat.agregar_version(ReglaVersion(
        id="PLAT.ISR_HOSPEDAJE_BASE",
        regla_clave="PLATAFORMAS.RETENCION_ISR_HOSPEDAJE",
        valor=Decimal("4"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 113-A fr. II LISR",
        jerarquia=Jerarquia.BASE,
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    # Art. 113-A fr. III LISR dice 1%
    cat.agregar_version(ReglaVersion(
        id="PLAT.ISR_ENAJENACION_BASE",
        regla_clave="PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS",
        valor=Decimal("1"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 113-A fr. III LISR",
        jerarquia=Jerarquia.BASE,
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    # LIF 2026 Art. 25 fr. VI SUSTITUYE la tasa a 2.5% para el ejercicio 2026
    cat.agregar_version(ReglaVersion(
        id="PLAT.ISR_ENAJENACION_LIF2026",
        regla_clave="PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS",
        valor=Decimal("2.5"),
        unidad="%",
        vigencia_desde=datetime.date(2026, 1, 1),
        vigencia_hasta=datetime.date(2027, 1, 1),
        norma_fuente_id="LIF_2026",
        articulo="Art. 25 fr. VI LIF 2026",
        jerarquia=Jerarquia.SUSTITUYE,
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #5: de verdad coexisten 2.1%, 4% y 2.5% "
            "segun actividad, o hay una disposicion posterior que unifico la tasa? "
            "Confirmacion pendiente #6: el 2.5% del Art. 25 fr. VI aplica a PF, "
            "o solo a PM como afirman varias fuentes secundarias?"
        ),
    ))
    # IVA Plataformas
    cat.agregar_version(ReglaVersion(
        id="PLAT.IVA_CON_RFC",
        regla_clave="PLATAFORMAS.RETENCION_IVA_CON_RFC",
        valor=Decimal("8"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LIVA_2025",
        articulo="Art. 18-J LIVA",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    cat.agregar_version(ReglaVersion(
        id="PLAT.IVA_SIN_RFC",
        regla_clave="PLATAFORMAS.RETENCION_IVA_SIN_RFC",
        valor=Decimal("16"),
        unidad="%",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LIVA_2025",
        articulo="Art. 18-J LIVA",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    cat.agregar_version(ReglaVersion(
        id="PLAT.LIMITE_DEFINITIVO",
        regla_clave="PLATAFORMAS.LIMITE_PAGO_DEFINITIVO",
        valor=Decimal("300000"),
        unidad="MXN anuales",
        vigencia_desde=datetime.date(2025, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 113-B LISR",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))

    # ===================================================================
    # Reglas con confirmacion pendiente (solo registrar, no codificar como definitivas)
    # ===================================================================

    cat.agregar_regla(ReglaFiscal(
        "RESICO_PF.BASE_CALCULO_MENSUAL_O_ACUMULADA",
        "Art. 113-E: tabla RESICO PF se aplica sobre ingreso del mes o acumulado del ejercicio?",
        "RESICO_PF",
    ))
    cat.agregar_version(ReglaVersion(
        id="RESICO_PF.BASE_CALCULO_PENDIENTE",
        regla_clave="RESICO_PF.BASE_CALCULO_MENSUAL_O_ACUMULADA",
        valor=Decimal("0"),
        unidad="pendiente",
        vigencia_desde=datetime.date(2025, 1, 1),
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #1: la tabla de RESICO PF se aplica "
            "sobre el ingreso del mes o sobre el acumulado del ejercicio?"
        ),
    ))

    cat.agregar_regla(ReglaFiscal(
        "RESICO_PF.LIMITE_INCLUYE_SUELDOS",
        "Art. 113-E: el limite de $3.5M incluye ingresos por sueldos o solo los de la actividad?",
        "RESICO_PF",
    ))
    cat.agregar_version(ReglaVersion(
        id="RESICO_PF.LIMITE_SUELDOS_PENDIENTE",
        regla_clave="RESICO_PF.LIMITE_INCLUYE_SUELDOS",
        valor=Decimal("0"),
        unidad="pendiente",
        vigencia_desde=datetime.date(2025, 1, 1),
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #2: el limite de $3.5M incluye ingresos "
            "por sueldos o solo los de la actividad?"
        ),
    ))

    cat.agregar_regla(ReglaFiscal(
        "ARRENDAMIENTO.PREDIAL_ADICIONAL_O_INCLUIDO",
        "Art. 115: el impuesto predial es adicional a la deduccion opcional del 35% o esta comprendido?",
        "ARRENDAMIENTO",
    ))
    cat.agregar_version(ReglaVersion(
        id="ARREND.PREDIAL_PENDIENTE",
        regla_clave="ARRENDAMIENTO.PREDIAL_ADICIONAL_O_INCLUIDO",
        valor=Decimal("0"),
        unidad="pendiente",
        vigencia_desde=datetime.date(2025, 1, 1),
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #4: el impuesto predial es adicional "
            "a la deduccion opcional del 35% o esta comprendido en ella?"
        ),
    ))

    # ===================================================================
    # Indicadores: UMA
    # ===================================================================

    # UMA 2025: vigente desde 01/02/2025 hasta 31/01/2026
    cat.agregar_indicador(Indicador(
        id="UMA_DIARIA_2025",
        tipo=TipoIndicador.UMA_DIARIA,
        valor=Decimal("113.14"),
        vigencia_desde=datetime.date(2025, 2, 1),
        vigencia_hasta=datetime.date(2026, 2, 1),
        norma_fuente_id="DOF_UMA_2025",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    # UMA 2024: para enero 2025 (usamos el valor previo)
    cat.agregar_indicador(Indicador(
        id="UMA_DIARIA_2024",
        tipo=TipoIndicador.UMA_DIARIA,
        valor=Decimal("108.57"),
        vigencia_desde=datetime.date(2024, 2, 1),
        vigencia_hasta=datetime.date(2025, 2, 1),
        norma_fuente_id="DOF_UMA_2025",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))
    # UMA 2026: vigente desde 01/02/2026 hasta 31/01/2027
    cat.agregar_indicador(Indicador(
        id="UMA_DIARIA_2026",
        tipo=TipoIndicador.UMA_DIARIA,
        valor=Decimal("117.31"),
        vigencia_desde=datetime.date(2026, 2, 1),
        vigencia_hasta=datetime.date(2027, 2, 1),
        norma_fuente_id="DOF_UMA_2026",
        estado=EstadoConfirmacion.CONFIRMADO,
    ))

    # ===================================================================
    # Tarifas 2025
    # ===================================================================

    # Art. 96 mensual 2025
    tramos_art96_2025 = [
        TarifaTramo(orden=i + 1, limite_inferior=t["li"], limite_superior=t["ls"],
                     cuota_fija=t["cf"], porcentaje=t["pct"])
        for i, t in enumerate(_ART96_BASE_2025)
    ]
    cat.agregar_tarifa(Tarifa(
        id="ART96_MENSUAL_2025",
        tipo=TipoTarifa.ART96_MENSUAL,
        vigencia_desde=datetime.date(2025, 1, 1),
        vigencia_hasta=datetime.date(2026, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2025",
        articulo="Art. 96 LISR",
        tramos=tramos_art96_2025,
    ))

    # Art. 152 anual 2025
    tramos_art152_2025 = [
        TarifaTramo(orden=i + 1, limite_inferior=t["li"], limite_superior=t["ls"],
                     cuota_fija=t["cf"], porcentaje=t["pct"])
        for i, t in enumerate(_ART152_BASE_2025)
    ]
    cat.agregar_tarifa(Tarifa(
        id="ART152_ANUAL_2025",
        tipo=TipoTarifa.ART152_ANUAL,
        vigencia_desde=datetime.date(2025, 1, 1),
        vigencia_hasta=datetime.date(2026, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2025",
        articulo="Art. 152 LISR",
        tramos=tramos_art152_2025,
    ))

    # RESICO PF mensual 2025 (mismos tramos que usa el fallback)
    cat.agregar_tarifa(Tarifa(
        id="RESICO_PF_MENSUAL_2025",
        tipo=TipoTarifa.RESICO_PF_MENSUAL,
        vigencia_desde=datetime.date(2025, 1, 1),
        vigencia_hasta=datetime.date(2026, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2025",
        articulo="Art. 113-E LISR",
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #1: se aplica sobre ingreso del mes "
            "o sobre acumulado del ejercicio?"
        ),
        tramos=[
            TarifaTramo(orden=1, limite_inferior=Decimal("0.01"), limite_superior=Decimal("25000.00"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("1.00")),
            TarifaTramo(orden=2, limite_inferior=Decimal("25000.01"), limite_superior=Decimal("50000.00"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("1.10")),
            TarifaTramo(orden=3, limite_inferior=Decimal("50000.01"), limite_superior=Decimal("83333.33"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("1.50")),
            TarifaTramo(orden=4, limite_inferior=Decimal("83333.34"), limite_superior=Decimal("208333.33"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("2.00")),
            TarifaTramo(orden=5, limite_inferior=Decimal("208333.34"), limite_superior=Decimal("291666.66"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("2.50")),
        ],
    ))

    # ===================================================================
    # Tarifas 2026 (actualizadas con factor 1.1321)
    # ===================================================================

    # Art. 96 mensual 2026
    tramos_art96_2026 = _actualizar_art96(_ART96_BASE_2025, _FACTOR_2026)
    cat.agregar_tarifa(Tarifa(
        id="ART96_MENSUAL_2026",
        tipo=TipoTarifa.ART96_MENSUAL,
        vigencia_desde=datetime.date(2026, 1, 1),
        vigencia_hasta=datetime.date(2027, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2026",
        articulo="Art. 96 LISR",
        estado=EstadoConfirmacion.CONFIRMADO,
        nota_confirmacion=(
            "Valores calculados aplicando factor 1.1321 a base 2025. "
            "Verificar contra PDF original del Anexo 8 RMF 2026 cuando "
            "el acceso a sat.gob.mx este disponible."
        ),
        tramos=tramos_art96_2026,
    ))

    # Art. 152 anual 2026
    tramos_art152_2026 = _actualizar_art96(_ART152_BASE_2025, _FACTOR_2026)
    cat.agregar_tarifa(Tarifa(
        id="ART152_ANUAL_2026",
        tipo=TipoTarifa.ART152_ANUAL,
        vigencia_desde=datetime.date(2026, 1, 1),
        vigencia_hasta=datetime.date(2027, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2026",
        articulo="Art. 152 LISR",
        estado=EstadoConfirmacion.CONFIRMADO,
        nota_confirmacion=(
            "Valores calculados aplicando factor 1.1321 a base 2025. "
            "Verificar contra PDF original."
        ),
        tramos=tramos_art152_2026,
    ))

    # RESICO PF mensual 2026 (mismos tramos que 2025 — la tarifa RESICO
    # no se actualiza con el Anexo 8, esta fija en la ley)
    cat.agregar_tarifa(Tarifa(
        id="RESICO_PF_MENSUAL_2026",
        tipo=TipoTarifa.RESICO_PF_MENSUAL,
        vigencia_desde=datetime.date(2026, 1, 1),
        vigencia_hasta=datetime.date(2027, 1, 1),
        norma_fuente_id="LISR_2025",
        articulo="Art. 113-E LISR",
        estado=EstadoConfirmacion.PENDIENTE_CONTADOR,
        nota_confirmacion=(
            "Confirmacion pendiente #1: se aplica sobre ingreso del mes "
            "o sobre acumulado del ejercicio?"
        ),
        tramos=[
            TarifaTramo(orden=1, limite_inferior=Decimal("0.01"), limite_superior=Decimal("25000.00"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("1.00")),
            TarifaTramo(orden=2, limite_inferior=Decimal("25000.01"), limite_superior=Decimal("50000.00"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("1.10")),
            TarifaTramo(orden=3, limite_inferior=Decimal("50000.01"), limite_superior=Decimal("83333.33"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("1.50")),
            TarifaTramo(orden=4, limite_inferior=Decimal("83333.34"), limite_superior=Decimal("208333.33"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("2.00")),
            TarifaTramo(orden=5, limite_inferior=Decimal("208333.34"), limite_superior=Decimal("291666.66"),
                        cuota_fija=Decimal("0"), porcentaje=Decimal("0"), tasa=Decimal("2.50")),
        ],
    ))

    # Arrendamiento mensual 2026 = misma tarifa que Art. 96 mensual 2026
    cat.agregar_tarifa(Tarifa(
        id="ARRENDAMIENTO_MENSUAL_2026",
        tipo=TipoTarifa.ARRENDAMIENTO_MENSUAL,
        vigencia_desde=datetime.date(2026, 1, 1),
        vigencia_hasta=datetime.date(2027, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2026",
        articulo="Art. 96 LISR (aplicado via Art. 106 LISR)",
        tramos=tramos_art96_2026,
    ))

    # Arrendamiento trimestral 2026 = Art. 96 x3
    tramos_arrend_trim_2026 = []
    for t in tramos_art96_2026:
        tramos_arrend_trim_2026.append(TarifaTramo(
            orden=t.orden,
            limite_inferior=t.limite_inferior * Decimal("3"),
            limite_superior=t.limite_superior * Decimal("3") if t.limite_superior is not None else None,
            cuota_fija=t.cuota_fija * Decimal("3"),
            porcentaje=t.porcentaje,
        ))
    cat.agregar_tarifa(Tarifa(
        id="ARRENDAMIENTO_TRIMESTRAL_2026",
        tipo=TipoTarifa.ARRENDAMIENTO_TRIMESTRAL,
        vigencia_desde=datetime.date(2026, 1, 1),
        vigencia_hasta=datetime.date(2027, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2026",
        articulo="Art. 96 LISR x3 (Art. 106 LISR opcion trimestral)",
        tramos=tramos_arrend_trim_2026,
    ))

    # Arrendamiento mensual 2025
    cat.agregar_tarifa(Tarifa(
        id="ARRENDAMIENTO_MENSUAL_2025",
        tipo=TipoTarifa.ARRENDAMIENTO_MENSUAL,
        vigencia_desde=datetime.date(2025, 1, 1),
        vigencia_hasta=datetime.date(2026, 1, 1),
        norma_fuente_id="ANEXO8_RMF_2025",
        articulo="Art. 96 LISR (aplicado via Art. 106 LISR)",
        tramos=tramos_art96_2025,
    ))

    return cat


# Singleton del catalogo cargado
_catalogo_global: CatalogoNormativo | None = None


def obtener_catalogo() -> CatalogoNormativo:
    """Obtiene el catalogo normativo global (lazy singleton)."""
    global _catalogo_global
    if _catalogo_global is None:
        _catalogo_global = construir_catalogo()
    return _catalogo_global
