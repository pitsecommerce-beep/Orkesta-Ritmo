import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  serverExternalPackages: ["pdf-parse", "pdfjs-dist"],
  outputFileTracingIncludes: {
    "/api/extract-constancia": [
      "./node_modules/pdfjs-dist/legacy/build/pdf.worker.mjs",
    ],
  },
};

export default nextConfig;
