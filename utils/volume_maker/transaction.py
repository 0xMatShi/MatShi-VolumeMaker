import os
import base64
import aiohttp
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig
from solders.commitment_config import CommitmentLevel
from solders.hash import Hash
from dotenv import load_dotenv

load_dotenv()
RPC_URL = os.getenv("RPC_URL")
JUP_BASE = os.getenv("JUPITER_QUOTE_URL")
SWAP_URL = os.getenv("JUPITER_SWAP_URL")

# === Получить котировку у Jupiter ===
async def get_quote(session, input_mint: str, output_mint: str,
                    amount_in: int, slippage_bps: int = 50):
    """
    amount_in - в минимальных единицах (lamports/wei)
    slippage_bps - слиппейдж в базисных пунктах (50 = 0.5%)
    """
    url = (
        f"{JUP_BASE}/quote?"
        f"inputMint={input_mint}&outputMint={output_mint}"
        f"&amount={amount_in}&slippageBps={slippage_bps}"
    )
    async with session.get(url) as r:
        return await r.json()

# === Получить готовую транзакцию у Jupiter ===
async def get_swap_tx(session, quote: dict, user_pubkey: str):
    payload = {
        "quoteResponse": quote,
        "userPublicKey": user_pubkey,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
    }
    async with session.post(SWAP_URL, json=payload) as resp:
        return await resp.json()

async def sign_and_send_swap(session: aiohttp.ClientSession, swap_b64: str, privkey_base58: str):
    """
    swap_b64  - base64 строка с VersionedTransaction, которую вернул Jupiter
    privkey_base58 - приватный ключ отправителя в base58 (64 bytes Keypair)
    Возвращает RPC-ответ (dict)
    """
    # 1) decode base64 -> bytes
    tx_bytes = base64.b64decode(swap_b64)

    # 2) распарсить "сырую" версию транзакции
    # VersionedTransaction.from_bytes(...) возвращает объект, у которого есть .message
    vt_raw = VersionedTransaction.from_bytes(tx_bytes)

    # 3) извлечь message (тот самый MessageV0 внутри)
    try:
        message = vt_raw.message
    except Exception as e:
        raise RuntimeError(f"Не удалось получить message из VersionedTransaction: {e}")

    # 4) создать Keypair из base58 (попробуем два варианта)
    try:
        kp = Keypair.from_base58_string(privkey_base58)
    except Exception:
        import base58 as b58
        kp = Keypair.from_bytes(b58.b58decode(privkey_base58))

    # 5) создать новый VersionedTransaction с message и списком ключей — конструктор подпишет транзакцию
    signed_tx = VersionedTransaction(message, [kp])

    # 6) сформировать RPC-пэйлоад и отправить в RPC
    send_req = SendVersionedTransaction(
        signed_tx,
        RpcSendTransactionConfig(
            preflight_commitment=CommitmentLevel.Confirmed
            )
    )

    async with session.post(
        RPC_URL,
        data=send_req.to_json(),
        headers={"Content-Type": "application/json"}
    ) as resp:
        return await resp.json()

# === RPC helpers ===
async def get_token_balance(session: aiohttp.ClientSession, owner: str, mint: str) -> int:
    """Возвращает баланс токена в минимальных единицах (без деления на decimals)."""
    # 1. Получаем токен-аккаунт
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            owner,
            {"mint": mint},
            {"encoding": "jsonParsed"}
        ]
    }
    async with session.post(RPC_URL, json=payload) as resp:
        data = await resp.json()

    accounts = data.get("result", {}).get("value", [])
    if not accounts:
        return 0

    # Берём первый найденный токен-аккаунт
    token_acc = accounts[0]["pubkey"]

    # 2. Получаем баланс
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountBalance",
        "params": [token_acc]
    }
    async with session.post(RPC_URL, json=payload) as resp:
        data = await resp.json()

    try:
        amount = int(data["result"]["value"]["amount"])
    except Exception:
        amount = 0
    return amount

async def get_sol_balance(session: aiohttp.ClientSession, owner: str) -> int:
    """
    Возвращает баланс SOL в лампортах (1 SOL = 1_000_000_000 lamports)
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [owner]
    }
    async with session.post(RPC_URL, json=payload) as resp:
        data = await resp.json()
    return int(data.get("result", {}).get("value", 0))
