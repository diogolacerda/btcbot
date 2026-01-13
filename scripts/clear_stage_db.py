#!/usr/bin/env python3
"""Script para limpar tabelas activity_events e trades do banco stage."""

import asyncio

from dotenv import load_dotenv
from sqlalchemy import delete, func, select

from src.database.engine import get_engine, get_session_maker
from src.database.models.activity_event import ActivityEvent
from src.database.models.trade import Trade


async def clear_tables():
    """Limpa todas as tabelas especificadas do banco de dados stage."""

    load_dotenv(".env.stage")

    print("Conectando ao banco de dados stage...")
    engine = get_engine(echo=True)
    session_maker = get_session_maker(engine)

    async with session_maker() as session:
        try:
            print("\nContando registros em activity_events...")
            count1 = await session.execute(select(func.count()).select_from(ActivityEvent))
            events_count = count1.scalar()
            print(f"📊 {events_count} registros encontrados em activity_events")

            print("\nLimpando tabela activity_events...")
            await session.execute(delete(ActivityEvent))
            print("✅ activity_events limpa")

            print("\nContando registros em trades...")
            count2 = await session.execute(select(func.count()).select_from(Trade))
            trades_count = count2.scalar()
            print(f"📊 {trades_count} registros encontrados em trades")

            print("\nLimpando tabela trades...")
            await session.execute(delete(Trade))
            print("✅ trades limpa")

            await session.commit()
            print(f"\n✅ {events_count} registros deletados de activity_events")
            print(f"✅ {trades_count} registros deletados de trades")
            print("\n✅ Todas as operações foram concluídas com sucesso!")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Erro ao limpar tabelas: {e}")
            raise
        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(clear_tables())
