import os, uuid, httpx
from fastapi import FastAPI, UploadFile, File, Query
from typing import List

app  = FastAPI(title="Cloudia Orquestador")
WORK = "/tmp/orch"
os.makedirs(WORK, exist_ok=True)

APISYNC_URL = os.environ.get("APISYNC_URL", "")
APINOTI_URL = os.environ.get("APINOTI_URL", "")

@app.get("/health")
def health():
    return {"status": "ok", "service": "orquestador"}

@app.post("/orquestar/upload-excel")
async def orquestar(
    files:       List[UploadFile] = File(...),
    usuario:     str  = Query(""),
    plataforma:  str  = Query("Colab"),
    fuente:      str  = Query("API"),
    sync_mysql:  bool = Query(True),
    sync_notion: bool = Query(True),
):
    resultados = []

    for file in files:
        if not file.filename.endswith(".xlsx"):
            resultados.append({"archivo": file.filename, "error": "No es .xlsx"})
            continue

        contenido = await file.read()
        resumen = {"archivo": file.filename, "destinos": {}}

        # 1. Extraer el pack
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{APISYNC_URL}/extraer",
                    files={"file": (file.filename, contenido, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                )
            data = r.json()
            if "error" in data:
                resultados.append({"archivo": file.filename, "error": data["error"]})
                continue
            
            # Capturamos el pack y los contadores usando los nuevos identificadores
            pack = data.get("pack", {})
            resumen["id_proy"]         = data.get("id_proy", data.get("id", "unknown"))
            resumen["epicas"]          = data.get("epicas", 0)
            resumen["funcionalidades"] = data.get("funcionalidades", 0)
            
        except Exception as e:
            resultados.append({"archivo": file.filename, "error": f"Extracción falló: {str(e)}"})
            continue

        params = {"usuario": usuario, "plataforma": plataforma, "fuente": fuente}

        # 2. Enviar a MySQL
        if sync_mysql and APISYNC_URL:
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(
                        f"{APISYNC_URL}/sync/desde-pack",
                        json=pack,
                        params=params
                    )
                resumen["destinos"]["mysql"] = r.json()
            except Exception as e:
                # INCORPORADO: Error detallado con endpoint intentado
                resumen["destinos"]["mysql"] = {
                    "status": "error_comunicacion",
                    "detalle": str(e),
                    "endpoint_intentado": f"{APISYNC_URL}/sync/desde-pack"
                }

        # 3. Enviar a Notion
        if sync_notion and APINOTI_URL:
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(
                        f"{APINOTI_URL}/sync/desde-pack",
                        json=pack,
                        params=params
                    )
                resumen["destinos"]["notion"] = r.json()
            except Exception as e:
                # INCORPORADO: Error detallado con endpoint intentado
                resumen["destinos"]["notion"] = {
                    "status": "error_comunicacion",
                    "detalle": str(e),
                    "endpoint_intentado": f"{APINOTI_URL}/sync/desde-pack"
                }

        resultados.append(resumen)

    return {"resultado": resultados}

# ── Endpoint nuevo: crear proyecto ─────────────────────────────
@app.post("/orquestar/crear-proyecto")
async def crear_proyecto(
    id_proy:     str  = Query(...),
    nombre:      str  = Query(...),
    pm:          str  = Query(""),
    squad:       str  = Query(""),
    crear_drive: bool = Query(True),
):
    """
    Crea un proyecto en MySQL + estructura de carpetas en Drive.
    Delega al apisync /proyectos/crear.
    """
    if not APISYNC_URL:
        return {"error": "APISYNC_URL no configurado"}
 
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{APISYNC_URL}/proyectos/crear",
                params={
                    "id_proy":     id_proy,
                    "nombre":      nombre,
                    "pm":          pm,
                    "squad":       squad,
                    "crear_drive": crear_drive,
                }
            )
        return r.json()
    except Exception as e:
        return {"error": f"Error creando proyecto: {str(e)}"}
 
 
# ── Endpoint nuevo: obtener proyecto ───────────────────────────
@app.get("/orquestar/proyecto/{id_proy}")
async def obtener_proyecto(id_proy: str):
    """Consulta el detalle de un proyecto desde apisync."""
    if not APISYNC_URL:
        return {"error": "APISYNC_URL no configurado"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{APISYNC_URL}/proyectos/{id_proy}")
        return r.json()
    except Exception as e:
        return {"error": str(e)}