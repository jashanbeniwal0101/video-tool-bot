from typing import Optional, Any, Dict, List
import motor.motor_asyncio

class Database:
    def __init__(self, uri: str, database_name: str):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.user

    @staticmethod
    def new_user(id: int) -> Dict[str, Any]:
        return dict(
            _id=int(id),
            thumb=None,
            caption=None,
            prefix=None,
            suffix=None,
            metadata=False,
        )

    async def add_user(self, b, m):
        """Add user if not exists. Atomic with upsert."""
        u = m.from_user
        result = await self.col.update_one(
            {'_id': int(u.id)},
            {'$setOnInsert': self.new_user(u.id)},
            upsert=True
        )
        if result.upserted_id is not None:
            # Only call send_log if actually inserted
            if 'send_log' in globals():
                await send_log(b, u)

    async def is_user_exist(self, id: int) -> bool:
        return await self.col.count_documents({'_id': int(id)}, limit=1) > 0

    async def total_users_count(self) -> int:
        return await self.col.count_documents({})

    async def get_all_users(self) -> List[Dict[str, Any]]:
        return await self.col.find({}).to_list(length=None)

    async def delete_user(self, user_id: int) -> None:
        await self.col.delete_one({'_id': int(user_id)})

    async def set_thumbnail(self, id: int, file_id: Any) -> None:
        await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id: int) -> Optional[Any]:
        user = await self.col.find_one({'_id': int(id)})
        return user['file_id'] if user and 'file_id' in user else None

    async def set_caption(self, id: int, caption: str) -> None:
        await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id: int) -> Optional[str]:
        user = await self.col.find_one({'_id': int(id)})
        return user['caption'] if user and 'caption' in user else None

    async def set_prefix(self, id: int, prefix: str) -> None:
        await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})

    async def get_prefix(self, id: int) -> Optional[str]:
        user = await self.col.find_one({'_id': int(id)})
        return user['prefix'] if user and 'prefix' in user else None

    async def set_suffix(self, id: int, suffix: str) -> None:
        await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})

    async def get_suffix(self, id: int) -> Optional[str]:
        user = await self.col.find_one({'_id': int(id)})
        return user['suffix'] if user and 'suffix' in user else None

    async def set_metadata(self, id: int, bool_meta: bool) -> None:
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata': bool_meta}})

    async def get_metadata(self, id: int) -> Optional[bool]:
        user = await self.col.find_one({'_id': int(id)})
        return user['metadata'] if user and 'metadata' in user else None

    async def set_metadata_code(self, id: int, metadata_code: Any) -> None:
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata_code': metadata_code}})

    async def get_metadata_code(self, id: int) -> Optional[Any]:
        user = await self.col.find_one({'_id': int(id)})
        return user['metadata_code'] if user and 'metadata_code' in user else None
