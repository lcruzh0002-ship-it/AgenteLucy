
---

# **DOSSIER DE PROYECTO: PORTFOLIO-CORE v1.0**
### *“The Intelligent Knowledge Agent: Arquitectura de Gobernanza y Resiliencia”*

---

## **1. VISIÓN GENERAL: EL CONCEPTO (Nivel No Técnico)**
**Portfolio-CORE** no es simplemente un chatbot; es un **Asistente Ejecutivo de Élite** para la gestión de proyectos. Imagine que su empresa tiene miles de documentos dispersos en Google Drive, tableros en Notion y registros en Excel. Portfolio-CORE actúa como el cerebro central que:
1.  **Valida:** Asegura que solo la información "Oficial" sea consultable.
2.  **Sincroniza:** Mueve los datos entre plataformas automáticamente.
3.  **Responde:** Entiende preguntas complejas y da respuestas precisas en segundos.

### **Diagrama Macro: El Ecosistema Portfolio-CORE**
Este gráfico muestra cómo el usuario interactúa con un sistema blindado y conectado.

```mermaid
graph LR
    User((Usuario)) --> L1[CAPA 1: CONTROL<br/>Next.js / Matriz de Madurez]
    L1 --> SEC[CAPA: SEGURIDAD<br/>IAM / Google Sheets]
    SEC --> L2[CAPA 2: INTELIGENCIA<br/>Agente ReAct / LangGraph]
    L2 <--> L3[CAPA 3: ORQUESTACIÓN<br/>Sync Engine / APIs]
    L2 <--> L4[CAPA 4: CONOCIMIENTO<br/>RAG / Elasticsearch]

    style L1 fill:#e3f2fd,stroke:#1565c2
    style L2 fill:#f1f8e9,stroke:#2e7d32
    style L3 fill:#fff3e0,stroke:#ef6c00
    style L4 fill:#f3e5f5,stroke:#4a148c
```

---

## **2. CAPA 1 & SEGURIDAD: EL CONTROL HUMANO (Nivel Funcional)**
**Objetivo:** Devolver al usuario el mando sobre los datos.
*   **La Matriz de Madurez:** Es una interfaz donde el usuario marca el ciclo de vida del documento (Borrador -> Revisión -> Oficial). La IA solo "aprende" lo que está en verde (Oficial).
*   **Seguridad Dinámica (IAM):** El acceso se controla mediante un Google Sheet. Esto permite que un administrador gestione permisos sin saber programar.

### **Diagrama de Flujo: El Portero y la Consola**
```mermaid
graph TD
    subgraph L1 [Capa de Presentación]
        A[Data Agent Console] --> B[Matriz de Madurez]
        B --> C[Auth.js / BFF]
    end
    subgraph Security [Capa de Seguridad]
        C --> D[Security API - FastAPI]
        D <--> E[Sheets_Reader - Permisos]
        E <--> F[(Google Sheets - RBAC)]
    end
    D --> G{¿Autorizado?}
    G -->|Sí| H[Acceso al Agente / Tools]
    style L1 fill:#e3f2fd
    style Security fill:#ffebee
```

---

## **3. CAPA 2: EL CEREBRO RESILIENTE (Nivel Técnico)**
**Objetivo:** Razonamiento inteligente y disponibilidad garantizada.
*   **Agente ReAct (LangGraph):** El agente no responde al azar; "piensa" antes de actuar. Si necesita un dato de Notion, llama a la herramienta correspondiente.
*   **Resiliencia Multi-LLM:** Si OpenAI falla, el sistema conmuta automáticamente a **Claude 3.5** o **Gemini 1.5**. El negocio nunca se detiene.
*   **State Management:** El sistema tiene "memoria de estado" (Checkpointing), recordando el hilo de la conversación.

### **Diagrama de Inteligencia: Razonamiento y Fallbacks**
```mermaid
graph TD
    subgraph L2 [Capa de Inteligencia]
        A[Agente de Razonamiento] <--> B[(State Management - MemorySaver)]
        subgraph Logic [Ciclo ReAct]
            A --> C{¿Herramienta?}
            C -->|Sí| D[Ejecutar Tool]
            D --> A
            C -->|No| F[Respuesta Final]
        end
        subgraph Resilience [Cascada de Modelos]
            G[GPT-4o] -.-> H[Claude 3.5] -.-> I[Gemini 1.5]
        end
        A --- Resilience
    end
    style L2 fill:#f1f8e9
```

---

## **4. CAPA 3: EL SISTEMA NERVIOSO (Nivel de Integración)**
**Objetivo:** Interoperabilidad total y fin del trabajo manual.
*   **Orquestador Asíncrono:** Un motor que procesa archivos Excel y los "empaca" para enviarlos a MySQL y Notion simultáneamente.
*   **Automatización Drive:** Crea automáticamente una estructura de 4 fases y 5 etapas en la nube para cada nuevo proyecto.

### **Diagrama de Orquestación: Conectividad Multi-Silo**
```mermaid
graph TB
    subgraph L3 [Capa de Orquestación]
        A[Petición de IA] --> B[FastAPI Orchestrator]
        B --> C[Extractor.py - Motor ETL]
        C --> D{Sync Engine}
        D -->|Update| E[Notion API]
        D -->|Estructura| F[Google Drive API]
        D -->|Upsert| G[MySQL Sync]
    end
    style L3 fill:#fff3e0
```

---

## **5. CAPA 4: LA MEMORIA OFICIAL (Nivel de Ingeniería de Datos)**
**Objetivo:** Verdad certificada y búsqueda semántica ultra-rápida.
*   **RAG (Retrieval Augmented Generation):** La IA consulta documentos PDF/DOCX en tiempo real.
*   **Elasticsearch + HNSW:** Usamos índices de "pequeños mundos navegables" (HNSW). Esto permite encontrar una respuesta entre millones de páginas en milisegundos (**O-logN**).
*   **Filtro de Gobernanza:** Solo se recuperan fragmentos de texto con el sello `OFFICIAL_VALIDATED`.

### **Diagrama de Memoria: El Almacén Vectorial**
```mermaid
graph LR
    subgraph L4 [Capa de Conocimiento]
        A[Documento Oficial] --> B[Embeddings OpenAI]
        B --> C[(Elasticsearch - Vector DB)]
        subgraph Search [Búsqueda KNN]
            E[Consulta Agente] --> F[Filtro: OFFICIAL]
            F --> G[Índice HNSW]
            G --> H[Respuesta Exacta]
        end
        C <--> G
    end
    style L4 fill:#f3e5f5
```

---

## **6. RESUMEN TÉCNICO DE VALOR **
1.  **Desacoplamiento:** Microservicios independientes. Si una API externa falla, el sistema sobrevive.
2.  **Anti-Alucinación:** Gobernanza estricta. La IA no inventa; cita fuentes oficiales de la Capa 4.
3.  **Resiliencia:** Arquitectura de fallbacks única en su clase (GPT/Claude/Gemini).
4.  **Eficiencia:** Sincronización automática que ahorra cientos de horas hombre de gestión administrativa.

---
**PORTFOLIO-CORE: Connect. Certify. Chat.**
