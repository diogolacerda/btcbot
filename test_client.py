#!/usr/bin/env python3
"""
Script de teste manual para validar os métodos do BingXClient.
"""
import asyncio

from config import load_config
from src.client.bingx_client import BingXClient


async def test_get_price(client: BingXClient, symbol: str):
    """Teste: get_price"""
    print("\n" + "="*50)
    print("TESTE: get_price")
    print("="*50)
    try:
        price = await client.get_price(symbol)
        print(f"✅ Sucesso! Preço do {symbol}: ${price:,.2f}")
        return price
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_get_klines(client: BingXClient, symbol: str):
    """Teste: get_klines"""
    print("\n" + "="*50)
    print("TESTE: get_klines")
    print("="*50)
    try:
        df = await client.get_klines(symbol, interval="1h", limit=10)
        print(f"✅ Sucesso! Recebidos {len(df)} candles")
        print("   Últimos 3 candles:")
        print(df[["timestamp", "open", "high", "low", "close"]].tail(3).to_string(index=False))
        return df
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_get_balance(client: BingXClient):
    """Teste: get_balance"""
    print("\n" + "="*50)
    print("TESTE: get_balance")
    print("="*50)
    try:
        balance = await client.get_balance()
        print("✅ Sucesso! Dados do balance:")
        if isinstance(balance, dict):
            available = balance.get("balance", {}).get("availableMargin", "N/A")
            equity = balance.get("balance", {}).get("equity", "N/A")
            print(f"   Available Margin: {available}")
            print(f"   Equity: {equity}")
        else:
            print(f"   Raw: {balance}")
        return balance
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_get_positions(client: BingXClient, symbol: str):
    """Teste: get_positions"""
    print("\n" + "="*50)
    print("TESTE: get_positions")
    print("="*50)
    try:
        positions = await client.get_positions(symbol)
        print(f"✅ Sucesso! Posições encontradas: {len(positions)}")
        for pos in positions:
            if float(pos.get("positionAmt", 0)) != 0:
                print(f"   - {pos.get('symbol')} {pos.get('positionSide')}: {pos.get('positionAmt')} @ {pos.get('avgPrice')}")
        if not positions or all(float(p.get("positionAmt", 0)) == 0 for p in positions):
            print("   (Nenhuma posição aberta)")
        return positions
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_get_open_orders(client: BingXClient, symbol: str):
    """Teste: get_open_orders"""
    print("\n" + "="*50)
    print("TESTE: get_open_orders")
    print("="*50)
    try:
        orders = await client.get_open_orders(symbol)
        print(f"✅ Sucesso! Ordens abertas: {len(orders)}")
        for order in orders[:5]:  # Mostrar até 5
            print(f"   - ID: {order.get('orderId')} | {order.get('side')} {order.get('positionSide')} | Preço: {order.get('price')} | Qtd: {order.get('origQty')}")
        if not orders:
            print("   (Nenhuma ordem aberta)")
        return orders
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_set_leverage(client: BingXClient, symbol: str, leverage: int):
    """Teste: set_leverage"""
    print("\n" + "="*50)
    print("TESTE: set_leverage")
    print("="*50)
    try:
        result = await client.set_leverage(symbol, leverage)
        print(f"✅ Sucesso! Leverage configurado para {leverage}x")
        print(f"   Resposta: {result}")
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_create_simple_limit_order(client: BingXClient, symbol: str, price: float, quantity: float):
    """Teste: create_order (LIMIT simples, sem TP)"""
    print("\n" + "="*50)
    print("TESTE: create_order (LIMIT simples)")
    print("="*50)

    print("   Criando ordem LIMIT BUY LONG:")
    print(f"   - Preço entrada: ${price:,.2f}")
    print(f"   - Quantidade: {quantity}")

    try:
        result = await client.create_order(
            symbol=symbol,
            side="BUY",
            position_side="BOTH",  # One-way mode requires BOTH
            order_type="LIMIT",
            price=price,
            quantity=quantity,
        )
        order_id = result.get("orderId") or result.get("order", {}).get("orderId")
        print("✅ Sucesso! Ordem criada")
        print(f"   Order ID: {order_id}")
        print(f"   Resposta completa: {result}")
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_create_limit_order_with_tp(client: BingXClient, symbol: str, price: float, quantity: float):
    """Teste: create_limit_order_with_tp"""
    print("\n" + "="*50)
    print("TESTE: create_limit_order_with_tp")
    print("="*50)

    # Calcular TP (1% acima do preço de entrada)
    tp_price = round(price * 1.01, 2)

    print("   Criando ordem LIMIT BUY LONG com TP:")
    print(f"   - Preço entrada: ${price:,.2f}")
    print(f"   - Take Profit: ${tp_price:,.2f}")
    print(f"   - Quantidade: {quantity}")

    try:
        result = await client.create_limit_order_with_tp(
            symbol=symbol,
            side="BUY",
            position_side="BOTH",  # One-way mode requires BOTH
            price=price,
            quantity=quantity,
            tp_price=tp_price,
        )
        order_id = result.get("orderId") or result.get("order", {}).get("orderId")
        print("✅ Sucesso! Ordem criada")
        print(f"   Order ID: {order_id}")
        print(f"   Resposta completa: {result}")
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def test_cancel_order(client: BingXClient, symbol: str, order_id: str):
    """Teste: cancel_order"""
    print("\n" + "="*50)
    print("TESTE: cancel_order")
    print("="*50)
    try:
        result = await client.cancel_order(symbol, order_id)
        print(f"✅ Sucesso! Ordem {order_id} cancelada")
        print(f"   Resposta: {result}")
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


async def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("   TESTE MANUAL DO CLIENTE BINGX")
    print("="*60)

    # Carregar configuração
    config = load_config()
    symbol = config.trading.symbol

    print("\nConfiguração:")
    print(f"  - Modo: {'DEMO (VST)' if config.bingx.is_demo else 'LIVE'}")
    print(f"  - Base URL: {config.bingx.base_url}")
    print(f"  - Symbol: {symbol}")
    print(f"  - Leverage: {config.trading.leverage}x")
    print(f"  - Order Size: ${config.trading.order_size_usdt} USDT")

    # Criar cliente
    client = BingXClient(config.bingx)

    try:
        # Teste 1: get_price
        price = await test_get_price(client, symbol)
        if not price:
            print("\n⚠️  Falha crítica: não foi possível obter preço. Abortando.")
            return

        # Teste 2: get_klines
        await test_get_klines(client, symbol)

        # Teste 3: get_balance
        await test_get_balance(client)

        # Teste 4: get_positions
        await test_get_positions(client, symbol)

        # Teste 5: get_open_orders
        await test_get_open_orders(client, symbol)

        # Teste 6: set_leverage
        await test_set_leverage(client, symbol, config.trading.leverage)

        # Teste 7: criar ordem simples (sem TP)
        # Criar ordem bem abaixo do preço atual para não ser executada
        test_price = round(price * 0.95, 2)  # 5% abaixo do preço atual
        test_quantity = 10  # Quantidade menor para teste

        # Retry logic para lidar com "system busy"
        for attempt in range(3):
            order_result = await test_create_simple_limit_order(client, symbol, test_price, test_quantity)
            if order_result:
                break
            print(f"   Tentativa {attempt + 1}/3 falhou, aguardando 3s...")
            await asyncio.sleep(3)

        # Se a ordem simples funcionar, testar com TP
        if order_result:
            order_id = str(order_result.get("orderId") or order_result.get("order", {}).get("orderId", ""))
            if order_id:
                await asyncio.sleep(1)
                await test_cancel_order(client, symbol, order_id)

        # Teste 8: criar ordem com TP
        await asyncio.sleep(1)
        order_result = await test_create_limit_order_with_tp(client, symbol, test_price, test_quantity)

        if order_result:
            order_id = str(order_result.get("orderId") or order_result.get("order", {}).get("orderId", ""))
            if order_id:
                # Aguardar um pouco
                await asyncio.sleep(1)

                # Verificar se a ordem aparece na lista
                print("\n" + "="*50)
                print("VERIFICAÇÃO: ordem aparece em get_open_orders?")
                print("="*50)
                orders = await client.get_open_orders(symbol)
                found = any(str(o.get("orderId")) == order_id for o in orders)
                if found:
                    print(f"✅ Ordem {order_id} encontrada na lista!")
                else:
                    print(f"⚠️  Ordem {order_id} NÃO encontrada na lista")
                    print(f"   Ordens atuais: {[o.get('orderId') for o in orders]}")

                # Cancelar a ordem de teste
                await test_cancel_order(client, symbol, order_id)

        # Resumo final
        print("\n" + "="*60)
        print("   RESUMO DOS TESTES")
        print("="*60)
        print("✅ Testes concluídos!")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
