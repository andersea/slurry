from ..sections.abc import AsyncSection

class TrioSection(AsyncSection):
    async def pump(self, input, output):
        await self.refine(input, output)
