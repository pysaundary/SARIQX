def get_verification_template(name: str, verify_link: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #4F46E5, #06B6D4); padding: 30px; text-align: center; color: white; }}
            .content {{ padding: 40px; color: #333333; line-height: 1.6; }}
            .btn {{ display: inline-block; padding: 14px 30px; background-color: #4F46E5; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2); }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to SARIQX! 🚀</h1>
            </div>
            <div class="content">
                <p>Hello <strong>{name}</strong>,</p>
                <p>Thank you for registering on SARIQX. Your multi-tenant secure space is almost ready. Please click the button below to verify your email address and activate your account:</p>
                <div style="text-align: center;">
                    <a href="{verify_link}" class="btn">Verify My Email</a>
                </div>
                <p style="margin-top: 30px; font-size: 13px; color: #6b7280;">If the button doesn't work, copy-paste this link into your browser:<br>{verify_link}</p>
            </div>
            <div class="footer">
                <p>This is an automated operational transmission from SARIQX Engine.<br>© 2026 SARIQX Inc.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_forget_password_template(name: str, reset_link: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ background: #1e293b; padding: 30px; text-align: center; color: white; }}
            .content {{ padding: 40px; color: #333333; line-height: 1.6; }}
            .btn {{ display: inline-block; padding: 14px 30px; background-color: #ef4444; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 6px rgba(239, 68, 68, 0.2); }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Requested 🔐</h1>
            </div>
            <div class="content">
                <p>Hello <strong>{name}</strong>,</p>
                <p>We received a request to reset the password for your SARIQX account context. Click the button below to set up a new password. This secure link will expire in 15 minutes:</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="btn">Reset Password</a>
                </div>
                <p style="margin-top:30px; color: #ef4444; font-size: 13px;"><strong>Security Alert:</strong> If you did not request this change, please ignore this email or reach out to platform guards immediately.</p>
            </div>
            <div class="footer">
                <p>SARIQX High-Velocity Security Control System.<br>© 2026 SARIQX Inc.</p>
            </div>
        </div>
    </body>
    </html>
    """