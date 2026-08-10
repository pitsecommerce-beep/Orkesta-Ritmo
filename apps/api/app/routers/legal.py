from fastapi import APIRouter

router = APIRouter()


@router.get("/privacidad")
async def aviso_privacidad():
    return {
        "titulo": "Aviso de Privacidad Integral",
        "estado": "en_revision",
        "contenido": (
            "Este aviso de privacidad se encuentra en revisión legal para su conformidad "
            "con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares, "
            "cuya autoridad es la Secretaría Anticorrupción y Buen Gobierno.\n\n"
            "Responsable: Orkesta Labs, S.A.P.I. de C.V.\n\n"
            "El documento definitivo será publicado antes del lanzamiento público del servicio."
        ),
    }


@router.get("/terminos")
async def terminos():
    return {
        "titulo": "Términos y Condiciones",
        "estado": "en_revision",
        "contenido": (
            "Estos términos y condiciones se encuentran en revisión legal.\n\n"
            "Orkesta Ritmo es una herramienta de cálculo y preparación de declaraciones fiscales. "
            "No es un despacho contable, no presta servicios de asesoría fiscal profesional "
            "y no sustituye la opinión de un contador público certificado.\n\n"
            "Ritmo prepara, tú presentas. El único acto irreversible — la presentación de la "
            "declaración en el portal del SAT — lo ejecuta el contribuyente con su propia credencial.\n\n"
            "El documento definitivo será publicado antes del lanzamiento público del servicio."
        ),
    }
