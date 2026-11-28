#!/usr/bin/env python3
"""
Standalone Gmail CDP email sender for test leads.
Uses the existing Chrome CDP session on port 9222.
Properly handles WebSocket request/response matching.
"""
import asyncio
import json
import websockets
import time
from datetime import datetime


class CDPClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self.request_id = 0
        self.pending = {}
    
    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, ping_interval=None, max_size=10**7)
        # Start message listener
        self.listener_task = asyncio.create_task(self._listen())
    
    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                # Handle response to our request
                if "id" in data and data["id"] in self.pending:
                    future = self.pending.pop(data["id"])
                    future.set_result(data)
        except Exception as e:
            print(f"Listener error: {e}")
    
    async def send_command(self, method: str, params: dict = None) -> dict:
        self.request_id += 1
        req_id = self.request_id
        future = asyncio.get_event_loop().create_future()
        self.pending[req_id] = future
        
        msg = {"id": req_id, "method": method}
        if params:
            msg["params"] = params
        
        await self.ws.send(json.dumps(msg))
        
        try:
            response = await asyncio.wait_for(future, timeout=10)
            return response
        except asyncio.TimeoutError:
            self.pending.pop(req_id, None)
            raise Exception(f"Timeout waiting for response to {method}")
    
    async def evaluate(self, expression: str) -> dict:
        return await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True
        })
    
    async def close(self):
        if self.listener_task:
            self.listener_task.cancel()
        if self.ws:
            await self.ws.close()


async def send_gmail_cdp(ws_url: str, to_email: str, subject: str, body_html: str) -> bool:
    """Send email via Gmail CDP automation with proper response handling."""
    client = CDPClient(ws_url)
    try:
        await client.connect()
        await asyncio.sleep(0.5)  # Let listener start
        
        # Enable Runtime
        resp = await client.send_command("Runtime.enable", {})
        if "error" in resp:
            print(f"  Runtime.enable error: {resp['error']}")
            return False
        
        # Find the To field and fill it
        script = f"""
        (() => {{
            const toField = document.querySelector('div[role="listbox"][aria-label*="To" i]');
            if (toField) {{
                toField.click();
                toField.focus();
                document.execCommand('insertText', false, '{to_email}');
                toField.dispatchEvent(new Event('input', {{bubbles: true}}));
                // Press Enter to confirm
                const event = new KeyboardEvent('keydown', {{key: 'Enter', bubbles: true}});
                toField.dispatchEvent(event);
                return true;
            }}
            return false;
        }})()
        """
        resp = await client.evaluate(script)
        result = resp.get("result", {}).get("result", {}).get("value", False)
        if not result:
            print(f"  Could not fill To field for {to_email}")
            return False
        
        await asyncio.sleep(1)
        
        # Fill Subject
        script = f"""
        (() => {{
            const subjInput = document.querySelector('input[name="subjectbox"]');
            if (subjInput) {{
                subjInput.focus();
                subjInput.value = '{subject.replace("'", "\\'")}';
                subjInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                subjInput.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        resp = await client.evaluate(script)
        result = resp.get("result", {}).get("result", {}).get("value", False)
        if not result:
            print(f"  Could not fill Subject")
            return False
        
        await asyncio.sleep(0.5)
        
        # Fill Body with HTML
        escaped_body = body_html.replace('`', '\\`').replace('${', '\\${')
        script = f"""
        (() => {{
            const bodyDiv = document.querySelector('div[role="textbox"][contenteditable="true"]');
            if (bodyDiv) {{
                bodyDiv.focus();
                bodyDiv.innerHTML = `{escaped_body}`;
                bodyDiv.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        resp = await client.evaluate(script)
        result = resp.get("result", {}).get("result", {}).get("value", False)
        if not result:
            print(f"  Could not fill Body")
            return False
        
        await asyncio.sleep(1)
        
        # Click Send button
        script = """
        (() => {
            const sendBtn = document.querySelector('div[role="button"][aria-label*="Send" i], button[aria-label*="Send" i]');
            if (sendBtn) { sendBtn.click(); return true; }
            return false;
        })()
        """
        resp = await client.evaluate(script)
        result = resp.get("result", {}).get("result", {}).get("value", False)
        if not result:
            print(f"  Could not click Send button")
            return False
        
        await asyncio.sleep(3)
        return True
        
    except Exception as e:
        print(f"  Error sending to {to_email}: {e}")
        return False
    finally:
        await client.close()


async def main():
    # Get the Gmail compose tab WS URL
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:9222/json/list") as f:
            tabs = json.loads(f.read().decode())
    except Exception as e:
        print(f"Failed to get Chrome tabs: {e}")
        return
    
    gmail_ws = None
    for tab in tabs:
        if "mail.google.com" in tab.get("url", "") and "compose" in tab.get("url", ""):
            gmail_ws = tab.get("webSocketDebuggerUrl")
            break
    
    if not gmail_ws:
        print("No Gmail compose tab found. Open a new compose window in Chrome first.")
        for tab in tabs:
            print(f"  Tab: {tab.get('url', '')[:80]}...")
        return
    
    print(f"Using Gmail compose tab: {gmail_ws}")
    
    # Test leads
    test_leads = [
        {
            "id": "LTEST001",
            "name": "Artistry BJJ",
            "email": "contact@artistrybjj.com",
            "city": "Houston",
            "disciplines": "Brazilian Jiu-Jitsu"
        },
        {
            "id": "LTEST002",
            "name": "Inspire Jiu-Jitsu Academy",
            "email": "info@inspirejiujitsuacademy.com",
            "city": "Houston",
            "disciplines": "Brazilian Jiu-Jitsu"
        },
        {
            "id": "LTEST003",
            "name": "Grappling Zone",
            "email": "info@grapplingzone.com",
            "city": "Houston",
            "disciplines": "Grappling, Brazilian Jiu-Jitsu"
        },
        {
            "id": "LTEST004",
            "name": "Pablo Silva Brazilian Jiu Jitsu HQ",
            "email": "info@pablosilvabjj.com",
            "city": "Bellaire",
            "disciplines": "Brazilian Jiu-Jitsu"
        },
        {
            "id": "LTEST005",
            "name": "Inevat Jiu Jitsu East Downtown",
            "email": "david@inevateastdowntown.com",
            "city": "Houston",
            "disciplines": "Brazilian Jiu-Jitsu"
        }
    ]
    
    for lead in test_leads:
        print(f"\nSending to {lead['name']} ({lead['email']})...")
        
        subject = f"Partnership Proposal: B2B Martial Arts Uniforms for {lead['name']}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
            <p>Hola {lead['name']} team,</p>
            
            <p>Soy <strong>HSN Warrior Apparels</strong> (Sialkot, Pakistán) — fabricantes B2B de uniformes y equipamiento para artes marciales desde 2011.</p>
            
            <p>Vimos que <strong>{lead['name']}</strong> en {lead['city']} ofrece clases de <strong>{lead['disciplines']}</strong>. Queremos proponer una asociación para suministrar sus uniformes y equipamiento con:</p>
            
            <ul>
                <li><strong>Precios de fábrica</strong> — sin intermediarios, directo desde Sialkot</li>
                <li><strong>MOQ 30 pcs</strong> por estilo/color</li>
                <li><strong>Producción 4–6 semanas</strong> + envío puerta a puerta DHL/FedEx (aduanas incluidas, sin sorpresas)</li>
                <li><strong>Branding gratis</strong> — logos, etiquetas, packaging personalizado</li>
                <li><strong>Catálogo completo</strong>: BJJ Gi, Judo, Karate, Taekwondo, MMA, Boxeo, Rash Guards, Shorts, Cinturones, Protecciones</li>
            </ul>
            
            <p><strong>Próximos pasos:</strong></p>
            <ol>
                <li>Responda con sus necesidades: estilos, cantidades por talla/color, peso de tela (ligero/medio/pesado)</li>
                <li>Adjunte su logo (AI/SVG/PDF/PNG) para mockup gratis</li>
                <li>Le enviamos cotización formal con precios unitarios y timeline</li>
            </ol>
            
            <p>Catálogo PDF: <a href="https://hsnwarriorapparels.vercel.app/HSN_Warrior_Apparels_Catalog.pdf">Ver catálogo</a><br>
            Lista de precios: <a href="https://hsnwarriorapparels.vercel.app/price-list.pdf">Ver precios</a></p>
            
            <p>Quedo a su disposición para cualquier duda.</p>
            
            <p>Saludos cordiales,<br>
            <strong>HSN Warrior Apparels</strong><br>
            Sialkot, Pakistán<br>
            hsnwarriorapparel@gmail.com | +92 337 333 6381<br>
            <a href="https://hsnwarriorapparels.vercel.app">hsnwarriorapparels.vercel.app</a></p>
        </div>
        """
        
        success = await send_gmail_cdp(gmail_ws, lead['email'], subject, body_html)
        if success:
            print(f"  ✅ Email sent successfully to {lead['email']}")
        else:
            print(f"  ❌ Failed to send to {lead['email']}")
        
        # Delay between emails
        await asyncio.sleep(5)
    
    print("\n✅ All test emails processed")


if __name__ == "__main__":
    asyncio.run(main())