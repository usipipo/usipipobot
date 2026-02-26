#!/usr/bin/env python3
"""
Example script demonstrating the TronDealer API integration.
This script shows how to:
1. Initialize the TronDealerClient with an API key
2. Assign a new BSC wallet
3. Get wallet balances
4. Get transaction history
5. Use the WalletManagementService
"""

import asyncio
from config import settings
from infrastructure.api_clients.client_tron_dealer import (
    TronDealerClient,
    TransactionStatus,
)
from application.services.wallet_management_service import WalletManagementService
from application.services.common.container import get_container


async def main():
    # First, let's test the TronDealerClient directly
    print("=== Testing TronDealerClient ===")

    # Get API key from settings
    api_key = settings.TRON_DEALER_API_KEY
    if not api_key:
        print("❌ TRON_DEALER_API_KEY not configured in .env file")
        return

    # Initialize client
    client = TronDealerClient(api_key=api_key)

    try:
        # Test 1: Assign a new wallet with label
        print("\n1. Assigning new wallet...")
        async with client as api_client:
            wallet = await api_client.assign_wallet(label="test-wallet-123")

        print(f"✅ Wallet created: {wallet.address}")
        print(f"   ID: {wallet.id}")
        print(f"   Label: {wallet.label}")
        print(f"   Status: {wallet.status}")
        print(f"   Created At: {wallet.created_at}")

        # Test 2: Get wallet balance
        print("\n2. Getting wallet balance...")
        async with client as api_client:
            balance = await api_client.get_balance(wallet.address)

        print(f"✅ Balance for {balance.address}")
        print(f"   BNB: {balance.bnb}")
        print(f"   USDT: {balance.usdt}")
        print(f"   USDC: {balance.usdc}")

        # Test 3: Get transaction history (with limit)
        print("\n3. Getting transaction history...")
        async with client as api_client:
            transactions = await api_client.get_transactions(
                wallet.address, limit=10, status=TransactionStatus.CONFIRMED
            )

        print(f"✅ Found {transactions.total} transactions")
        print(f"   Limit: {transactions.limit}")
        print(f"   Offset: {transactions.offset}")

        if transactions.transactions:
            print("\nTransaction History:")
            for tx in transactions.transactions:
                print(f"- {tx.asset}: {tx.amount} from {tx.from_address[:10]}...")
                print(f"  Hash: {tx.tx_hash[:10]}...")
                print(f"  Status: {tx.status}")
                print()
        else:
            print("📭 No transactions found")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        print(traceback.format_exc())

    # Now let's test the WalletManagementService through dependency injection
    print("\n=== Testing WalletManagementService ===")

    try:
        container = get_container()
        wallet_service = container.resolve(WalletManagementService)

        print("\n1. Getting or creating wallet for user 12345...")
        # Create a mock user (in real usage, you'd get from user_repo)
        from domain.entities.user import User

        user = User(telegram_id=12345, wallet_address=None)

        bsc_wallet = await wallet_service.get_or_create_wallet(user)

        if bsc_wallet:
            print(f"✅ Wallet: {bsc_wallet.address}")

            # Get balance
            balance = await wallet_service.get_wallet_balance(user)
            if balance:
                print(f"Balance: {balance.usdt} USDT")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
