import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // 1. Extraemos el formulario que viene del frontend
    const formData = await request.formData();
    const backendUrl = 'https://apiagente2-1057731265260.us-west4.run.app/agent';

    console.log("Reenviando petición al backend...");

    // 2. Enviamos al backend de Python en Cloud Run
    const apiRes = await fetch(backendUrl, {
      method: 'POST',
      body: formData,
      // IMPORTANTE: No pongas headers de Content-Type, 
      // fetch los genera automáticamente con el "boundary" correcto para archivos.
    });

    // 3. Verificamos si el backend respondió con un error (404, 500, 503, etc.)
    if (!apiRes.ok) {
      const errorText = await apiRes.text();
      console.error("El Agente (Python) devolvió un error:", errorText);
      
      return NextResponse.json(
        { error: "El Agente no pudo procesar la solicitud", details: errorText },
        { status: apiRes.status }
      );
    }

    // 4. Si todo salió bien, enviamos el JSON al frontend
    const data = await apiRes.json();
    return NextResponse.json(data);

  } catch (error) {
    // Manejo de errores de red o errores inesperados
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    
    console.error("Error crítico en API Proxy (Next.js):", error);
    
    return NextResponse.json(
      { error: "Error de conexión con el Agente", details: errorMessage },
      { status: 500 }
    );
  }
}