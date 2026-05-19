import httpx
from bs4 import BeautifulSoup
import asyncio


async def buscar_dni_eldni(dni: str) -> dict | None:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get("https://www.eldni.com/")
            response.raise_for_status()

            soup = await asyncio.to_thread(BeautifulSoup, response.text, "lxml")
            token_input = soup.find("input", attrs={"name": "_token"})
            token = token_input.get("value") if token_input else None
            if not token:
                return None

            response = await client.post(
                "https://eldni.com/pe/buscar-datos-por-dni",
                data={"_token": token, "dni": dni},
            )
            response.raise_for_status()

        soup = await asyncio.to_thread(BeautifulSoup, response.text, "lxml")

        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            values = [" ".join(cell.get_text(" ", strip=True).split()) for cell in cells[:4]]
            if values[0] != dni or not any(values[1:]):
                continue

            nombres = values[1]
            apellido_paterno = values[2]
            apellido_materno = values[3]
            nombre_completo = " ".join(
                part for part in [apellido_paterno, apellido_materno, nombres] if part
            )

            if not nombre_completo:
                return None

            return {
                "numero_documento": dni,
                "nombre": nombre_completo,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "nombres": nombres,
            }

        return None
    except Exception:
        return None
