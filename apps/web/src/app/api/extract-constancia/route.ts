import { NextRequest, NextResponse } from "next/server";
import { extraerDatosConstancia } from "@/lib/extract-constancia";
import { installPolyfills } from "@/lib/dommatrix-polyfill";

installPolyfills();

async function extractTextFromPdf(data: Uint8Array): Promise<string> {
  const { getDocument } = await import(
    "pdfjs-dist/legacy/build/pdf.mjs" as string
  );
  const loadingTask = getDocument({
    data,
    verbosity: 0,
    useSystemFonts: true,
  });
  const pdf = await loadingTask.promise;
  const pageTexts: string[] = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    let text = "";
    for (const item of content.items) {
      if ("str" in item) {
        text += item.str;
        if ("hasEOL" in item && item.hasEOL) text += "\n";
      }
    }
    pageTexts.push(text);
  }
  await pdf.cleanup();
  return pageTexts.join("\n");
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
