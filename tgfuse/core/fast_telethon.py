import os
import math
import asyncio
from telethon import TelegramClient
from telethon.network import MTProtoSender
from telethon.tl.functions.upload import SaveFilePartRequest, SaveBigFilePartRequest, GetFileRequest
from telethon.tl.types import InputFile, InputFileBig, InputDocumentFileLocation
import telethon.helpers
from tgfuse.funcs.floodwait import retry_flood_wait

class MTProtoPool:
    def __init__(self, client: TelegramClient, connections: int = 4):
        self.client = client
        self.connections = connections
        self._senders = []
        self._lock = asyncio.Lock()
        self._ready = False

    async def connect(self):
        async with self._lock:
            if self._ready: return
            dc = await self.client._get_dc(self.client.session.dc_id)
            for _ in range(self.connections):
                sender = MTProtoSender(self.client.session.auth_key, loggers=self.client._log)
                await sender.connect(self.client._connection(dc.ip_address, dc.port, dc.id, loggers=self.client._log))
                self._senders.append(sender)
            self._ready = True

    async def disconnect(self):
        async with self._lock:
            for sender in self._senders:
                await sender.disconnect()
            self._senders.clear()
            self._ready = False

    async def upload_file(self, file_path: str, filename: str):
        await self.connect()
        file_size = os.path.getsize(file_path)
        part_size = 512 * 1024
        part_count = math.ceil(file_size / part_size)
        is_large = file_size > 10 * 1024 * 1024
        file_id = telethon.helpers.generate_random_long()

        async def upload_worker(sender, worker_id):
            with open(file_path, "rb") as f:
                for i in range(worker_id, part_count, self.connections):
                    f.seek(i * part_size)
                    data = f.read(part_size)
                    if not data: break
                    req = SaveBigFilePartRequest(file_id, i, part_count, data) if is_large else SaveFilePartRequest(file_id, i, data)
                    
                    async def do_send():
                        return await sender.send(req)
                        
                    await retry_flood_wait(do_send, label=f"upload chunk {i} for {filename}")

        tasks = [upload_worker(self._senders[i], i) for i in range(self.connections)]
        await asyncio.gather(*tasks)
        return InputFileBig(file_id, part_count, filename) if is_large else InputFile(file_id, part_count, filename, "")

    async def download_chunk(self, document, offset: int, limit: int) -> bytes:
        await self.connect()
        part_size = 512 * 1024
        parts = math.ceil(limit / part_size)
        results = [b""] * parts
        
        location = InputDocumentFileLocation(
            id=document.id, access_hash=document.access_hash,
            file_reference=document.file_reference, thumb_size=""
        )

        async def download_worker(sender, worker_id):
            for i in range(worker_id, parts, self.connections):
                chunk_offset = offset + (i * part_size)
                chunk_limit = min(part_size, limit - (i * part_size))
                if chunk_limit <= 0: break
                req = GetFileRequest(location, offset=chunk_offset, limit=chunk_limit)
                
                async def do_fetch():
                    return await sender.send(req)
                    
                res = await retry_flood_wait(do_fetch, label=f"download chunk at {chunk_offset}")
                results[i] = res.bytes

        workers_to_use = min(parts, self.connections)
        tasks = [download_worker(self._senders[i], i) for i in range(workers_to_use)]
        await asyncio.gather(*tasks)
        return b"".join(results)