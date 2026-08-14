import { NextRequest, NextResponse } from "next/server";
import { extraerDatosConstancia } from "@/lib/extract-constancia";

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

    const buffer = Buffer.from(await file.arrayBuffer());

    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pdfParse = require("pdf-parse") as (buf: Buffer) => Promise<{ text: string }>;
    const { text } = await pdfParse(buffer);

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
