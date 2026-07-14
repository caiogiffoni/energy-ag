import json
from datetime import date

from libraries.logger import get_logger
from utils.email_util import send_email_with_image
from utils.secrets_util import secret_or_env

logger = get_logger(__name__)


def _get_gspread_client():
    import gspread

    creds_value = secret_or_env("GOOGLE_CREDENTIALS_JSON")
    if not creds_value:
        return None
    if creds_value.strip().startswith("{"):
        return gspread.service_account_from_dict(json.loads(creds_value))
    return gspread.service_account(filename=creds_value)


def post_to_sheets(weg, saj, solis, growatt):
    sheet_id = secret_or_env("GOOGLE_SHEET_ID")
    if not sheet_id:
        logger.info("GOOGLE_SHEET_ID not set - Sheets post skipped")
        return

    gc = _get_gspread_client()
    if gc is None:
        logger.info("GOOGLE_CREDENTIALS_JSON not set - Sheets post skipped")
        return

    ws = gc.open_by_key(sheet_id).sheet1
    today_str = date.today().strftime("%d/%m/%Y")

    all_rows = ws.get_all_values()
    data_rows = all_rows[1:]  # skip header

    if data_rows and data_rows[-1][0] == today_str:
        row_num = len(all_rows)  # overwrite last row
        logger.info("Today's row already exists - overwriting row %d", row_num)
    else:
        row_num = len(all_rows) + 1  # append new row
        logger.info("Appending new row %d for %s", row_num, today_str)

    # Write A:C (date, weg, formula) and G:I (saj, solis, growatt). D:F stay empty.
    formula = f"=G{row_num}+H{row_num}+I{row_num}"
    ws.update(f"A{row_num}:C{row_num}", [[today_str, weg, formula]], value_input_option="USER_ENTERED")
    ws.update(f"G{row_num}:I{row_num}", [[saj, solis, growatt]])
    logger.info("Posted to Google Sheets row %d", row_num)


def send_generated_energy_email(weg_info: tuple[str, str, str, str], saj_info: tuple[str, str, str, str], solis_info: tuple[str, str, str, str], growatt_info: tuple[str, str, str, str]):
        weg_production, weg_title, weg_shot, weg_notes = weg_info
        saj_production, saj_title, saj_shot, saj_notes = saj_info
        solis_production, solis_title, solis_shot, solis_notes = solis_info
        growatt_production, growatt_title, growatt_shot, growatt_notes = growatt_info
        to_addr = secret_or_env("EMAIL_TO")
        logger.info("Sending emails to %s", to_addr)
        if not to_addr:
            logger.info("EMAIL_TO not set - email skipped")
            return
        smtp_user = secret_or_env("SMTP_USER")
        smtp_password = secret_or_env("SMTP_PASSWORD")
        if not smtp_user or not smtp_password:
            logger.info("SMTP_USER or SMTP_PASSWORD not set - email skipped")
            return
        inversor2 = round(float(saj_production) + float(solis_production) + float(growatt_production), 2)
        post_to_sheets(weg_production, saj_production, solis_production, growatt_production)
        notes_entries = [
            ("weg", weg_notes),
            ("saj", saj_notes),
            ("solis", solis_notes),
            ("growatt", growatt_notes),
        ]
        notes_block = ""
        active_notes = [(name, n.strip()) for name, n in notes_entries if n.strip()]
        if active_notes:
            notes_block = "\nDeveloper Notes:\n" + "\n".join(f"  {name}: {n}" for name, n in active_notes) + "\n"
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
                    f"{notes_block}"
                ),
                image_path=[weg_shot, saj_shot, solis_shot],
                smtp_host=secret_or_env("SMTP_HOST"),
                smtp_port=int(secret_or_env("SMTP_PORT") or "587"),
                smtp_user=smtp_user,
                smtp_password=smtp_password,
                from_addr=secret_or_env("EMAIL_FROM") or smtp_user,
            )
            logger.info("Email sent to %s", recipient)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    post_to_sheets(weg=555.99, saj=555, solis=555, growatt=555)