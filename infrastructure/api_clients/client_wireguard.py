import asyncio
import ipaddress
import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import settings
from utils.logger import logger


class WireGuardClient:
    """
    Cliente de infraestructura para gestionar WireGuard nativo.
    """

    def __init__(self):
        self.interface = settings.WG_INTERFACE or "wg0"
        self.base_path = Path(settings.WG_PATH or "/etc/wireguard")
        self.conf_path = self.base_path / f"{self.interface}.conf"
        self.clients_dir = self.base_path / "clients"
        self.default_quota = 10 * 1024 * 1024 * 1024
        self._permissions_checked = False

        # Cache for get_usage results to prevent race conditions
        self._usage_cache: Optional[Tuple[List[Dict], datetime]] = None
        self._cache_ttl = timedelta(seconds=10)  # Cache for 10 seconds
        self._cache_lock = asyncio.Lock()

        os.makedirs(self.clients_dir, exist_ok=True)

    async def _run_cmd(
        self, cmd: str, require_admin: bool = False, retries: int = 2
    ) -> str:
        """
        Ejecuta comandos de WireGuard con reintentos para errores transitorios.

        Uses synchronous subprocess.run wrapped in asyncio.to_thread for compatibility
        with all event loop implementations (including uvloop).

        Args:
            cmd: Comando a ejecutar
            require_admin: Si True, verifica permisos antes de ejecutar
            retries: Número de reintentos para errores transitorios
        """

        def run_sync() -> str:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Exit code: {result.returncode}"

                if "Operation not permitted" in error_msg:
                    raise PermissionError(
                        "WireGuard requiere CAP_NET_ADMIN. "
                        "Ejecuta: sudo setcap cap_net_admin+ep /usr/bin/wg"
                    )
                raise Exception(f"Error ejecutando comando WireGuard: {error_msg}")
            return result.stdout.strip()

        last_error = None

        for attempt in range(retries + 1):
            try:
                return await asyncio.to_thread(run_sync)

            except PermissionError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Excepción en comando WG (intento {attempt + 1}): {type(e).__name__}: {e}"
                )
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue

        raise last_error or Exception("Error desconocido ejecutando comando WireGuard")

    async def _check_permissions(self) -> bool:
        """Verifica si tenemos permisos para gestionar WireGuard."""
        try:
            await self._run_cmd(f"wg show {self.interface}")
            return True
        except PermissionError:
            return False
        except Exception:
            # La interfaz puede no existir, pero si no es error de permisos, está OK
            return True

    async def ensure_permissions(self):
        """Verifica permisos una sola vez al primer uso."""
        if not self._permissions_checked:
            if not await self._check_permissions():
                raise PermissionError(
                    "WireGuard no tiene permisos. Ejecuta:\n"
                    "sudo setcap cap_net_admin+ep /usr/bin/wg"
                )
            self._permissions_checked = True

    async def get_next_available_ip(self) -> str:
        try:
            content = self.conf_path.read_text()
            addr_match = re.search(r"Address\s*=\s*([\d.]+)", content)
            if not addr_match:
                raise Exception("No se encontró la dirección base en wg0.conf")

            network = ipaddress.IPv4Interface(f"{addr_match.group(1)}/24").network
            used_ips = set(re.findall(r"AllowedIPs\s*=\s*([\d.]+)", content))
            server_ip = network.network_address + 1

            for ip in network.hosts():
                str_ip = str(ip)
                if str_ip not in used_ips and str_ip != str(server_ip):
                    return str_ip

            raise Exception("No hay IPs disponibles en el rango de WireGuard")
        except Exception as e:
            logger.error(f"Error calculando IP: {e}")
            raise

    async def create_peer(self, user_id: int, name: str) -> dict:
        await self.ensure_permissions()

        client_name = f"tg_{user_id}_{uuid.uuid4().hex[:4]}"

        priv_key = await self._run_cmd("wg genkey")
        pub_key = await self._run_cmd(f"echo '{priv_key}' | wg pubkey")
        psk = await self._run_cmd("wg genpsk")

        client_ip = await self.get_next_available_ip()
        server_pub_key = settings.WG_SERVER_PUBKEY or await self._run_cmd(
            f"wg show {self.interface} public-key"
        )

        peer_block = (
            f"\n### CLIENT {client_name}\n"
            f"[Peer]\n"
            f"PublicKey = {pub_key}\n"
            f"PresharedKey = {psk}\n"
            f"AllowedIPs = {client_ip}/32\n"
        )

        with open(self.conf_path, "a") as f:
            f.write(peer_block)

        psk_file_path = f"/tmp/{client_name}.psk"
        try:
            with open(psk_file_path, "w") as f:
                f.write(psk)

            cmd = (
                f"wg set {self.interface} peer {pub_key} "
                f"allowed-ips {client_ip}/32 preshared-key {psk_file_path}"
            )
            await self._run_cmd(cmd)
        finally:
            if os.path.exists(psk_file_path):
                os.remove(psk_file_path)

        client_conf = self._build_client_config(
            priv_key, client_ip, server_pub_key, psk
        )
        client_file = self.clients_dir / f"{self.interface}-{client_name}.conf"
        client_file.write_text(client_conf)
        os.chmod(client_file, 0o600)

        return {
            "id": pub_key,
            "name": name,
            "client_name": client_name,
            "ip": client_ip,
            "config": client_conf,
            "file_path": str(client_file),
        }

    def _build_client_config(
        self, priv_key: str, ip: str, server_pub: str, psk: str
    ) -> str:
        dns = f"{settings.WG_CLIENT_DNS_1 or '1.1.1.1'}"
        endpoint = (
            settings.WG_ENDPOINT
            or f"{settings.SERVER_IP}:{settings.WG_SERVER_PORT or '51820'}"
        )

        return f"""[Interface]
PrivateKey = {priv_key}
Address = {ip}/24
DNS = {dns}
MTU = 1420

[Peer]
PublicKey = {server_pub}
PresharedKey = {psk}
Endpoint = {endpoint}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 15
"""

    async def delete_peer(self, pub_key: str, client_name: str) -> bool:
        try:
            content = self.conf_path.read_text()

            pk_pattern = (
                rf"### CLIENT {re.escape(client_name)}.*?PublicKey\s*=\s*([^\n]+)"
            )
            match = re.search(pk_pattern, content, flags=re.DOTALL)

            if match:
                found_pub_key = match.group(1).strip()
                await self._run_cmd(
                    f"wg set {self.interface} peer {found_pub_key} remove"
                )
            elif pub_key:
                await self._run_cmd(f"wg set {self.interface} peer {pub_key} remove")

            pattern = rf"### CLIENT {re.escape(client_name)}.*?(?=\n### CLIENT|\Z)"
            new_content = re.sub(pattern, "", content, flags=re.DOTALL)
            self.conf_path.write_text(new_content.strip() + "\n")

            client_file = self.clients_dir / f"{self.interface}-{client_name}.conf"
            if client_file.exists():
                client_file.unlink()

            return True
        except Exception as e:
            logger.error(f"Error eliminando peer {client_name}: {e}")
            return False

    async def delete_client(self, client_name: str) -> bool:
        return await self.delete_peer(pub_key="", client_name=client_name)

    async def get_peer_metrics(self, client_name: str) -> Dict[str, int]:
        """
        Obtiene métricas para un cliente específico buscando su Public Key
        en el archivo de configuración basándose en el client_name.
        """
        try:
            if not self.conf_path.exists():
                logger.warning(
                    f"Archivo de configuración no encontrado: {self.conf_path}"
                )
                return {"transfer_total": 0}

            content = self.conf_path.read_text()

            pk_pattern = (
                rf"### CLIENT {re.escape(client_name)}.*?PublicKey\s*=\s*([^\n]+)"
            )
            match = re.search(pk_pattern, content, flags=re.DOTALL)

            if not match:
                logger.warning(
                    f"WireGuard: Cliente '{client_name}' no encontrado en configuración "
                    f"({self.conf_path})"
                )
                return {"transfer_total": 0}

            target_pub_key = match.group(1).strip()
            logger.debug(
                f"WireGuard: Cliente '{client_name}' encontrado con PK {target_pub_key[:16]}..."
            )

            all_usage = await self.get_usage()

            for peer in all_usage:
                if peer["public_key"] == target_pub_key:
                    logger.info(
                        f"WireGuard: Métricas para '{client_name}' - "
                        f"RX: {peer['rx']/(1024**2):.2f}MB, "
                        f"TX: {peer['tx']/(1024**2):.2f}MB, "
                        f"Total: {peer['total']/(1024**2):.2f}MB"
                    )
                    return {
                        "transfer_rx": peer["rx"],
                        "transfer_tx": peer["tx"],
                        "transfer_total": peer["total"],
                    }

            logger.warning(
                f"WireGuard: Public key de '{client_name}' no encontrada en wg show "
                f"(posiblemente no hay tráfico aún)"
            )
            return {"transfer_total": 0}

        except Exception as e:
            logger.error(
                f"Error obteniendo métricas específicas para {client_name}: {e}",
                error=e,
            )
            return {"transfer_total": 0}

    async def get_usage(self) -> List[Dict]:
        """Get WireGuard usage metrics with caching to prevent race conditions."""
        async with self._cache_lock:
            if self._usage_cache is not None:
                cached_data, cached_time = self._usage_cache
                if datetime.now() - cached_time < self._cache_ttl:
                    logger.debug("Returning cached WireGuard usage metrics")
                    return cached_data

            try:
                output = await self._run_cmd(f"wg show {self.interface} dump")
                lines = output.split("\n")[1:]

                usage = []
                for line in lines:
                    cols = line.split("\t")
                    if len(cols) >= 7:
                        usage.append(
                            {
                                "public_key": cols[0],
                                "rx": int(cols[5]),
                                "tx": int(cols[6]),
                                "total": int(cols[5]) + int(cols[6]),
                            }
                        )

                self._usage_cache = (usage, datetime.now())
                return usage
            except Exception as e:
                error_msg = (
                    str(e) if str(e) else repr(e) or "Unknown error (empty exception)"
                )
                logger.error(f"Error obteniendo métricas WG: {error_msg}", error=e)
                return []

    async def disable_peer(self, client_name: str) -> bool:
        """
        Deshabilita un peer de WireGuard sin eliminarlo.
        Cambia allowed-ips a 0.0.0.0/32 para bloquear tráfico.
        """
        try:
            if not self.conf_path.exists():
                logger.error(f"Config file not found: {self.conf_path}")
                return False

            content = self.conf_path.read_text()

            pk_pattern = (
                rf"### CLIENT {re.escape(client_name)}.*?PublicKey\s*=\s*([^\n]+)"
            )
            match = re.search(pk_pattern, content, flags=re.DOTALL)

            if not match:
                logger.error(f"Peer not found: {client_name}")
                return False

            pub_key = match.group(1).strip()

            await self._run_cmd(
                f"wg set {self.interface} peer {pub_key} allowed-ips 0.0.0.0/32"
            )

            new_content = content.replace(
                f"### CLIENT {client_name}",
                f"### CLIENT {client_name} [DISABLED]"
            )
            self.conf_path.write_text(new_content)

            logger.info(f"Peer {client_name} disabled successfully")
            return True

        except Exception as e:
            logger.error(f"Error disabling peer {client_name}: {e}")
            return False

    async def enable_peer(self, client_name: str) -> bool:
        """
        Reactiva un peer previamente deshabilitado.
        Restaura allowed-ips desde la configuración.
        """
        try:
            if not self.conf_path.exists():
                logger.error(f"Config file not found: {self.conf_path}")
                return False

            content = self.conf_path.read_text()

            pk_pattern = (
                rf"### CLIENT {re.escape(client_name)}.*?PublicKey\s*=\s*([^\n]+)"
            )
            match = re.search(pk_pattern, content, flags=re.DOTALL)

            if not match:
                logger.error(f"Peer not found: {client_name}")
                return False

            pub_key = match.group(1).strip()

            allowed_ips_pattern = (
                rf"### CLIENT {re.escape(client_name)}.*?AllowedIPs\s*=\s*([\d./]+)"
            )
            ip_match = re.search(allowed_ips_pattern, content, flags=re.DOTALL)

            if not ip_match:
                logger.error(f"AllowedIPs not found for peer: {client_name}")
                return False

            original_ip = ip_match.group(1)

            await self._run_cmd(
                f"wg set {self.interface} peer {pub_key} allowed-ips {original_ip}"
            )

            new_content = content.replace(
                f"### CLIENT {client_name} [DISABLED]",
                f"### CLIENT {client_name}"
            )
            self.conf_path.write_text(new_content)

            logger.info(f"Peer {client_name} enabled successfully")
            return True

        except Exception as e:
            logger.error(f"Error enabling peer {client_name}: {e}")
            return False
