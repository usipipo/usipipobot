from pathlib import Path

import qrcode

from config import settings
from utils.logger import logger


class QrGenerator:
    @staticmethod
    def generate_vpn_qr(data: str, filename: str) -> str:
        """Genera un QR a partir de la configuración y devuelve la ruta del archivo."""
        try:
            qr_path = Path(settings.QR_CODE_PATH)
            qr_path.mkdir(parents=True, exist_ok=True)

            file_full_path = qr_path / f"{filename}.png"

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(str(file_full_path))

            return str(file_full_path)
        except Exception as e:
            logger.error(f"Error generando QR: {e}")
            return ""

    @staticmethod
    def save_conf_file(content: str, filename: str) -> str:
        """Guarda el contenido en un archivo .conf para enviarlo por Telegram."""
        try:
            conf_path = Path(settings.CLIENT_CONFIGS_PATH)
            conf_path.mkdir(parents=True, exist_ok=True)

            file_full_path = conf_path / f"{filename}.conf"
            file_full_path.write_text(content)

            return str(file_full_path)
        except Exception as e:
            logger.error(f"Error guardando archivo .conf: {e}")
            return ""

    @staticmethod
    def generate_payment_qr(
        wallet_address: str, amount: float, chain_id: int = 56, filename: str = ""
    ) -> str:
        """
        Genera un QR para pago crypto usando formato EIP-681.
        Compatible con BSC (chain_id=56) y wallets como Trust Wallet, MetaMask.

        Args:
            wallet_address: Dirección de la billetera BSC
            amount: Monto en USDT
            chain_id: ID de la cadena (56 para BSC)
            filename: Nombre del archivo (opcional)

        Returns:
            str: Ruta del archivo QR generado
        """
        try:
            # USDT contract en BSC
            usdt_contract = "0x55d398326f99059fF775485246999027B3197955"

            # Formato EIP-681 para transferencia de ERC20
            # ethereum:<contract_address>@<chain_id>/transfer?address=<recipient>&uint256=<amount>
            # El amount debe estar en wei (6 decimales para USDT)
            amount_wei = int(amount * 1_000_000)

            qr_data = (
                f"ethereum:{usdt_contract}@{chain_id}/transfer?"
                f"address={wallet_address}&uint256={amount_wei}"
            )

            qr_path = Path(settings.QR_CODE_PATH)
            qr_path.mkdir(parents=True, exist_ok=True)

            if not filename:
                import uuid
                filename = f"payment_{uuid.uuid4().hex[:8]}"

            file_full_path = qr_path / f"{filename}.png"

            qr = qrcode.QRCode(version=3, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(str(file_full_path))

            logger.info(f"💳 QR de pago generado: {file_full_path}")
            return str(file_full_path)
        except Exception as e:
            logger.error(f"Error generando QR de pago: {e}")
            return ""

    @staticmethod
    def cleanup_old_qr_files(max_age_hours: int = 24) -> int:
        """
        Elimina archivos QR antiguos para liberar espacio.

        Args:
            max_age_hours: Edad máxima en horas para mantener archivos

        Returns:
            int: Cantidad de archivos eliminados
        """
        try:
            from datetime import datetime, timedelta

            qr_path = Path(settings.QR_CODE_PATH)
            if not qr_path.exists():
                return 0

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0

            for file_path in qr_path.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"🧹 {deleted_count} archivos QR antiguos eliminados")
            return deleted_count
        except Exception as e:
            logger.error(f"Error limpiando archivos QR: {e}")
            return 0
