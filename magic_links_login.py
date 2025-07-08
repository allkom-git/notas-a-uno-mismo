#!/usr/bin/env python3
"""
magic_links_login.py - Módulo para autenticación con Magic Links
"""

import secrets
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from utils.db import get_db_connection
from dotenv import load_dotenv

load_dotenv()

# Router para los endpoints de magic links
router = APIRouter()

# Modelos Pydantic
class MagicLinkRequest(BaseModel):
    email: str

class SessionInfo(BaseModel):
    email: str
    expires_at: str
    days_remaining: int


def enviar_email_magic_link(email: str, magic_url: str):
    """
    Envía email con magic link usando Gmail SMTP
    """
    try:
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            raise Exception("Credenciales de email no configuradas")
        
        # HTML del email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tu Magic Link</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f7fa;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f7fa; padding: 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 300;">🔗 Tu Magic Link</h1>
                                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Accede a tus notas personales de forma segura</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333; margin: 0 0 20px 0; font-size: 20px;">¡Hola! 👋</h2>
                                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Recibiste este email porque solicitaste acceso a tu cuenta de Notas Personales. 
                                        Haz clic en el botón de abajo para acceder de forma segura:
                                    </p>
                                    
                                    <!-- Magic Button -->
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center" style="padding: 20px 0;">
                                                <a href="{magic_url}" 
                                                   style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                                                          color: white; 
                                                          padding: 16px 32px; 
                                                          text-decoration: none; 
                                                          border-radius: 25px; 
                                                          font-weight: 600; 
                                                          font-size: 16px;
                                                          display: inline-block;
                                                          box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);">
                                                    🚀 Acceder a mis notas
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Alternative link -->
                                    <p style="color: #999; font-size: 14px; text-align: center; margin: 20px 0;">
                                        ¿No funciona el botón? Copia y pega este enlace:<br>
                                        <a href="{magic_url}" style="color: #667eea; word-break: break-all;">{magic_url}</a>
                                    </p>
                                    
                                    <!-- Security info -->
                                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 30px 0 0 0;">
                                        <p style="color: #666; font-size: 14px; margin: 0 0 10px 0;">
                                            <strong>🔒 Información de seguridad:</strong>
                                        </p>
                                        <ul style="color: #666; font-size: 14px; margin: 0; padding-left: 20px;">
                                            <li>⏰ Este enlace expira en <strong>15 minutos</strong></li>
                                            <li>🔐 Solo funciona <strong>una vez</strong></li>
                                            <li>🚫 Si no solicitaste este acceso, <strong>ignora este email</strong></li>
                                        </ul>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="color: #999; font-size: 12px; margin: 0;">
                                        Enviado desde <strong>Notas Personales</strong> • {datetime.now().strftime("%d/%m/%Y %H:%M")}
                                    </p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = email
        msg['Subject'] = "🔗 Tu acceso seguro a Notas Personales"
        
        # Versión texto plano (fallback)
        texto_plano = f"""
        ¡Hola!
        
        Accede a tus notas personales usando este enlace seguro:
        {magic_url}
        
        ⏰ Este enlace expira en 15 minutos
        🔐 Solo funciona una vez
        
        Si no solicitaste este acceso, ignora este email.
        
        Saludos,
        Notas Personales
        """
        
        # Agregar ambas versiones
        msg.attach(MIMEText(texto_plano, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Enviar
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Magic link enviado a {email}")
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        raise Exception(f"No se pudo enviar el email: {str(e)}")


@router.post("/send-magic-link")
def send_magic_link(data: MagicLinkRequest):
    """
    Genera y envía un magic link al email del usuario
    """
    email = data.email.lower().strip()
    
    if not email or "@" not in email:
        return {"status": "error", "message": "Email inválido"}
    
    # Generar token único y seguro
    token = secrets.token_urlsafe(32)  # 256 bits de entropía
    expires_at = datetime.utcnow() + timedelta(minutes=15)  # Expira en 15 min
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Invalidar tokens anteriores para este email
        cursor.execute("""
            UPDATE magic_tokens 
            SET used = TRUE 
            WHERE email = %s AND used = FALSE
        """, (email,))
        
        # Crear nuevo token
        cursor.execute("""
            INSERT INTO magic_tokens (email, token, expires_at) 
            VALUES (%s, %s, %s)
        """, (email, token, expires_at))
        
        db.commit()
        
        # Enviar email
        magic_url = f"https://notasia.1963.com.ar/magic-login?token={token}"
        enviar_email_magic_link(email, magic_url)
        
        print(f"🔗 Magic link creado para {email}, token: {token}")
        
        return {
            "status": "ok",
            "message": f"Magic link enviado a {email}. Revisa tu bandeja de entrada."
        }
        
    except Exception as e:
        print(f"❌ Error enviando magic link: {e}")
        return {"status": "error", "message": "Error enviando el email. Intenta nuevamente."}
    
    finally:
        cursor.close()
        db.close()


@router.get("/magic-login")
def login_with_magic_token(token: str):
    """
    Valida magic token y crea sesión de 30 días máximo
    """
    if not token:
        return {"status": "error", "message": "Token requerido"}
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar token
        cursor.execute("""
            SELECT email, expires_at, used 
            FROM magic_tokens 
            WHERE token = %s
        """, (token,))
        
        magic_token = cursor.fetchone()
        
        if not magic_token:
            return {"status": "error", "message": "Token inválido"}
        
        if magic_token['used']:
            return {"status": "error", "message": "Token ya utilizado"}
        
        if datetime.utcnow() > magic_token['expires_at']:
            return {"status": "error", "message": "Token expirado. Solicita un nuevo magic link."}
        
        # ✅ Token válido - crear sesión
        email = magic_token['email']
        
        # Marcar token como usado
        cursor.execute("""
            UPDATE magic_tokens 
            SET used = TRUE 
            WHERE token = %s
        """, (token,))
        
        # Buscar o crear usuario
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            cursor.execute(
                "INSERT INTO usuarios (nombre, email) VALUES (%s, %s)", 
                (email, email)
            )
            db.commit()
        
        # Invalidar sesiones anteriores (opcional)
        cursor.execute("DELETE FROM sessions WHERE email = %s", (email,))
        
        # Crear nueva sesión (30 días máximo, manual)
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        cursor.execute("""
            INSERT INTO sessions (email, session_token, expires_at) 
            VALUES (%s, %s, %s)
        """, (email, session_token, expires_at))
        
        db.commit()
        
        print(f"✅ Sesión creada para {email}, expira en 30 días")
        
        return {
            "status": "ok",
            "message": "Login exitoso",
            "session_token": session_token,
            "email": email,
            "expires_at": expires_at.isoformat(),
            "expires_in_days": 30
        }
        
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return {"status": "error", "message": "Error interno"}
    
    finally:
        cursor.close()
        db.close()


def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Middleware para validar sesión en endpoints protegidos
    """
    if not authorization:
        raise HTTPException(401, "Token de sesión requerido")
    
    # Extraer token (formato: "Bearer abc123xyz")
    if authorization.startswith("Bearer "):
        session_token = authorization[7:]
    else:
        session_token = authorization
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT email, expires_at FROM sessions 
            WHERE session_token = %s
        """, (session_token,))
        
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(401, "Sesión inválida")
        
        if datetime.utcnow() > session['expires_at']:
            # Limpiar sesión expirada
            cursor.execute("DELETE FROM sessions WHERE session_token = %s", (session_token,))
            db.commit()
            raise HTTPException(401, "Sesión expirada. Solicita un nuevo magic link.")
        
        # Actualizar último uso
        cursor.execute("""
            UPDATE sessions 
            SET last_used = CURRENT_TIMESTAMP 
            WHERE session_token = %s
        """, (session_token,))
        db.commit()
        
        return session['email']
        
    finally:
        cursor.close()
        db.close()


@router.get("/session-info")
def get_session_info(current_user: str = Depends(get_current_user)):
    """
    Obtiene información de la sesión actual
    """
    return {
        "email": current_user,
        "status": "active",
        "message": "Sesión válida"
    }


@router.post("/logout")
def logout(current_user: str = Depends(get_current_user)):
    """
    Cierra sesión manual
    """
    # Buscar y eliminar sesión por email
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE email = %s", (current_user,))
        db.commit()
        
        print(f"🔓 Logout manual para {current_user}")
        
        return {
            "status": "ok",
            "message": "Sesión cerrada correctamente"
        }
        
    finally:
        cursor.close()
        db.close()
