import { NextRequest, NextResponse } from "next/server";
import { PDFParse } from "pdf-parse";
import { extraerDatosConstancia } from "@/lib/extract-constancia";

async function extractTextFromPdf(data: Uint8Array): Promise<string> {
  const parser = new PDFParse({ data, verbosity: 0 });
  try {
    const result = await parser.getText();
    return result.text;
  } finally {
    await parser.destroy();
  }
}

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
    const text = await extractTextFromPdf(new Uint8Array(buffer));

    if (!text.trim()) {
      return NextResponse.json({
        valido: false,
        error: "No se pudo extraer texto del PDF. ¿Es un PDF escaneado (imagen)?",
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
