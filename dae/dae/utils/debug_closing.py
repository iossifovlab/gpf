import logging
from contextlib import AbstractContextManager


logger = logging.getLogger(__name__)


LIVE_CONNECTIONS = 0


class closing(AbstractContextManager):
    """Context to automatically close something at the end of a block.

    Code like this:

        with closing(<module>.open(<arguments>)) as f:
            <block>

    is equivalent to this:

        f = <module>.open(<arguments>)
        try:
            <block>
        finally:
            f.close()

    """
    def __init__(self, thing):
        self.thing = thing

    def __enter__(self):
        global LIVE_CONNECTIONS

        LIVE_CONNECTIONS += 1
        logger.info(
            f"[closing] enter {id(self.thing)}; live {LIVE_CONNECTIONS}",
            # stack_info=True
        )
        return self.thing

    def __exit__(self, *exc_info):
        global LIVE_CONNECTIONS
        self.thing.close()

        LIVE_CONNECTIONS -= 1
        logger.info(
            f"[closing] exit {id(self.thing)}; live {LIVE_CONNECTIONS}",
            # stack_info=True
        )

    async def __aenter__(self):
        logger.info("[closing] aenter...")
        return self

    async def __aexit__(self, *exc_details):
        logger.info("[closing] aexit...")

    def close(self):
        self.thing.close()
