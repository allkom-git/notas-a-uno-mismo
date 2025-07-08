#!/usr/bin/env python3
"""
Módulo de prueba para envío de emails con Gmail SMTP
Ejecutar: python test_email.py
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
import secrets

# Cargar variables de entorno
load_dotenv()

def test_conexion_smtp():
    """
    Prueba la conexión SMTP con Gmail
    """
    print("🔍 Probando conexión SMTP con Gmail...")
    
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_user or not email_password:
        print("❌ Error: Variables EMAIL_USER y EMAIL_PASSWORD no encontradas en .env")
        print("📝 Agrega estas líneas a tu archivo .env:")
        print("   EMAIL_USER=tu_email@gmail.com")
        print("   EMAIL_PASSWORD=tu_contraseña_de_aplicacion")
        return False
    
    try:
        # Conectar a Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Habilitar cifrado TLS
        server.login(email_user, email_password)
        
        print(f"✅ Conexión exitosa con {email_user}")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación")
        print("💡 Verifica:")
        print("   1. Email correcto en EMAIL_USER")
        print("   2. Contraseña de aplicación (no tu contraseña normal)")
        print("   3. 2FA activado en tu cuenta Google")
        return False
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def enviar_email_simple(destinatario: str, asunto: str, mensaje: str):
    """
    Envía un email simple de texto
    """
    print(f"📧 Enviando email simple a {destinatario}...")
    
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    try:
        # Crear mensaje
        msg = MIMEText(mensaje, 'plain', 'utf-8')
        msg['From'] = email_user
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Enviar
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email simple enviado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email simple: {e}")
        return False


def enviar_magic_link_test(destinatario: str):
    """
    Envía un magic link de prueba con diseño bonito
    """
    print(f"🔗 Enviando magic link de prueba a {destinatario}...")
    
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    # Generar token de prueba
    token = secrets.token_urlsafe(32)
    magic_url = f"https://notasia.1963.com.ar/login?token={token}"
    
    # HTML bonito para el email
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
    
    try:
        # Crear mensaje multipart
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = destinatario
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
        
        print("✅ Magic link enviado correctamente")
        print(f"🔑 Token generado: {token}")
        print(f"🔗 URL: {magic_url}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando magic link: {e}")
        return False


def main():
    """
    Función principal para probar el envío de emails
    """
    print("🧪 === PRUEBA DE ENVÍO DE EMAILS ===\n")
    
    # Paso 1: Verificar conexión
    if not test_conexion_smtp():
        return
    
    print("\n" + "="*50)
    
    # Paso 2: Solicitar email de destino
    email_destino = input("\n📧 Ingresa tu email para las pruebas: ").strip()
    
    if not email_destino or "@" not in email_destino:
        print("❌ Email inválido")
        return
    
    print(f"\n🎯 Enviando emails de prueba a: {email_destino}")
    
    # Paso 3: Enviar email simple
    print("\n" + "-"*30)
    print("1️⃣ PRUEBA: Email simple")
    enviar_email_simple(
        email_destino,
        "✅ Prueba de conexión SMTP",
        f"¡Hola!\n\nEste es un email de prueba enviado desde tu aplicación de notas.\n\nFecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n¡La conexión SMTP funciona correctamente! 🎉"
    )
    
    # Paso 4: Enviar magic link
    print("\n" + "-"*30)
    print("2️⃣ PRUEBA: Magic link con diseño")
    enviar_magic_link_test(email_destino)
    
    print("\n" + "="*50)
    print("🎉 Pruebas completadas!")
    print("\n💡 Revisa tu bandeja de entrada (y spam) para ver los emails.")
    print("⚠️  NOTA: El magic link es solo de prueba, no funcionará en tu app aún.")


if __name__ == "__main__":
    main()
