"""
"""

from email_util import send_email_with_image
from libraries.logger import get_logger
logger = get_logger(__name__)
from secrets_util import secret_or_env


def send_generated_energy_email(weg_info: tuple[str, str, str], saj_info: tuple[str, str, str], solis_info: tuple[str, str, str], growatt_info: tuple[str, str, str]):
        weg_production, weg_title, weg_shot = weg_info
        saj_production, saj_title, saj_shot = saj_info
        solis_production, solis_title, solis_shot = solis_info
        growatt_production, growatt_title, growatt_shot = growatt_info
        to_addr = secret_or_env("EMAIL_TO")
        logger.info("Sending emails to %s", to_addr)
        if not to_addr:
            logger.info("EMAIL_TO not set — email skipped")
            return
        smtp_user = secret_or_env("SMTP_USER")
        smtp_password = secret_or_env("SMTP_PASSWORD")
        if not smtp_user or not smtp_password:
            logger.info("SMTP_USER or SMTP_PASSWORD not set — email skipped")
            return
        inversor2 = round(float(saj_production) + float(solis_production) + float(growatt_production), 2)
        recipients = [addr.strip() for addr in to_addr.split(",") if addr.strip()]
        for recipient in recipients:
            logger.info("Sending email to %s", recipient)
            send_email_with_image(
                to_addr=recipient,
                subject=f"Weg: {weg_production} kWh, II: {inversor2} kWh",
                body=(
                    f"WEG production (kWh): {weg_production}\n"
                    f"Saj production (kWh): {saj_production}\n"
                    f"Solis production (kWh): {solis_production}\n"
                    f"Growatt production (kWh): {growatt_production}\n"
                    f"Screenshot: {weg_shot.name} (attached)\n"
                    f"Screenshot: {saj_shot.name} (attached)\n"
                    f"Screenshot: {solis_shot.name} (attached)\n"
                ),
                image_path=[weg_shot, saj_shot, solis_shot],
                smtp_host=secret_or_env("SMTP_HOST"),
                smtp_port=int(secret_or_env("SMTP_PORT") or "587"),
                smtp_user=smtp_user,
                smtp_password=smtp_password,
                from_addr=secret_or_env("EMAIL_FROM") or smtp_user,
            )
            logger.info("Email sent to %s", recipient)