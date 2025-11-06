"""
MCP-Server für das taskapp-backend (mit Authentifizierung).
Verwendet das mcp-python-sdk (STDIO).
"""

import httpx
import os
import sys
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- 1. Konfiguration ---
# Umgebungsvariablen für die Anmeldedaten abrufen
# Die Basis-URL Ihres Backends
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080/api")
# Wir verwenden die vom Benutzer vorgeschlagenen Standardwerte,
# falls die ENV-Variablen nicht gesetzt sind.
TASKAPP_USER = os.getenv("TASKAPP_USER", "max.power")
TASKAPP_PASSWORD = os.getenv("TASKAPP_PASSWORD", "password456")

if TASKAPP_USER == "max.power":
    print(
        "Info: Verwende Standard-Benutzer 'max.power'. Setze TASKAPP_USER für einen anderen Benutzer.",
        file=sys.stderr,
    )


# --- 2. Authentifizierungs-Logik ---


def create_authenticated_client() -> httpx.Client:
    """
    Diese Funktion wird EINMAL beim Start des Servers aufgerufen.
    Sie meldet sich beim Backend an und erstellt einen Client,
    der den Token automatisch für alle Anfragen verwendet.
    """
    print(
        f"Versuche Login beim Backend ({BACKEND_URL}) als Benutzer '{TASKAPP_USER}'...",
        file=sys.stderr,
    )

    try:
        # Temporärer Client nur für den Login
        with httpx.Client(base_url=BACKEND_URL) as login_client:
            response = login_client.post(
                "/auth/login",
                json={"username": TASKAPP_USER, "password": TASKAPP_PASSWORD},
            )

            # WICHTIG: Wenn der Login fehlschlägt, MUSS der Server abstürzen.
            response.raise_for_status()

            # Token aus der Antwort extrahieren (Annahme: Standard-OAuth2-Antwort)
            token = response.json().get("token")
            if not token:
                raise ValueError(
                    "Konnte 'access_token' nicht in der Login-Antwort finden."
                )

            print("Login erfolgreich. Bearer-Token erhalten.", file=sys.stderr)

            # --- Permanenten, authentifizierten Client erstellen ---
            headers = {"Authorization": f"Bearer {token}"}

            # Dieser Client wird für alle Tool-Aufrufe wiederverwendet
            return httpx.Client(base_url=BACKEND_URL, headers=headers)

    except httpx.HTTPStatusError as e:
        print(
            f"FEHLER: Login fehlgeschlagen! Status: {e.response.status_code}, Antwort: {e.response.text}",
            file=sys.stderr,
        )
        raise  # Beendet das Skript
    except httpx.ConnectError as e:
        print(f"FEHLER: Backend unter {BACKEND_URL} nicht erreichbar.", file=sys.stderr)
        raise
    except Exception as e:
        print(f"FEHLER beim Login: {e}", file=sys.stderr)
        raise


# --- 3. MCP Server Initialisierung ---

mcp = FastMCP("TaskApp Backend Adapter")

# Der Client wird hier, beim Laden des Skripts, erstellt und authentifiziert.
# Wenn dies fehlschlägt, startet der MCP-Server gar nicht erst.
client = create_authenticated_client()


# --- 4. Pydantic-Modell für Parameter ---


class GetTasksParams(BaseModel):
    project_id: int
    user_id: Optional[int] = Field(
        None, description="Optional: Nach Benutzer-ID filtern."
    )


# --- 5. Tool-Definition ---


@mcp.tool()
def get_tasks(params: GetTasksParams) -> Dict[str, Any]:
    """
    Ruft Aufgaben für ein bestimmtes Projekt ab.
    Die Authentifizierung erfolgt automatisch.
    """
    print(
        f"Tool 'get_tasks' aufgerufen für Projekt {params.project_id}", file=sys.stderr
    )
    try:
        query_params = {}
        if params.user_id:
            query_params["user_id"] = params.user_id

        # ANNAHME: Ihr Backend ist GET /api/v1/projects/{id}/tasks
        # Der 'client' hat bereits den Bearer-Token im Header.
        response = client.get(
            f"/projects/{params.project_id}/tasks", params=query_params
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        # Meldet einen Backend-Fehler an die KI
        return {
            "error": f"Backend-Fehler: {e.response.status_code}",
            "details": e.response.text,
        }
    except Exception as e:
        return {"error": f"Interner MCP-Fehler: {str(e)}"}


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def get_weather(city: str, unit: str = "celsius") -> str:
    """Get weather for a city."""
    # This would normally call a weather API
    return f"Weather in {city}: 22degrees{unit[0].upper()}"


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."
