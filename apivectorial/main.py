"""
apivectorial/main.py
────────────────────
API dedicada para indexación y búsqueda semántica en Elasticsearch.
Sin LLM — solo chunks. El agente sintetiza.
"""

import os, io, re, time, hashlib
import fitz
from docx import Document as DocxDoc
from fastapi import FastAPI, UploadFile, File, Query
from openai import OpenAI
from elasticsearch import Elasticsearch, helpers
from googleapiclient.discovery import build
from google.oauth2 import service_account
import mysql.connector

app = FastAPI(title="Cloudia Vectorial API")

OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY", "")
ES_URL             = os.environ.get("ES_URL", "")
ES_USER            = os.environ.get("ES_USER", "elastic")
ES_PASSWORD        = os.environ.get("ES_PASSWORD", "")
ES_INDEX           = os.environ.get("ES_INDEX", "proy_lucy")
EMBED_MODEL        = "text-embedding-3-small"
CHUNK_CHARS        = 1600
OVERLAP_CHARS      = 200
DB_CONNECTION_NAME = os.environ.get("DB_CONNECTION_NAME", "")
DB_NAME            = os.environ.get("DB_NAME", "portfolio")
DB_USER_DB         = os.environ.get("DB_USER", "portfolio_app")
DB_PASS            = os.environ.get("DB_PASS", "")
DRIVE_SA_JSON      = os.environ.get("DRIVE_SA_JSON", "service_account.json")

oai = OpenAI(api_key=OPENAI_API_KEY)
es  = Elasticsearch(ES_URL, basic_auth=(ES_USER, ES_PASSWORD))

def _conectar():
    unix_socket = f"/cloudsql/{DB_CONNECTION_NAME}"
    if os.path.exists(unix_socket):
        return mysql.connector.connect(
            unix_socket=unix_socket, user=DB_USER_DB,
            password=DB_PASS, database=DB_NAME, autocommit=False
        )
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user=DB_USER_DB,
        password=DB_PASS, database=DB_NAME, autocommit=False
    )

def _extraer_pdf(contenido: bytes) -> str:
    doc = fitz.open(stream=contenido, filetype="pdf")
    parrafos = []
    for page in doc:
        for b in page.get_text("blocks"):
            texto = b[4].strip()
            if texto and len(texto) > 20:
                parrafos.append(texto)
    return "\n\n".join(parrafos)

def _extraer_docx(contenido: bytes) -> str:
    doc = DocxDoc(io.BytesIO(contenido))
    return "\n\n".join([p.text.strip() for p in doc.paragraphs
                        if p.text.strip() and len(p.text.strip()) > 10])

def _extraer_texto(contenido: bytes, nombre: str) -> str:
    ext = nombre.split(".")[-1].lower()
    if ext == "pdf":  return _extraer_pdf(contenido)
    if ext == "docx": return _extraer_docx(contenido)
    try:              return _extraer_pdf(contenido)
    except:           return ""

def _chunkear(texto: str) -> list:
    parrafos = [p.strip() for p in re.split(r"\n{2,}", texto) if p.strip()]
    chunks, actual = [], ""
    for p in parrafos:
        if len(p) > CHUNK_CHARS:
            for o in re.split(r"(?<=[.!?])\s+", p):
                if len(actual) + len(o) > CHUNK_CHARS and actual:
                    chunks.append(actual.strip())
                    actual = actual[-OVERLAP_CHARS:] + " " + o
                else:
                    actual += " " + o
        else:
            if len(actual) + len(p) > CHUNK_CHARS and actual:
                chunks.append(actual.strip())
                actual = actual[-OVERLAP_CHARS:] + "\n\n" + p
            else:
                actual += "\n\n" + p
    if actual.strip(): chunks.append(actual.strip())
    return [c for c in chunks if len(c) > 50]

def _embeddings(textos: list, batch=20) -> list:
    todos = []
    for i in range(0, len(textos), batch):
        resp = oai.embeddings.create(model=EMBED_MODEL, input=textos[i:i+batch])
        todos.extend([r.embedding for r in resp.data])
        time.sleep(0.1)
    return todos

def _indexar(chunks, embeddings, metadata, nombre, doc_id):
    acciones = [{
        "_index": ES_INDEX, "_id": f"{doc_id}_{i}",
        "_source": {
            "content": chunk, "embedding": vector,
            "metadata": {**metadata, "chunk_index": i,
                         "total_chunks": len(chunks), "file_name": nombre}
        }
    } for i, (chunk, vector) in enumerate(zip(chunks, embeddings))]
    return helpers.bulk(es, acciones, raise_on_error=False)

def _registrar_en_gobernanza_completo(id_proy, id_cat_art, version, nivel, es_vector_id, nombre_archivo, email_autor, chunks_count):
    conn = None
    try:
        conn = _conectar()
        cur  = conn.cursor()

        # 1. Obtener ID Proyecto
        cur.execute("SELECT id FROM proyectos WHERE id_proy = %s", (id_proy,))
        row_p = cur.fetchone()
        if not row_p: return f"Error: Proyecto {id_proy} no existe"
        id_proyecto_db = row_p[0]

        # 2. Obtener ID Artefacto de catálogo
        cur.execute("SELECT id FROM cat_artefactos WHERE id_artefacto = %s", (id_cat_art,))
        row_a = cur.fetchone()
        if not row_a: return f"Error: Artefacto {id_cat_art} no existe"
        id_cat_art_db = row_a[0]

        # 3. Manejar Usuario Autor
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email_autor,))
        row_u = cur.fetchone()
        if not row_u:
            cur.execute("INSERT INTO usuarios (email, nombre, rol) VALUES (%s, %s, 'editor')", 
                        (email_autor, email_autor.split("@")[0]))
            id_autor_db = cur.lastrowid
        else:
            id_autor_db = row_u[0]

        # 4. Marcar versiones anteriores como no latest
        cur.execute("""
            UPDATE documentos_gobernanza 
            SET is_latest = 0 
            WHERE id_proyecto = %s AND id_cat_artefacto = %s
        """, (id_proyecto_db, id_cat_art_db))

        # 5. Insertar en documentos_gobernanza
        cur.execute("""
            INSERT INTO documentos_gobernanza (
                id_proyecto, id_cat_artefacto, mai_art_id, nivel_confianza, version,
                id_autor, id_elastic_vector, url_documento, fase, etapa, is_latest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Delivery', '4_OFFICIAL_VALIDATED', 1)
        """, (id_proyecto_db, id_cat_art_db, id_cat_art, nivel, version, id_autor_db, es_vector_id, nombre_archivo))
        id_doc_new = cur.lastrowid

        # 6. Actualizar mai_artefactos
        cur.execute("""
            UPDATE mai_artefactos SET es_indexado=1, es_vector_id=%s, es_indexado_en=NOW()
            WHERE art_id=%s
        """, (es_vector_id, id_cat_art))

        # 7. Changelog
        cur.execute("""
            INSERT INTO changelog (tabla, registro_id, campo, valor_nuevo, cambiado_por, fuente)
            VALUES ('documentos_gobernanza', %s, 'ingesta', %s, %s, 'Agente')
        """, (str(id_doc_new), f"Indexado en ES ({chunks_count} chunks)", email_autor))

        conn.commit()
        return "OK"
    except Exception as e:
        if conn: conn.rollback()
        return str(e)
    finally:
        if conn: conn.close()

# Actualizamos el endpoint /indexar para que use esta función
@app.post("/indexar")
async def indexar(
    file:     UploadFile = File(...),
    id_proy:  str  = Query(...),
    art_id:   str  = Query(...), # Ahora lo pedimos obligatorio
    nivel:    int  = Query(4),
    version:  str  = Query("1.0"),
    autor:    str  = Query("Agente"),
):
    contenido = await file.read()
    nombre    = file.filename
    texto     = _extraer_texto(contenido, nombre)
    
    if not texto or len(texto) < 100:
        return {"error": "Texto insuficiente para indexar"}

    chunks     = _chunkear(texto)
    embeddings = _embeddings(chunks)
    
    # ID único basado en tu lógica de la Celda 7
    doc_id = hashlib.md5(f"{id_proy}-{art_id}-{nombre}".encode()).hexdigest()[:12]
    
    metadata = {
        "id_proy": id_proy, "artifact_id": art_id,
        "nivel_confianza": nivel, "status_gobierno": "OFFICIAL_VALIDATED",
        "is_latest": True, "version": version, "file_name": nombre
    }

    exito, errores = _indexar(chunks, embeddings, metadata, nombre, doc_id)
    
    # Ejecutamos toda la lógica de tus Celdas en MySQL
    res_db = _registrar_en_gobernanza_completo(id_proy, art_id, version, nivel, doc_id, nombre, autor, len(chunks))

    return {
        "status": "completado" if res_db == "OK" else "error_db",
        "mysql_log": res_db,
        "chunks": len(chunks),
        "vector_id": doc_id
    }

def _drive_service():
    creds = service_account.Credentials.from_service_account_file(
        DRIVE_SA_JSON, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def _descargar_drive(file_id: str, mime_type: str) -> bytes:
    service = _drive_service()
    if mime_type == "application/vnd.google-apps.document":
        req = service.files().export_media(fileId=file_id, mimeType="application/pdf")
    else:
        req = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    from googleapiclient.http import MediaIoBaseDownload
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done: _, done = dl.next_chunk()
    return buf.getvalue()

# ── ENDPOINTS ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "es_version": es.info()["version"]["number"]}



@app.post("/indexar/drive")
async def indexar_drive(
    drive_file_id:  str  = Query(...),
    drive_mime:     str  = Query("application/pdf"),
    nombre_archivo: str  = Query("documento.pdf"),
    id_proy:        str  = Query(...),
    art_id:         str  = Query(""),
    nivel:          int  = Query(4),
    version:        str  = Query("1.0"),
    area:           str  = Query("Operations"),
    autor:          str  = Query(""),
    actualizar_mysql: bool = Query(True),
):
    """Descarga de Drive e indexa en ES."""
    try:
        contenido = _descargar_drive(drive_file_id, drive_mime)
    except Exception as e:
        return {"error": f"Error descargando Drive: {str(e)}"}
    texto = _extraer_texto(contenido, nombre_archivo)
    if not texto or len(texto) < 100:
        return {"error": "No se pudo extraer texto"}
    chunks     = _chunkear(texto)
    embeddings = _embeddings(chunks)
    doc_id     = hashlib.md5(f"{id_proy}-{art_id}-{drive_file_id}".encode()).hexdigest()[:12]
    metadata   = {
        "id_proy": id_proy, "artifact_id": art_id or nombre_archivo.split("_")[0],
        "nivel_confianza": nivel, "status_gobierno": "OFFICIAL_VALIDATED",
        "is_latest": True, "version": version,
        "area_negocio": area, "responsable_validacion": autor,
        "drive_id": drive_file_id,
    }
    exito, errores = _indexar(chunks, embeddings, metadata, nombre_archivo, doc_id)
    if actualizar_mysql and art_id:
        _actualizar_mysql(art_id, doc_id)
    return {"archivo": nombre_archivo, "id_proy": id_proy, "art_id": art_id,
            "drive_id": drive_file_id, "chunks": len(chunks),
            "indexados": exito, "errores": len(errores), "vector_id": doc_id}


@app.get("/buscar")
async def buscar(
    q:         str = Query(...),
    id_proy:   str = Query(None),
    nivel_min: int = Query(3),
    k:         int = Query(5),
):
    """Búsqueda semántica — devuelve chunks crudos. El agente sintetiza."""
    try:
        vector  = oai.embeddings.create(model=EMBED_MODEL, input=[q]).data[0].embedding
    except Exception as e:
        return {"error": f"Error generando embedding: {str(e)}"}

    filtros = [
        {"term":  {"metadata.is_latest": True}},
        {"range": {"metadata.nivel_confianza": {"gte": nivel_min}}},
    ]
    if id_proy:
        filtros.append({"term": {"metadata.id_proy": id_proy}})

    resp = es.search(index=ES_INDEX, body={
        "knn": {
            "field": "embedding", "query_vector": vector,
            "k": k, "num_candidates": k * 5,
            "filter": {"bool": {"must": filtros}},
        },
        "_source": ["content", "metadata"],
    })

    hits = resp["hits"]["hits"]
    if not hits:
        return {"query": q, "chunks": [], "fuente": None,
                "contexto": "No se encontró información relevante."}

    contexto = "\n\n".join([h["_source"]["content"] for h in hits])
    fuente   = (f"{hits[0]['_source']['metadata'].get('id_proy','N/A')} / "
                f"{hits[0]['_source']['metadata'].get('artifact_id','N/A')}")

    return {
        "query":    q,
        "fuente":   fuente,
        "contexto": contexto,
        "chunks":   [{"score": round(h["_score"], 4),
                      "texto": h["_source"]["content"][:300]}
                     for h in hits],
    }


@app.delete("/eliminar")
async def eliminar(id_proy: str = Query(...), art_id: str = Query(None)):
    """Elimina chunks de un proyecto/artefacto de ES."""
    must = [{"term": {"metadata.id_proy": id_proy}}]
    if art_id:
        must.append({"term": {"metadata.artifact_id": art_id}})
    resp = es.delete_by_query(index=ES_INDEX, body={"query": {"bool": {"must": must}}})
    return {"eliminados": resp.get("deleted", 0), "id_proy": id_proy, "art_id": art_id}


@app.get("/estado")
async def estado(id_proy: str = Query(None)):
    """Lista artefactos indexados en ES."""
    must = [{"term": {"metadata.is_latest": True}}]
    if id_proy:
        must.append({"term": {"metadata.id_proy": id_proy}})
    resp = es.search(index=ES_INDEX, body={
        "query": {"bool": {"must": must}},
        "aggs": {
            "por_proyecto": {
                "terms": {"field": "metadata.id_proy", "size": 50},
                "aggs": {"por_artefacto": {"terms": {"field": "metadata.artifact_id", "size": 20}}}
            }
        },
        "size": 0
    })
    resultado = []
    for proy in resp["aggregations"]["por_proyecto"]["buckets"]:
        for art in proy["por_artefacto"]["buckets"]:
            resultado.append({"id_proy": proy["key"], "art_id": art["key"],
                               "chunks": art["doc_count"]})
    return {"indexados": resultado, "total": len(resultado)}