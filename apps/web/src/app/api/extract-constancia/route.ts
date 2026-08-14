import { NextRequest, NextResponse } from "next/server";
import { extraerDatosConstancia } from "@/lib/extract-constancia";
import { PDFParse } from "pdf-parse";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json(
        { valido: false, error: "No se recibió archivo PDF" },
        { status: 400 },
      );
    }

    const buffer = await file.arrayBuffer();
    const parser = new PDFParse({ data: new Uint8Array(buffer) });
    const result = await parser.getText();
    const text = result.text;

    if (!text.trim()) {
      return NextResponse.json({
        valido: false,
        error: "No se pudo extraer texto del PDF",
      });
    }

    const datos = extraerDatosConstancia(text);
    return NextResponse.json(datos);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Error desconocido";
    return NextResponse.json(
      { valido: false, error: `Error al procesar PDF: ${msg}` },
      { status: 500 },
    );
  }
}
