import smtplib
import anyio
from email.message import EmailMessage
from app.core.collector import collector
from app.services.email_templates import get_verification_template, get_forget_password_template
from loguru import logger

class BrevoEmailService:  # ⚡ Wapas wahi trusted naam rakh diya bhai!
    """
    Hybrid High-Velocity SMTP Transactional Email Service.
    Uses native smtplib executed inside non-blocking asynchronous worker threads.
    """

    @classmethod
    def _build_raw_message(cls, to_email: str, to_name: str, subject: str, html_content: str) -> EmailMessage:
        """Compiles standard multi-part structural EmailMessage matrix."""
        msg = EmailMessage()
        
        from_name = collector.get("BREVO_FROM_NAME", "SARIQX Support Engine")
        from_email = collector.get("BREVO_FROM_EMAIL", "no-reply@sariqx.com")
        
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email.strip()}>"
        msg["To"] = f"{to_name} <{to_email.strip()}>"

        plain_text_fallback = "SARIQX Security Operational Transmission. Please use an HTML compatible mail client."
        msg.set_content(plain_text_fallback, subtype="plain", charset="utf-8")
        
        msg.add_alternative(html_content, subtype="html", charset="utf-8")
        return msg

    @classmethod
    def _synchronous_smtp_send(cls, msg: EmailMessage):
        """Pure synchronous SMTP network connection wrapper block."""
        host = collector.get("SMTP_HOST", "smtp-relay.brevo.com")
        port = int(collector.get("SMTP_PORT", 587))
        user = collector.get("BREVO_SMTP_USER") or collector.get("SMTP_USER")
        password = collector.get("BREVO_SMTP_KEY") or collector.get("SMTP_PASS")

        if not user or not password:
            raise ValueError("SMTP network connection dropped: Auth credentials missing in configuration.")

        with smtplib.SMTP(host, port, timeout=10.0) as server:
            if port == 587:
                server.starttls()  
            server.login(user, password)
            server.send_message(msg)

    @classmethod
    async def send_transactional_html(cls, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        """Main non-blocking async proxy runner mapping to thread pool."""
        try:
            msg = cls._build_raw_message(to_email, to_name, subject, html_content)
            await anyio.to_thread.run_sync(cls._synchronous_smtp_send, msg)
            logger.info(f"📨 Mail Pipeline: SMTP relay dispatched message context smoothly to {to_email}")
            return True
        except Exception as e:
            logger.error(f"💥 Mail Critical Failure: SMTP socket interaction crashed across network thread: {e}")
            return False

    @classmethod
    async def send_verification(cls, email: str, name: str, token: str):
        """Assembles and triggers account verification links"""
        verify_link = f"http://localhost:8000/api/v1/auth/verify?token={token}" 
        html = get_verification_template(name, verify_link)
        await cls.send_transactional_html(email, name, "SARIQX: Verify your security infrastructure", html)

    @classmethod
    async def send_password_reset(cls, email: str, name: str, token: str):
        """Assembles and triggers password recovery nodes"""
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        html = get_forget_password_template(name, reset_link)
        await cls.send_transactional_html(email, name, "SARIQX: Security Password Reset Request", html)