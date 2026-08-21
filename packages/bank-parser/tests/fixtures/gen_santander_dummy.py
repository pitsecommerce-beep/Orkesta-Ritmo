"""
Genera estados de cuenta Santander SINTETICOS (debito y credito) que replican
la estructura de los reales, incluyendo paginas de publicidad intercaladas,
y los rasteriza para reproducir la condicion critica del documento real:
CERO capa de texto extraible (Santander entrega PDFs rasterizados).

Todos los datos son ficticios. Los montos cuadran aritmeticamente a proposito,
para que el parser pueda validar el cuadre.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

ROJO = colors.HexColor("#EC0000")
styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Heading2"], fontSize=13, textColor=colors.black)
N = ParagraphStyle("N", parent=styles["Normal"], fontSize=8)
SM = ParagraphStyle("SM", parent=styles["Normal"], fontSize=7)
ADV = ParagraphStyle("ADV", parent=styles["Heading1"], fontSize=22, textColor=ROJO, alignment=1)
ADV2 = ParagraphStyle("ADV2", parent=styles["Normal"], fontSize=12, alignment=1)


def hdr(txt, w=17.5 * cm):
    """Banda roja de encabezado de seccion, como usa Santander."""
    t = Table([[txt]], colWidths=[w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROJO),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def grid(rows, widths, header_bg=colors.HexColor("#D9D9D9"), align_right=None, size=6.5):
    t = Table(rows, colWidths=widths, repeatRows=1)
    st = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), size),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    for c in (align_right or []):
        st.append(("ALIGN", (c, 1), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(st))
    return t


def pagina_publicidad(story, titulo, cuerpo):
    """Pagina de puro marketing, sin datos fiscales. El parser debe ignorarla."""
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(titulo, ADV))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(cuerpo, ADV2))
    story.append(Spacer(1, 1 * cm))
    b = Table([[""]], colWidths=[14 * cm], rowHeights=[6 * cm])
    b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5E6E6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0C0C0")),
    ]))
    story.append(b)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Contrata en tu app Santander. Consulta terminos y condiciones en la pagina del banco. "
        "Documento sintetico de prueba, sin validez.", SM))
    story.append(PageBreak())


# =====================================================================
# DEBITO
# =====================================================================
def build_debito(path):
    s = []
    s.append(Paragraph("Santander", ParagraphStyle("L", parent=styles["Heading1"], fontSize=18, textColor=ROJO)))
    s.append(Paragraph("Banco Santander Mexico, S.A., Institucion de Banca Multiple.", SM))
    s.append(Spacer(1, 6))
    s.append(Paragraph("ESTADO DE CUENTA", H))
    s.append(Spacer(1, 8))

    s.append(grid([
        ["JUAN PEREZ SINTETICO", "CODIGO DE CLIENTE NO. 00000000"],
        ["CALLE FICTICIA 000", "R.F.C.  XAXX010101000"],
        ["COLONIA DE PRUEBA", "MONEDA  MONEDA NACIONAL"],
        ["C.P. 00000  CIUDAD DEMO, ESTADO DEMO", "SUCURSAL  0000 SUCURSAL DEMO"],
        ["", "PERIODO  DEL 01-DIC-2025 AL 31-DIC-2025"],
        ["", "CORTE AL  31-DIC-2025"],
    ], [9 * cm, 8.5 * cm], header_bg=colors.white, size=7.5))
    s.append(Spacer(1, 12))

    s.append(Paragraph("Resumen informativo.", H))
    s.append(Spacer(1, 4))
    s.append(grid([
        ["PRODUCTO", "NUMERO DE CUENTA", "INTERESES BRUTOS", "ISR RETENIDO (0.50%)", "INTERESES NETOS", "COMISIONES COBRADAS"],
        ["CUENTA DEMO SINTETICA", "00-00000000-0", "0.00", "0.00", "0.00", "0.00"],
    ], [4.6 * cm, 3 * cm, 2.4 * cm, 2.6 * cm, 2.4 * cm, 2.5 * cm]))
    s.append(Spacer(1, 10))

    s.append(Paragraph("Cuenta de cheques.", H))
    s.append(Spacer(1, 4))
    s.append(grid([
        ["CUENTA DEMO SINTETICA", "00-00000000-0", "CUENTA CLABE: 014000000000000000"],
    ], [6 * cm, 4 * cm, 7.5 * cm], header_bg=colors.HexColor("#D9D9D9")))
    s.append(Spacer(1, 4))
    s.append(grid([
        ["Saldo inicial", "1,000.00"],
        ["+ Depositos", "8,300.50"],
        ["- Retiros", "4,300.50"],
        ["= Saldo final", "5,000.00"],
    ], [6 * cm, 4 * cm], header_bg=colors.white, align_right=[1], size=7.5))
    s.append(PageBreak())

    # Publicidad intercalada ANTES de los movimientos, como en el real
    pagina_publicidad(s, "PROMOCION SINTETICA", "Este bloque existe solo para verificar que el parser lo ignora.")

    # Movimientos (la seccion que importa)
    s.append(Paragraph("Santander", ParagraphStyle("L2", parent=styles["Heading1"], fontSize=14, textColor=ROJO)))
    s.append(Paragraph("JUAN PEREZ SINTETICO", N))
    s.append(Paragraph("CODIGO DE CLIENTE NO. 00000000 &nbsp;&nbsp; PERIODO DEL 01-DIC-2025 AL 31-DIC-2025", SM))
    s.append(Spacer(1, 8))
    s.append(Paragraph("Detalle de movimientos cuenta de cheques.", H))
    s.append(Spacer(1, 4))
    s.append(grid([["CUENTA DEMO SINTETICA 00-00000000-0", ""]], [12 * cm, 5.5 * cm], header_bg=colors.HexColor("#D9D9D9")))
    s.append(grid([["SALDO FINAL DEL PERIODO ANTERIOR:", "$1,000.00"]], [12 * cm, 5.5 * cm],
                  header_bg=colors.HexColor("#EFEFEF"), align_right=[1]))
    s.append(Spacer(1, 2))

    movs = [
        ["FECHA", "FOLIO", "DESCRIPCION", "DEPOSITO", "RETIRO", "SALDO"],
        ["04-DIC-2025", "0000001",
         "ABONO TRANSFERENCIA SPEI HORA 10:00:00\nRECIBIDO DE BANCO DEMO\nDE LA CUENTA 000000000000000000\n"
         "DEL CLIENTE CLIENTE SINTETICO UNO\nCLAVE DE RASTREO DEMO0000000000000000001\nREF 0000001\n"
         "CONCEPTO pago de servicios\nRFC XAXX010101000",
         "5,000.00", "", "6,000.00"],
        ["05-DIC-2025", "0000002",
         "PAGO TRANSFERENCIA SPEI HORA 11:00:00\nENVIADO A PROVEEDOR DEMO\nA LA CUENTA 000000000000000001\n"
         "AL CLIENTE PROVEEDOR SINTETICO\nCLAVE DE RASTREO DEMO0000000000000000002\nREF 0000002\nCONCEPTO compra insumos",
         "", "1,500.00", "4,500.00"],
        ["10-DIC-2025", "0000003",
         "ABONO TRANSFERENCIA SPEI HORA 12:00:00\nRECIBIDO DE BANCO DEMO DOS\nDE LA CUENTA 000000000000000002\n"
         "DEL CLIENTE CLIENTE SINTETICO DOS\nCLAVE DE RASTREO DEMO0000000000000000003\nREF 0000003\n"
         "CONCEPTO honorarios\nRFC XEXX010101000",
         "2,300.50", "", "6,800.50"],
        ["15-DIC-2025", "0000004",
         "DISP ATM PROPIO TARJ DEB X00000 TERMINACION 0000 15DIC25", "", "800.50", "6,000.00"],
        ["20-DIC-2025", "0000005",
         "ABONO TRANSFERENCIA ENLACE Transferencia a JUAN PEREZ", "1,000.00", "", "7,000.00"],
        ["28-DIC-2025", "0000006",
         "PAGO TRANSF RAPIDA SPEI TRASPASO A CUENTA DEMO RFC XAXX010101000 IVA 0.0 REF 0000006",
         "", "2,000.00", "5,000.00"],
        ["", "", "TOTAL", "8,300.50", "4,300.50", ""],
    ]
    rows = [movs[0]] + [[r[0], r[1], Paragraph(r[2].replace("\n", "<br/>"), SM), r[3], r[4], r[5]] for r in movs[1:]]
    s.append(grid(rows, [2.1 * cm, 1.5 * cm, 7.9 * cm, 2 * cm, 2 * cm, 2 * cm], align_right=[3, 4, 5]))
    s.append(Spacer(1, 3))
    s.append(grid([["SALDO FINAL DEL PERIODO:", "$5,000.00"]], [13.5 * cm, 4 * cm],
                  header_bg=colors.HexColor("#FFF2CC"), align_right=[1]))
    s.append(PageBreak())

    pagina_publicidad(s, "OTRA PROMOCION SINTETICA", "Segunda pagina de relleno posterior a los movimientos.")

    s.append(Paragraph("Significado de abreviaturas utilizadas en el estado de cuenta:", H))
    s.append(Spacer(1, 6))
    s.append(grid([
        ["ABO=", "ABONO (S)", "DEP=", "DEPOSITO"],
        ["CGO=", "CARGO", "SPEI=", "SISTEMA DE PAGOS ELECTRONICOS"],
        ["COM=", "COMISION", "TRANSF=", "TRANSFERENCIA"],
    ], [2 * cm, 6 * cm, 2 * cm, 6 * cm], header_bg=colors.white, size=7))
    s.append(Spacer(1, 10))
    s.append(Paragraph("DOCUMENTO SINTETICO DE PRUEBA. Datos ficticios. Sin validez fiscal ni bancaria.", SM))

    SimpleDocTemplate(path, pagesize=letter, topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                      leftMargin=1.5 * cm, rightMargin=1.5 * cm).build(s)


# =====================================================================
# CREDITO
# =====================================================================
def build_credito(path):
    s = []
    pagina_publicidad(s, "CARATULA PUBLICITARIA", "El estado de cuenta de credito abre con publicidad. El parser debe saltarla.")

    s.append(Paragraph("Santander", ParagraphStyle("L", parent=styles["Heading1"], fontSize=18, textColor=ROJO)))
    s.append(Paragraph("Tarjeta de Credito Santander DEMO", N))
    s.append(Spacer(1, 8))
    s.append(grid([
        ["JUAN PEREZ SINTETICO", "TU PAGO REQUERIDO ESTE PERIODO"],
        ["CALLE FICTICIA 000", "Periodo: Del 13-Nov-2025 al 12-Dic-2025"],
        ["C.P. 00000 CIUDAD DEMO", "Fecha de corte: 12-Dic-2025"],
        ["Numero de tarjeta: 0000 0000 0000 0000", "Numero de dias en el periodo: 30 dias"],
        ["RFC del Usuario: XAXX010101000", "Fecha limite de pago: Viernes, 02-ene-2026"],
        ["Sucursal: 0000", "Pago para no generar intereses: $ 4,500.00"],
        ["Numero de cliente: 00000000", "Pago minimo: $ 250.00"],
        ["CLABE: 014000000000000000", ""],
    ], [8.7 * cm, 8.8 * cm], header_bg=colors.white, size=7.5))
    s.append(Spacer(1, 10))

    s.append(hdr("RESUMEN DE CARGOS Y ABONOS DEL PERIODO"))
    s.append(grid([
        ["Adeudo del periodo anterior", "=", "$ 3,000.00"],
        ["Cargos regulares (no a meses)", "+", "$ 4,500.00"],
        ["Cargos y compras a meses (capital)", "+", "$ 0.00"],
        ["Monto de intereses", "+", "$ 0.00"],
        ["Monto de comisiones", "+", "$ 0.00"],
        ["IVA de intereses y comisiones", "+", "$ 0.00"],
        ["Pagos y abonos", "-", "$ 3,000.00"],
        ["PAGO PARA NO GENERAR INTERESES", "=", "$ 4,500.00"],
    ], [10 * cm, 1 * cm, 6.5 * cm], header_bg=colors.white, align_right=[2], size=7.5))
    s.append(Spacer(1, 8))

    s.append(hdr("NIVEL DE USO DE TU TARJETA"))
    s.append(grid([
        ["Saldo cargos regulares:", "$ 4,500.00"],
        ["Saldo cargos a meses:", "$ 0.00"],
        ["Saldo deudor total:", "$ 4,500.00"],
        ["Limite de credito:", "$ 50,000.00"],
        ["Credito disponible:", "$ 45,500.00"],
    ], [11 * cm, 6.5 * cm], header_bg=colors.white, align_right=[1], size=7.5))
    s.append(PageBreak())

    pagina_publicidad(s, "PROMOCION INTERMEDIA", "Bloque publicitario entre el resumen y el desglose de movimientos.")

    s.append(Paragraph("Santander", ParagraphStyle("L3", parent=styles["Heading1"], fontSize=14, textColor=ROJO)))
    s.append(Paragraph("Numero de cuenta: 0000 0000 0000 0000", SM))
    s.append(Spacer(1, 8))
    s.append(hdr("CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)"))
    s.append(grid([["Tarjeta Titular 0000000000000000", ""]], [12 * cm, 5.5 * cm], header_bg=colors.white, size=7))
    s.append(Spacer(1, 2))

    filas = [
        ["Fecha de la operacion", "Fecha de cargo", "Descripcion del movimiento", "", "", "Monto"],
        ["12-Nov-2025", "13-Nov-2025", "COMERCIO DEMO UNO", "AAA 000000000", "+", "$ 200.00"],
        ["15-Nov-2025", "17-Nov-2025", "COMERCIO DEMO DOS", "BBB 000000000", "+", "$ 1,300.00"],
        ["20-Nov-2025", "21-Nov-2025", "COMERCIO DEMO TRES", "CCC 000000000", "+", "$ 1,500.00"],
        ["25-Nov-2025", "25-Nov-2025", "PAGO POR TRANSFERENCIA", "", "-", "$ 3,000.00"],
        ["01-Dic-2025", "02-Dic-2025", "SUSCRIPCION DEMO", "DDD 000000000", "+", "$ 1,000.00"],
        ["05-Dic-2025", "06-Dic-2025", "COMERCIO DEMO CUATRO", "EEE 000000000", "+", "$ 500.00"],
    ]
    s.append(grid(filas, [2.5 * cm, 2.3 * cm, 6.2 * cm, 3 * cm, 0.8 * cm, 2.7 * cm], align_right=[5], size=6.5))
    s.append(Spacer(1, 4))
    s.append(grid([
        ["Total Cargos", "+", "$ 4,500.00"],
        ["Total Abonos", "-", "$ 3,000.00"],
    ], [13 * cm, 0.8 * cm, 3.7 * cm], header_bg=colors.white, align_right=[2], size=7.5))
    s.append(PageBreak())

    pagina_publicidad(s, "PROMOCION FINAL", "Publicidad posterior al desglose.")

    s.append(hdr("NOTAS ACLARATORIAS"))
    s.append(Spacer(1, 4))
    s.append(Paragraph("1. Texto de nota aclaratoria sintetica de relleno.", SM))
    s.append(Paragraph("2. Segunda nota aclaratoria sintetica de relleno.", SM))
    s.append(Spacer(1, 10))
    s.append(Paragraph("DOCUMENTO SINTETICO DE PRUEBA. Datos ficticios. Sin validez fiscal ni bancaria.", SM))

    SimpleDocTemplate(path, pagesize=letter, topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                      leftMargin=1.5 * cm, rightMargin=1.5 * cm).build(s)


if __name__ == "__main__":
    build_debito("/home/claude/out/santander_debito_TEXTO.pdf")
    build_credito("/home/claude/out/santander_credito_TEXTO.pdf")
    print("OK")
