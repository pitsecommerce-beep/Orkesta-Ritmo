"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  Upload,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  FolderOpen,
  Loader2,
  ArrowRight,
  Building2,
  Calculator,
  Receipt,
  FileUp,
  Trash2,
} from "lucide-react";
import { createClient } from "@/lib/supabase";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { useTenant } from "@/hooks/use-tenant";
import { usePermissions } from "@/hooks/use-permissions";

const ALLOWED_EXTENSIONS: Record<string, string[]> = {
  cfdi: [".xml"],
  extracto: [".csv", ".xlsx"],
  constancia: [".pdf"],
  otro: [".pdf", ".xml", ".csv", ".xlsx"],
};

interface DocRow {
  id: string;
  nombre_archivo: string;
  tipo: string;
  estado: string;
  created_at: string;
  tamano_bytes: number | null;
}

const MOCK_DOCS: DocRow[] = [
  { id: "1", nombre_archivo: "cfdi_enero_01.xml", tipo: "CFDI", estado: "validado", created_at: "2025-01-15T00:00:00", tamano_bytes: 12288 },
  { id: "2", nombre_archivo: "cfdi_enero_02.xml", tipo: "CFDI", estado: "validado", created_at: "2025-01-20T00:00:00", tamano_bytes: 8192 },
  { id: "3", nombre_archivo: "nomina_enero.xml", tipo: "Nomina", estado: "validado", created_at: "2025-01-31T00:00:00", tamano_bytes: 15360 },
  { id: "4", nombre_archivo: "extracto_bbva_ene.csv", tipo: "Extracto", estado: "recibido", created_at: "2025-02-01T00:00:00", tamano_bytes: 46080 },
  { id: "5", nombre_archivo: "constancia_situacion.pdf", tipo: "constancia_situacion_fiscal", estado: "validado", created_at: "2025-01-05T00:00:00", tamano_bytes: 102400 },
];

const STATUS_MAP: Record<string, { label: string; icon: typeof CheckCircle; color: string }> = {
  validado: { label: "Procesado", icon: CheckCircle, color: "text-green-600" },
  recibido: { label: "Pendiente", icon: Clock, color: "text-yellow-600" },
  procesando: { label: "Procesando", icon: Loader2, color: "text-blue-600" },
  con_error: { label: "Error", icon: AlertCircle, color: "text-red-600" },
};

function formatBytes(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

const PROCESS_STEPS = [
  {
    num: 0,
    title: "Sube tu constancia",
    description: "PDF de la Constancia de Situación Fiscal del SAT. Tu régimen se detecta automáticamente.",
    icon: FileUp,
    docType: "constancia" as const,
  },
  {
    num: 1,
    title: "Sube tus CFDIs",
    description: "Archivos XML de tus comprobantes fiscales emitidos y recibidos.",
    icon: FileText,
    docType: "cfdi" as const,
  },
  {
    num: 2,
    title: "Sube extractos bancarios",
    description: "Estados de cuenta en CSV o XLSX para conciliar con tus CFDIs.",
    icon: Building2,
    docType: "extracto" as const,
  },
  {
    num: 3,
    title: "Calcula tu declaración",
    description: "Revisa tus periodos y ejecuta el cálculo fiscal.",
    icon: Calculator,
    docType: null,
  },
  {
    num: 4,
    title: "Presenta en el SAT",
    description: "Descarga tu pre-declaración y preséntala en el portal del SAT.",
    icon: Receipt,
    docType: null,
  },
];

export default function DocumentosPage() {
  const { demoMode } = useDemoMode();
  const { tenant, loading: tenantLoading } = useTenant();
  const { canUpload, canDelete } = usePermissions();
  const [docs, setDocs] = useState<DocRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (demoMode) {
      setDocs(MOCK_DOCS);
      setLoading(false);
      return;
    }

    setDocs([]);
    setLoading(true);

    if (tenantLoading) return;

    async function load() {
      if (!tenant) { setLoading(false); return; }

      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data } = await supabase
        .from("documentos")
        .select("id, nombre_archivo, tipo, estado, created_at, tamano_bytes")
        .eq("tenant_id", tenant.tenantId)
        .order("created_at", { ascending: false })
        .limit(100);

      setDocs((data ?? []) as DocRow[]);
      setLoading(false);
    }
    load();
  }, [demoMode, tenant, tenantLoading]);

  function validateFile(file: File, docType: string | null): string | null {
    if (file.size > 10 * 1024 * 1024) {
      return `El archivo "${file.name}" excede el límite de 10 MB.`;
    }

    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    const allowed = docType
      ? ALLOWED_EXTENSIONS[docType] ?? []
      : [...ALLOWED_EXTENSIONS.cfdi, ...ALLOWED_EXTENSIONS.extracto, ...ALLOWED_EXTENSIONS.constancia];

    if (!allowed.includes(ext)) {
      const tipoLabel = docType === "cfdi" ? "CFDIs" : docType === "extracto" ? "extractos" : docType === "constancia" ? "constancias" : "documentos";
      return `"${file.name}" no es un formato válido para ${tipoLabel}. Formatos aceptados: ${allowed.join(", ")}`;
    }

    return null;
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    setUploadError(null);

    if (!canUpload) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    const activeDocType = activeStep !== null
      ? PROCESS_STEPS.find(s => s.num === activeStep)?.docType ?? null
      : null;

    for (const file of files) {
      const error = validateFile(file, activeDocType);
      if (error) {
        setUploadError(error);
        return;
      }
    }
  }, [canUpload, activeStep]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0) return;

    const activeDocType = activeStep !== null
      ? PROCESS_STEPS.find(s => s.num === activeStep)?.docType ?? null
      : null;

    for (const file of files) {
      const error = validateFile(file, activeDocType);
      if (error) {
        setUploadError(error);
        return;
      }
    }
  }, [activeStep]);

  const cfdisCount = docs.filter(d => d.tipo === "CFDI" || d.tipo === "Nomina").length;
  const extractosCount = docs.filter(d => d.tipo === "Extracto").length;
  const constanciaCount = docs.filter(d => d.tipo === "constancia_situacion_fiscal").length;
  const allProcessed = docs.length > 0 && docs.every(d => d.estado === "validado");

  function getStepStatus(stepNum: number): "done" | "active" | "pending" {
    if (stepNum === 0 && constanciaCount > 0) return "done";
    if (stepNum === 1 && cfdisCount > 0) return "done";
    if (stepNum === 2 && extractosCount > 0) return "done";
    if (stepNum === 0) return "active";
    if (stepNum === 1 && constanciaCount > 0) return "active";
    if (stepNum === 2 && cfdisCount > 0) return "active";
    if (stepNum === 3 && cfdisCount > 0 && allProcessed) return "active";
    if (stepNum === 4 && allProcessed) return "active";
    return "pending";
  }

  const activeDocType = activeStep !== null
    ? PROCESS_STEPS.find(s => s.num === activeStep)?.docType ?? null
    : null;

  const extensions = activeDocType
    ? ALLOWED_EXTENSIONS[activeDocType]
    : [...ALLOWED_EXTENSIONS.cfdi, ...ALLOWED_EXTENSIONS.extracto, ...ALLOWED_EXTENSIONS.constancia];

  const acceptAttr = [...new Set(extensions)].join(",");

  const uploadLabel = activeDocType === "cfdi"
    ? "Sube tus CFDIs (XML)"
    : activeDocType === "extracto"
      ? "Sube tu estado de cuenta (CSV / XLSX)"
      : activeDocType === "constancia"
        ? "Sube tu Constancia de Situación Fiscal (PDF)"
        : "Arrastra tus archivos aquí";

  const showUploadZone = activeStep !== null
    ? PROCESS_STEPS.find(s => s.num === activeStep)?.docType !== null
    : true;

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">Documentos</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sigue estos pasos para preparar tu declaración fiscal.
        </p>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5 animate-fade-in-up stagger-1">
        {PROCESS_STEPS.map((step) => {
          const status = getStepStatus(step.num);
          const isUploadStep = step.docType !== null;
          const isActive = activeStep === step.num;

          return (
            <button
              key={step.num}
              type="button"
              onClick={() => {
                if (isUploadStep) {
                  setActiveStep(isActive ? null : step.num);
                  setUploadError(null);
                } else if (step.num === 3) {
                  window.location.href = "/dashboard/periodos";
                }
              }}
              className={`relative rounded-lg border p-4 text-left transition-all ${
                isActive
                  ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5 ring-1 ring-[var(--color-azul)]"
                  : status === "done"
                    ? "border-green-200 bg-green-50"
                    : "hover:border-muted-foreground/30"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                  status === "done"
                    ? "bg-green-100 text-green-700"
                    : isActive
                      ? "bg-[var(--color-azul)] text-white"
                      : "bg-muted text-muted-foreground"
                }`}>
                  {status === "done" ? <CheckCircle className="h-3.5 w-3.5" /> : step.num + 1}
                </div>
                <step.icon className={`h-4 w-4 ${
                  status === "done" ? "text-green-600" : isActive ? "text-[var(--color-azul)]" : "text-muted-foreground"
                }`} />
              </div>
              <p className="font-medium text-sm">{step.title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{step.description}</p>
              {isUploadStep && status === "done" && (
                <Badge className="mt-2 bg-green-100 text-green-700">
                  {step.num === 0 ? `${constanciaCount} archivo${constanciaCount !== 1 ? "s" : ""}`
                    : step.num === 1 ? `${cfdisCount} archivos`
                    : `${extractosCount} archivos`}
                </Badge>
              )}
            </button>
          );
        })}
      </div>

      {showUploadZone && (activeStep === null || activeDocType !== null) && (
        <Card className="mt-6 animate-fade-in-up stagger-2">
          <CardContent className="pt-6">
            {canUpload ? (
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
                  dragOver ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5" : "border-muted-foreground/25"
                }`}
              >
                <Upload className="h-8 w-8 text-muted-foreground" />
                <p className="mt-3 font-heading font-semibold">{uploadLabel}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  o haz clic para seleccionar
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Formatos: {[...new Set(extensions)].join(", ")} &mdash; Máximo 10 MB
                </p>
                <Button
                  variant="outline"
                  className="mt-4 gap-2"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-4 w-4" /> Seleccionar archivos
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={acceptAttr}
                  multiple
                  className="hidden"
                  onChange={handleFileSelect}
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/15 bg-muted/30 p-10 text-center">
                <Upload className="h-8 w-8 text-muted-foreground/40" />
                <p className="mt-3 font-heading font-semibold text-muted-foreground">
                  Carga de archivos no disponible
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Tu rol de lectura no permite subir documentos. Contacta al propietario del workspace.
                </p>
              </div>
            )}
            {uploadError && (
              <div className="mt-3 flex items-start gap-2 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeStep !== null && PROCESS_STEPS.find(s => s.num === activeStep)?.docType === null && activeStep === 3 && (
        <Card className="mt-6 animate-fade-in-up">
          <CardContent className="flex flex-col items-center py-10 text-center">
            <Calculator className="h-10 w-10 text-[var(--color-azul)]" />
            <p className="mt-4 font-heading font-semibold">Listo para calcular</p>
            <p className="mt-1 text-sm text-muted-foreground max-w-sm">
              Tus documentos están procesados. Ve a Periodos para ejecutar el cálculo fiscal y generar tu declaración.
            </p>
            <Link href="/dashboard/periodos">
              <Button className="mt-4 gap-2">
                Ir a Periodos <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      <Card className="mt-6 animate-fade-in-up stagger-4">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-heading text-lg">Archivos subidos</CardTitle>
          {!loading && docs.length > 0 && (
            <Badge variant="outline">{docs.length} archivos</Badge>
          )}
        </CardHeader>
        <CardContent>
          {loading || tenantLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : docs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Archivo</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead className="text-right">Tamaño</TableHead>
                    {canDelete && <TableHead className="w-10"></TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {docs.map((doc) => {
                    const st = STATUS_MAP[doc.estado] ?? STATUS_MAP.recibido;
                    return (
                      <TableRow key={doc.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">{doc.nombre_archivo}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {doc.tipo === "constancia_situacion_fiscal" ? "Constancia" : doc.tipo}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <st.icon className={`h-4 w-4 ${st.color}`} />
                            <span className="text-sm">{st.label}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {doc.created_at.split("T")[0]}
                        </TableCell>
                        <TableCell className="text-right text-sm text-muted-foreground">
                          {formatBytes(doc.tamano_bytes)}
                        </TableCell>
                        {canDelete && (
                          <TableCell>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-muted-foreground hover:text-red-600">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Eliminar archivo</TooltipContent>
                            </Tooltip>
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="h-10 w-10 text-muted-foreground/40" />
              <p className="mt-3 text-sm text-muted-foreground">No hay documentos subidos</p>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                Selecciona un paso arriba para comenzar a subir archivos.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
