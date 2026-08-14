/**
 * Extraction logic for Constancia de Situación Fiscal (SAT PDF).
 *
 * Mirrors the patterns from packages/tax-engine/src/tax_engine/constancia.py
 * but in TypeScript, operating on plain text extracted from the PDF.
 */

export interface DatosConstanciaFront {
  rfc: string;
  nombre: string;
  tipoPersona: "fisica" | "moral" | "";
  regimen: string;
  domicilioCp: string;
  valido: boolean;
  error: string;
}

// --- Normalización ---

function normalizar(texto: string): string {
  return texto
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/\.$/, "")
    .replace(/\s+/g, " ")
    .trim();
}

// --- Catálogo c_RegimenFiscal: descripción normalizada → clave SAT ---

const CATALOGO_REGIMEN: Record<string, string> = {
  "general de ley personas morales": "601",
  "personas morales con fines no lucrativos": "603",
  "sueldos y salarios e ingresos asimilados a salarios": "605",
  "arrendamiento": "606",
  "regimen de enajenacion o adquisicion de bienes": "607",
  "demas ingresos": "608",
  "residentes en el extranjero sin establecimiento permanente en mexico": "610",
  "ingresos por dividendos (socios y accionistas)": "611",
  "personas fisicas con actividades empresariales y profesionales": "612",
  "ingresos por intereses": "614",
  "regimen de los ingresos por obtencion de premios": "615",
  "sin obligaciones fiscales": "616",
  "sociedades cooperativas de produccion que optan por diferir sus ingresos": "620",
  "incorporacion fiscal": "621",
  "actividades agricolas, ganaderas, silvicolas y pesqueras": "622",
  "opcional para grupos de sociedades": "623",
  "coordinados": "624",
  "regimen de las actividades empresariales con ingresos a traves de plataformas tecnologicas": "625",
  "regimen simplificado de confianza": "626",
  "hidrocarburos": "628",
  "de los regimenes fiscales preferentes y de las empresas multinacionales": "629",
  "enajenacion de acciones en bolsa de valores": "630",
};

// --- Clave SAT → régimen del sistema ---

const REGIMENES_SOPORTADOS: Record<string, string> = {
  "612": "RESICO_PF",
  "606": "ARRENDAMIENTO",
  "626": "RESICO_PF",
};

// --- Regex para bloque de identificación ---

const RE_RFC = /RFC\s*:\s*([A-ZÑ&0-9]{12,13})/i;
const RE_NOMBRE_COMPLETO =
  /(?:Denominaci[oó]n|Raz[oó]n\s+Social)\s*(?:\([^)]*\))?[^\S\n]*:[^\S\n]*(.+)/i;
const RE_NOMBRE_PARTES = /Nombre\s*\(?s?\)?\s*:[^\S\n]*(.+)/i;
const RE_PRIMER_APELLIDO = /Primer\s+Apellido\s*:[^\S\n]*(.+)/i;
const RE_SEGUNDO_APELLIDO = /Segundo\s+Apellido\s*:[^\S\n]*(.+)/i;
const RE_CP = /C[oó]digo\s+Postal\s*:\s*(\d{5})/i;

// --- Detección de regímenes en el texto ---

function detectarRegimenes(texto: string): string[] {
  const claves: string[] = [];
  const textoNorm = normalizar(texto);

  for (const [desc, clave] of Object.entries(CATALOGO_REGIMEN)) {
    if (textoNorm.includes(desc)) {
      claves.push(clave);
    }
  }

  return claves;
}

function derivarRegimen(claves: string[]): string {
  const soportados = claves
    .map((c) => REGIMENES_SOPORTADOS[c])
    .filter(Boolean);

  const tieneSueldos = claves.includes("605");

  if (soportados.includes("ARRENDAMIENTO")) {
    return tieneSueldos ? "ARRENDAMIENTO_SUELDOS" : "ARRENDAMIENTO";
  }

  if (soportados.includes("RESICO_PF")) {
    return tieneSueldos ? "RESICO_PF_SUELDOS" : "RESICO_PF";
  }

  return "";
}

// --- Extracción principal ---

export function extraerDatosConstancia(texto: string): DatosConstanciaFront {
  if (!texto.trim()) {
    return {
      rfc: "", nombre: "", tipoPersona: "", regimen: "",
      domicilioCp: "", valido: false, error: "Texto vacío",
    };
  }

  const rfcMatch = RE_RFC.exec(texto);
  const rfc = rfcMatch ? rfcMatch[1].toUpperCase() : "";

  const nombreCompletoMatch = RE_NOMBRE_COMPLETO.exec(texto);
  let nombre = "";
  if (nombreCompletoMatch) {
    nombre = nombreCompletoMatch[1].trim();
  } else {
    const partesNombre = RE_NOMBRE_PARTES.exec(texto);
    const primerAp = RE_PRIMER_APELLIDO.exec(texto);
    const segundoAp = RE_SEGUNDO_APELLIDO.exec(texto);
    nombre = [
      partesNombre?.[1]?.trim(),
      primerAp?.[1]?.trim(),
      segundoAp?.[1]?.trim(),
    ]
      .filter(Boolean)
      .join(" ");
  }

  let tipoPersona: "fisica" | "moral" | "" = "";
  if (rfc.length === 13) tipoPersona = "fisica";
  else if (rfc.length === 12) tipoPersona = "moral";

  const cpMatch = RE_CP.exec(texto);
  const domicilioCp = cpMatch ? cpMatch[1] : "";

  const claves = detectarRegimenes(texto);
  const regimen = derivarRegimen(claves);

  if (!rfc && !regimen) {
    return {
      rfc, nombre, tipoPersona, regimen, domicilioCp,
      valido: false,
      error: "No se pudo extraer RFC ni régimen de la constancia",
    };
  }

  return {
    rfc, nombre, tipoPersona, regimen, domicilioCp,
    valido: true, error: "",
  };
}
