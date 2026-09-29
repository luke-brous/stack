from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from stack.app.db import create_database_engine
from stack.app.models import Base, Vitamin, VitaminLog


def test_deleting_vitamin_cascades_to_logs() -> None:
    engine = create_database_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        vitamin = Vitamin(name="Vitamin D", dose_amount=1000, dose_unit="IU")
        vitamin.logs.append(VitaminLog(taken_at=datetime.now(UTC)))
        session.add(vitamin)
        session.commit()

        session.delete(vitamin)
        session.commit()

        assert session.scalar(select(VitaminLog)) is None
