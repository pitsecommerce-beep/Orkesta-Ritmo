# Orkesta Ritmo

Herramienta web para preparar declaraciones mensuales de impuestos de contribuyentes mexicanos. Lee CFDI y estados de cuenta, calcula ISR e IVA, y acompaña al contribuyente hasta que presenta en el portal del SAT.

**Ritmo prepara, tu presentas.** El unico acto irreversible lo ejecuta el contribuyente, en el portal oficial, con su propia credencial.

Producto de Orkesta Labs, S.A.P.I. de C.V.

## Regimenes soportados

- RESICO Persona Fisica
- RESICO PF + Sueldos
- Arrendamiento
- Arrendamiento + Sueldos
- RESICO Persona Moral

## Stack

| Componente | Tecnologia |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Backend | Python 3.12, FastAPI |
| Cola | Redis + RQ |
| Base de datos | Supabase (Postgres + RLS + Auth + Storage) |
| Despliegue | Railway |

## Estructura del repositorio

```
/
├── apps/
│   ├── web/                 Next.js frontend
│   └── api/                 FastAPI backend + RQ workers
├── packages/
│   ├── tax-engine/          Motor de calculo (Python puro, sin I/O)
│   ├── cfdi-parser/         Parser de CFDI 4.0, Pagos 2.0, Retenciones 1.1, Nomina 1.2
│   └── bank-parser/         Adaptadores de estados de cuenta por institucion
├── supabase/migrations/     Migraciones de base de datos
├── DECISIONES.md            Decisiones de implementacion
├── PENDIENTES.md            Elementos pendientes
└── SEGURIDAD.md             Modelo de seguridad
```

## Levantar el entorno local

### Requisitos

- Python 3.12+
- Node.js 20+
- Redis
- Cuenta de Supabase (para Auth, DB y Storage)

### 1. Clonar y configurar variables

```bash
git clone <repo-url>
cd Orkesta-Ritmo
cp .env.example .env
# Editar .env con tus credenciales de Supabase y Redis
```

### 2. Backend (API)

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Instalar paquetes locales
pip install -e ../../packages/tax-engine
pip install -e ../../packages/cfdi-parser
pip install -e ../../packages/bank-parser

# Iniciar API
uvicorn app.main:app --reload --port 8000
```

### 3. Worker (procesamiento asincrono)

```bash
cd apps/api
source .venv/bin/activate
rq worker --url $REDIS_URL default
```

### 4. Frontend (Web)

```bash
cd apps/web
npm install
npm run dev
```

### 5. Migraciones de base de datos

Aplicar las migraciones en orden desde `supabase/migrations/` en tu proyecto de Supabase:

1. `00001_initial_schema.sql` - Esquema completo
2. `00002_rls_policies.sql` - Politicas de Row Level Security
3. `00003_seed_data.sql` - Datos semilla (tarifas, cuestionario IVA, demo)

### 6. Ejecutar pruebas

```bash
# Motor de calculo (60 tests)
cd packages/tax-engine && PYTHONPATH=src pytest tests/ -v

# Parser de CFDI (69 tests)
cd packages/cfdi-parser && PYTHONPATH=src pytest tests/ -v

# Parser de banco (70 tests, 8 skipped)
cd packages/bank-parser && PYTHONPATH=src pytest tests/ -v

# API (44 tests)
cd apps/api && PYTHONPATH=. pytest tests/ -v
```

## Despliegue en Railway

El archivo `railway.json` configura tres servicios:

- **web**: Next.js frontend
- **api**: FastAPI backend
- **redis**: Redis 7

Cada servicio tiene su Dockerfile. Las variables de entorno se configuran en el dashboard de Railway.

## Documentacion adicional

- `DECISIONES.md` - Cada decision tecnica y su razonamiento
- `PENDIENTES.md` - Lo que quedo fuera o bloqueado
- `SEGURIDAD.md` - Modelo de amenazas, boveda de e.firma, rotacion de llaves
