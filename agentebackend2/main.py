import os
import json
import requests
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage 
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


app = Flask(__name__)

# ════════════════════════════════════════════════════
# 1. CONFIGURACIÓN Y VARIABLES DE ENTORNO
# ════════════════════════════════════════════════════
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")          

APISYNC_URL       = os.getenv("APISYNC_URL")
APINOTION_URL     = os.getenv("APINOTION_URL")
ORQUESTADOR_URL   = os.getenv("ORQUESTADOR_URL")
APIVECTORIAL_URL  = os.getenv("APIVECTORIAL_URL")

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
_FMT = "txt"

checkpointer = MemorySaver()

# ════════════════════════════════════════════════════
# 2. UTILIDADES
# ════════════════════════════════════════════════════
def _get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=30)
        return r.text if r.status_code == 200 else f"Error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Error: {str(e)}"

def _ajustar_fechas_peru(data):
    if isinstance(data, str):
        try: data = json.loads(data)
        except: return data
    if not isinstance(data, list): data = [data] if isinstance(data, dict) else []
    cols = ["fecha_sync", "ult_act", "fecha_inicio", "fecha_fin", "actualizado_en"]
    for fila in data:
        for col in cols:
            if col in fila and fila[col]:
                try:
                    dt = datetime.strptime(str(fila[col]), "%Y-%m-%d %H:%M:%S")
                    fila[col] = (dt - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")
                except: continue
    return json.dumps(data, ensure_ascii=False, default=str)

# ════════════════════════════════════════════════════
# 3. HERRAMIENTAS (sin cambios)
# ════════════════════════════════════════════════════

@tool
def tool_proyectos():
    """Obtiene una lista de todos los proyectos activos en el portfolio"""
    return f"REPORTE_DIRECTO:\n{_get(f'{APINOTION_URL}/proyectos', params={'fmt': _FMT})}"

@tool
def tool_proyecto(id_proy: str, show_subs: bool = False):
    """Obtiene el detalle de un proyecto específico y su épica actual usando su ID (ej. PROY-001)."""
    id_norm = re.sub(r'([A-Z]+)(\d+)', r'\1-\2', id_proy.upper().replace('-',''))
    res = _get(f"{APINOTION_URL}/proyecto/{id_proy.upper()}", params={"fmt": _FMT, "show_subs": str(show_subs).lower()})
    if "404" in res or "no encontrado" in res.lower():
        res = _get(f"{APINOTION_URL}/proyecto/{id_norm}", params={"fmt": _FMT, "show_subs": str(show_subs).lower()})
    return f"REPORTE_DIRECTO:\n{res}"

@tool
def tool_epicas(id_proy: str):
    """Lista todas las épicas asociadas a un ID de proyecto específico."""
    return f"REPORTE_DIRECTO:\n{_get(f'{APINOTION_URL}/proyecto/{id_proy}/epicas', params={'fmt': _FMT})}"

@tool
def tool_epica_detalle(id_proy: str, orden: int, show_subs: bool = False):
    """Obtiene el detalle completo de una épica específica de un proyecto mediante su número de orden."""
    return f"REPORTE_DIRECTO:\n{_get(f'{APINOTION_URL}/proyecto/{id_proy}/epica/{orden}', params={'fmt': _FMT, 'show_subs': str(show_subs).lower()})}"

@tool
def tool_sync_log(limit: int = 10):
    """Muestra el historial de las últimas sincronizaciones realizadas en el sistema."""
    res = _get(f"{APISYNC_URL}/sync-log", params={"limite": limit})
    try:
        data = json.loads(res)
        return _ajustar_fechas_peru(data.get("logs", data.get("sync_log", [])))
    except: return res

@tool
def tool_extraer_excel(archivo_path: str):
    """Previsualiza el contenido de un archivo Excel sin llegar a sincronizarlo en la base de datos."""
    if not os.path.exists(archivo_path): return f"Error: No existe el archivo {archivo_path}"
    try:
        with open(archivo_path, "rb") as f:
            r = requests.post(f"{APISYNC_URL}/extraer", files={"file": f}, timeout=60)
        return json.dumps(r.json(), ensure_ascii=False, indent=2)
    except Exception as e: return f"Error Extraer: {str(e)}"

@tool
def tool_sync_excel(archivo_path: str):
    """Sincroniza y sube los datos de un archivo Excel a las bases de datos de MySQL y Notion."""
    if not os.path.exists(archivo_path): return f"Error: No existe el archivo {archivo_path}"
    try:
        with open(archivo_path, "rb") as f:
            r = requests.post(f"{ORQUESTADOR_URL}/orquestar/upload-excel",
                files={"files": (os.path.basename(archivo_path), f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                params={"usuario": "agente", "plataforma": "WebApp", "sync_mysql": True, "sync_notion": True}, timeout=600)
        return json.dumps(r.json(), ensure_ascii=False, indent=2) if r.status_code == 200 else r.text
    except Exception as e: return f"Error Sync: {str(e)}"

@tool
def tool_sync_carpeta():
    """Inicia la sincronización masiva de todos los archivos dentro de una carpeta (No habilitado en Cloud)."""
    return "La sincronización masiva de carpetas no está habilitada en el entorno Cloud."

@tool
def tool_consulta_vectorial(query: str) -> str:
    """Consulta la base de conocimientos RAG para obtener información técnica, manuales o flujos de procesos."""
    try:
        r = requests.get(f"{APIVECTORIAL_URL}/buscar", params={"q": query, "k": 5}, timeout=30)
        data = r.json()
        if not data.get("chunks"):
            return "No se encontró información relevante en la base vectorial."
        contexto = data.get("contexto", "")
        fuente   = data.get("fuente", "N/A")
        return f"{contexto}\n\n_(Fuente: {fuente})_"
    except Exception as e:
        return f"Error RAG: {str(e)}"

@tool
def tool_crear_proyecto(id_proy: str, nombre: str, pm: str = "", squad: str = "") -> str:
    """Crea un nuevo proyecto o actualiza uno existente tanto en la base de datos MySQL como en Google Drive."""
    try:
        r = requests.post(
            f"{ORQUESTADOR_URL}/orquestar/crear-proyecto",
            params={"id_proy": id_proy, "nombre": nombre, "pm": pm, "squad": squad, "crear_drive": True},
            timeout=60
        )
        data = r.json()
        if data.get("error"): return f"Error: {data['error']}"
        mysql  = data.get("mysql", {})
        drive  = data.get("drive", {})
        folder = data.get("drive_folder_id", "N/A")
        return (
            f"✅ Proyecto {id_proy} creado correctamente.\n"
            f"MySQL: {mysql.get('estado', 'ok')} (id={mysql.get('id')})\n"
            f"Drive: {drive.get('estado', 'ok')} (folder_id={folder})\n"
            f"URL Drive: https://drive.google.com/drive/folders/{folder}"
        )
    except Exception as e:
        return f"Error creando proyecto: {str(e)}"

@tool
def tool_ingestar_gobernanza(archivo_path: str, id_proy: str, id_cat_art: str):
    """
    Sube un documento a la base vectorial y registra su GOBERNANZA oficial en MySQL.
    Requiere el ID del proyecto (ej. PROY-002) y el ID del artefacto (ej. ART-OPS-RUN-001).
    Usa esto cuando el usuario diga 'sincroniza este manual/PDF/archivo'.
    """
    try:
        url_vectorial = f"{APIVECTORIAL_URL}/indexar"
        params = {
            "id_proy": id_proy.upper(),
            "art_id": id_cat_art.upper(),
            "autor": "lcruzh0002@gmail.com", # O el email que venga en el mensaje
            "version": "1.0"
        }
        
        with open(archivo_path, "rb") as f:
            r = requests.post(url_vectorial, params=params, files={"file": f}, timeout=180)
            
        if r.status_code == 200:
            data = r.json()
            return f"✅ Gobernanza Completa: Documento indexado ({data['chunks']} chunks) y registrado en MySQL con VectorID {data['vector_id']}."
        return f"❌ Error en API Vectorial: {r.text}"
    except Exception as e:
        return f"Error crítico: {str(e)}"

tools_finales = [
    tool_proyectos, tool_proyecto, tool_epicas, tool_epica_detalle,
    tool_sync_log, tool_extraer_excel, tool_sync_excel,
    tool_sync_carpeta, tool_consulta_vectorial, tool_crear_proyecto,tool_ingestar_gobernanza
]

# ════════════════════════════════════════════════════
# 4. PROMPT DEL SISTEMA (sin cambios)
# ════════════════════════════════════════════════════
instrucciones_maestras = """Sos un asistente experto en el portfolio de proyectos.
El usuario puede venir identificado como [Usuario: email] al inicio del mensaje — úsalo para personalizar.

HERRAMIENTAS:
- tool_proyectos → lista todos los proyectos activos
- tool_proyecto(id_proy, show_subs) → detalle de un proyecto con épica actual
- tool_epicas(id_proy) → todas las épicas de un proyecto
- tool_epica_detalle(id_proy, orden, show_subs) → detalle completo de una épica
- tool_sync_log(limit) → historial de sincronizaciones
- tool_extraer_excel(archivo) → previsualiza Excel sin sincronizar
- tool_sync_excel(archivo_path) → sincroniza un Excel a MySQL y Notion
- tool_consulta_vectorial(query) → consulta documentos OFFICIAL indexados en la base vectorial. Usar cuando pregunten sobre: requerimientos, manuales, runbooks, specs técnicas, cómo funciona un sistema, controles operativos, flujos de proceso.
- tool_crear_proyecto(id_proy, nombre, pm, squad) → crea O ACTUALIZA proyecto en MySQL + Drive. Puede q exista en bd pero no en Drive o viceversa, debemos asegurarnos de crear.

NUEVA HERRAMIENTA CRÍTICA:
- tool_ingestar_gobernanza(archivo_path, id_proy, id_cat_art) → Sincroniza, indexa y registra OFICIALMENTE la gobernanza de un PDF/DOCX en Elasticsearch y MySQL. Es el paso final para que un documento sea "OFFICIAL_VALIDATED".


REGLAS DE GOBERNANZA (Subida de archivos):
1. Si el usuario sube un archivo y pide "sincronizar", "indexar", "subir" o "guardar en gobernanza":
   - DEBES identificar el ID_PROY (ej. PROY-002) y el ID_CAT_ART (ej. ART-OPS-RUN-001).
   - Si el usuario NO proporciona estos IDs en su mensaje, NO ejecutes la herramienta. Pídelos amablemente: "Para registrar la gobernanza, por favor indícame el ID del proyecto y el ID del artefacto".
   - Una vez tengas ambos, llama a tool_ingestar_gobernanza.

REGLAS:
1. Para listar proyectos → tool_proyectos
2. Para detalle técnico (épicas, avance, %) → tool_proyecto NUNCA uses tool_proyecto cuando pregunten "de qué trata", "qué hace", "cómo funciona", "qué incluye" → eso es SIEMPRE tool_consulta_vectorial
3. Para ver épicas → tool_epicas
4. Para detalle de épica específica → tool_epica_detalle
5. show_subs=True solo cuando pidan subfuncionalidades o detalles internos
6. Para sincronizar → usa tool_sync_excel(archivo_path) directamente sin preguntar
7. Fechas en GMT-5 (Perú)
8. IDs siempre en mayúsculas (ejemplo PRIT-0013, PROY-001)
9. Si no encuentras un proyecto en Notion → intenta variantes del ID: PROY001 → PROY-001
10. Si el usuario pregunta de qué trata un sistema o pide requerimientos → USA tool_consulta_vectorial.
11. Para crear proyecto → llama tool_crear_proyecto directamente sin verificar.
    El sistema maneja automáticamente si ya existe (actualiza) o es nuevo (crea).
    Solo confirma al usuario el resultado que devuelva la tool.
12. tool_consulta_vectorial devuelve contexto crudo — sintetízalo en lenguaje natural y siempre indica la fuente al final.

FORMATO DE RESPUESTA:
- Cuando el resultado venga con REPORTE_DIRECTO:, cópiala exactamente sin modificar ningún carácter.
- No envuelvas reportes en bloques de código adicionales.

PRIORIDAD:
- Ingesta oficial de documentos técnicos → tool_ingestar_gobernanza.
- "de qué trata X" / "qué hace X" / "cómo funciona X" → tool_consulta_vectorial SIEMPRE
- "estado de X" / "épicas de X" / "avance de X" → tool_proyecto
"""

# ════════════════════════════════════════════════════
# 5. ENDPOINT PRINCIPAL
# ════════════════════════════════════════════════════

@app.route('/agent', methods=['POST'])
def main_agent():
    msg     = request.form.get('msg') or request.json.get('msg', '')
    id_hilo = request.form.get('idagente') or request.json.get('idagente', 'user_01')
    email   = request.form.get('email', 'anonimo')
    archivo = request.files.get('archivo')

    if not msg:
        return jsonify({"error": "No se recibió ningún mensaje (msg)"}), 400

    path_a = None
    if archivo:
        path_a = os.path.join(UPLOAD_DIR, archivo.filename)
        archivo.save(path_a)

    ctx = f"[Usuario: {email}] " + (f"[Archivo subido: {path_a}] " if path_a else "") + msg

    try:
        # === Fallback con los tres modelos ===
        llm_openai = ChatOpenAI(
            model="gpt-4o",
            api_key=OPENAI_API_KEY,
            temperature=0
        )
        llm_anthropic = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",  # ← nota: este snapshot ya está obsoleto en 2026
            api_key=ANTHROPIC_API_KEY,
            temperature=0
        )
        llm_gemini = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )

        model_con_fallbacks  = llm_openai.with_fallbacks([llm_anthropic, llm_gemini])

        # Agente
        agent = create_react_agent(
            model=model_con_fallbacks ,
            #model=llm_openai,
            tools=tools_finales,
            #state_modifier=instrucciones_maestras,
            #messages_modifier=instrucciones_maestras,
            checkpointer=checkpointer,
        )

        config = {"configurable": {"thread_id": id_hilo}}

        final_response = ""
        reporte_raw = None

        for chunk in agent.stream(
            {"messages": [
                 SystemMessage(content=instrucciones_maestras),
                 HumanMessage(content=ctx)
                 ]},
            config,
            stream_mode="values"
        ):
            last_msg = chunk["messages"][-1]
            if last_msg.type == "tool":
                content_str = str(last_msg.content)
                if "REPORTE_DIRECTO:" in content_str:
                    reporte_raw = content_str
            final_response = last_msg.content

        respuesta_final = reporte_raw if reporte_raw else final_response

        if path_a and os.path.exists(path_a):
            os.remove(path_a)

        return jsonify({
            "respuesta": respuesta_final,
            "idagente": id_hilo,
            "es_reporte": "REPORTE_DIRECTO:" in (respuesta_final or "")
        })

    except Exception as e:
        print(f"Error detectado: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)