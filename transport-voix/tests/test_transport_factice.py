import pytest

from app.transport.fake import TransportFactice


@pytest.mark.asyncio
async def test_demarrer_et_arreter_basculent_actif():
    transport = TransportFactice()
    assert transport.actif is False

    await transport.demarrer()
    assert transport.actif is True

    await transport.arreter()
    assert transport.actif is False
