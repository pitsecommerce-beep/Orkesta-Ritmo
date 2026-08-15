import { NextRequest, NextResponse } from "next/server";
import { extraerDatosConstancia } from "@/lib/extract-constancia";

interface TextItem {
  str?: string;
  hasEOL?: boolean;
}

async function extractTextFromPdf(data: Uint8Array): Promise<string> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");

  const doc = await pdfjs.getDocument({
    data,
    verbosity: 0,
    useSystemFonts: false,
    disableFontFace: true,
    isEvalSupported: false,
  }).promise;

  try {
    const pages: string[] = [];
    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const content = await page.getTextContent();
      let pageText = "";
      for (const item of content.items as TextItem[]) {
        pageText += item.str ?? "";
        if (item.hasEOL) pageText += "\n";
      }
      pages.push(pageText);
    }
    return pages.join("\n");
  } finally {
    await doc.destroy();
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
