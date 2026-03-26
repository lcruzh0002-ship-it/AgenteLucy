# Portfolio-CORE
Ecosistema de IA Generativa con arquitectura de microservicios que orquesta datos de Drive, Notion y MySQL mediante agentes resilientes y RAG sobre Elasticsearch

---


# **1. INTRODUCCIÓN Y PROPÓSITO DEL PROYECTO**

### **1.1. Contexto Estratégico**
En el actual ecosistema corporativo, las organizaciones enfrentan un desafío crítico: la **fragmentación de activos de información**. Los datos estratégicos residen en silos aislados —unidades de red (Google Drive), plataformas de gestión colaborativa (Notion) y bases de datos relacionales (MySQL)— lo que genera una brecha de conocimiento, duplicidad de tareas y, fundamentalmente, una pérdida de la **trazabilidad oficial**.

La implementación convencional de Inteligencia Artificial a menudo ignora la jerarquía y la veracidad de estos datos, resultando en respuestas imprecisas o "alucinaciones" que no cumplen con los estándares de auditoría y cumplimiento empresarial.

### **1.2. Definición de Portfolio-CORE**
**Portfolio-CORE** surge como una respuesta de ingeniería avanzada diseñada para cerrar la brecha entre la **Inteligencia de Capacidad** (IA Generativa) y la **Integridad de Información** (Gobernanza de Datos). No se define simplemente como un asistente conversacional, sino como un **Agente Orquestador de Conocimiento** capaz de navegar, sincronizar y certificar el flujo de información de un portafolio de proyectos complejo.

### **1.3. La Propuesta de Valor: De la IA al Gobierno de Datos**
El núcleo diferenciador de este sistema es la implementación de una **Matriz de Madurez Documental**. Esta funcionalidad permite al usuario humano supervisar el ciclo de vida del dato, asegurando que la arquitectura de **Recuperación Aumentada (RAG)** solo consuma información que ha alcanzado un nivel de madurez "Oficial". 

Mediante una infraestructura de **microservicios asíncronos y resilientes**, Portfolio-CORE garantiza que la "Verdad Única" de la organización esté siempre disponible, actualizada y, sobre todo, validada por expertos humanos.

### **1.4. Alcance Técnico y Arquitectura**
El presente documento detalla una arquitectura de grado industrial desplegada en la nube (**Google Cloud Run**), que integra:
*   **Agentes Inteligentes (LangGraph):** Con capacidad de razonamiento autónomo y memoria de estado persistente.
*   **Resiliencia Operativa:** Una estrategia multi-modelo con *fallbacks* automáticos para garantizar alta disponibilidad.
*   **Búsqueda Semántica de Alto Rendimiento:** Indexación vectorial mediante algoritmos **HNSW** en Elasticsearch para recuperaciones instantáneas.
*   **Interoperabilidad Total:** Sincronización bidireccional entre ecosistemas Cloud y bases de datos relacionales.

---


# **2. El Gráfico: "El Viaje del Dato Oficial"

1.  **La Consola (El Control):** "Aquí el usuario no solo chatea, sino que **gobierna**. Usa la *Matriz de Madurez* para decir qué archivos son borradores y cuáles son Verdad Oficial."
2.  **El Guardián (La Seguridad):** "Antes de que la IA se mueva, nuestra API de Seguridad revisa una lista en la nube. Si no tienes permiso, el sistema no te muestra ni una palabra."
3.  **El Cerebro (La Inteligencia):** "Usamos un Agente que **razona**. Si le pides algo, él decide si debe ir a buscar en los documentos o actualizar el estado en Notion. Además, es **resiliente**: si falla una IA, usa otra de respaldo automáticamente."
4.  **Las Manos (La Orquestación):** "Este es el motor que hace el trabajo pesado. Conecta Google Drive, Notion y las bases de datos para que todo esté sincronizado en segundos, sin que el humano tenga que copiar y pegar nada."
5.  **La Memoria (La Verdad):** "Aquí es donde Portfolio-CORE brilla. Nuestra IA no inventa. Solo busca en la memoria de **documentos certificados**. Si el documento no pasó por la Matriz de Madurez, la IA simplemente no lo conoce."


```mermaid
graph TD
    %% Estilos de Colores
    classDef front fill:#e3f2fd,stroke:#1565c2,stroke-width:2px,color:#1565c2;
    classDef brain fill:#f1f8e9,stroke:#2e7d32,stroke-width:2px,color:#2e7d32;
    classDef hands fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#ef6c00;
    classDef vault fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#4a148c;
    classDef security fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#c62828;

    %% Nodos de la Arquitectura
    User((<b>USUARIO</b>)) --> Console[<b>1. CONSOLA DE CONTROL</b><br/>Next.js / Matriz de Madurez]:::front
    
    Console --> Guard[<b>2. EL GUARDIAN</b><br/>Security API / Google Sheets]:::security
    
    Guard --> Agent[<b>3. EL CEREBRO</b><br/>Agente ReAct / LangGraph]:::brain
    
    subgraph Inteligencia [Resiliencia Inteligente]
        Agent -.-> LLM1[GPT-4o]
        LLM1 -- Fallback --> LLM2[Claude 3.5]
    end

    Agent <--> Orch[<b>4. LAS MANOS</b><br/>Orquestador / Sync Engine]:::hands
    
    subgraph Silos [Ecosistema de Datos]
        Orch <--> Drive[Google Drive]
        Orch <--> Notion[Notion Kanban]
        Orch <--> SQL[(MySQL - Logs)]
    end

    Agent <--> RAG[<b>5. LA MEMORIA OFICIAL</b><br/>Elasticsearch / Vector DB]:::vault
    
    %% La lógica de negocio
    Drive -- "Solo Documentos Verdes" --> RAG
    RAG -- "Citas de Fuentes Reales" --> Agent

    %% Leyenda
    linkStyle default stroke:#555,stroke-width:1px;
```



---
# **3. Evidencia

## ANEXO 1: Evidencia del lo desplegago

<img width="947" height="665" alt="image" src="https://github.com/user-attachments/assets/487d4eb8-2f45-4ddf-b95a-b6fe71cd667c" />
---
## ANEXO 2: Evidencia del MVP

<img width="1161" height="590" alt="image" src="https://github.com/user-attachments/assets/19e87c15-49b9-418c-98d6-5b9a0944e7b0" />
<img width="1153" height="784" alt="image" src="https://github.com/user-attachments/assets/934b36f7-17db-47a7-9229-656ad652e26d" />
<img width="1149" height="825" alt="image" src="https://github.com/user-attachments/assets/75886fc3-b0ab-4b0f-873b-07be20d8e044" />
<img width="1158" height="665" alt="image" src="https://github.com/user-attachments/assets/37099e35-c007-4434-a98d-d47cce4ce08e" />
<img width="1567" height="876" alt="image" src="https://github.com/user-attachments/assets/379a801f-e95a-4b88-ba31-ea2c3dae5503" />
<img width="1554" height="502" alt="image" src="https://github.com/user-attachments/assets/c2fba67c-cb2f-4aaa-8b60-a4e474b15903" />

Creacón de carpeta en drive - Antes

<img width="1571" height="420" alt="image" src="https://github.com/user-attachments/assets/0f8d716f-9f6e-4900-b734-5bed67fabf66" />

Creacón de carpeta en drive - Despues

<img width="1604" height="662" alt="image" src="https://github.com/user-attachments/assets/ed174582-2552-4c29-ba4c-ff93c57fd7b5" />
<img width="604" height="351" alt="image" src="https://github.com/user-attachments/assets/6b270f62-d242-4d82-be22-2d96f346b1ff" />

