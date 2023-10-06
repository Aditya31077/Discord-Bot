from typing import List

import aiosqlite


from ..ext import Record, Rank
from ..settings import Info



class Base:
    conn: aiosqlite.Connection

    def __init__(self, table_query: str) -> None:
        self.table_query = table_query

    async def setup(self) -> None:
        self.conn = await aiosqlite.connect(Info.DB_FILE)
        cursor = await self.conn.cursor()
        await cursor.execute(self.table_query)
        await self.conn.commit()
        await cursor.close()

class Experience(Base):
    conn: aiosqlite.Connection

    def __init__(self) -> None:
        super().__init__("CREATE TABLE IF NOT EXISTS exps(user_id INTEGER, guild_id INTEGER, xp INTEGER, level INTEGER)")

    async def all_records(self) -> None | List[Rank]:
        cursor = await self.conn.cursor()
        data = await (await cursor.execute("SELECT * FROM exps")).fetchall()
        await cursor.close()
        return None if not data else [Rank(record[0], record[1], record[2], record[3]) for record in data]
    
    async def all_guild_records(self, guild_id: int, *, raw=False) -> None | List[Rank]:
        cursor = await self.conn.cursor()
        data = await (await cursor.execute("SELECT * FROM exps WHERE guild_id = ?", (guild_id,))).fetchall()
        await cursor.close()
        if raw is True:
            return data
        return None if not data else [Rank(record[0], record[1], record[2], record[3]) for record in data]

    async def read(self, user_id: int, guild_id: int) -> None | Rank:
        cursor = await self.conn.cursor()
        record = await (await cursor.execute('''SELECT * FROM exps WHERE user_id = ? AND guild_id = ?''', (user_id, guild_id,))).fetchone()
        await cursor.close()

        return None if record is None else Rank(record[0], record[1], record[2], record[3])

    async def create(self, user_id: int, guild_id: int, starting_xp: int=5, starting_level: int=1):
        if (check := await self.read(user_id, guild_id)):
            return check
        
        cursor = await self.conn.cursor()
        await cursor.execute('''INSERT INTO exps(user_id, guild_id, xp, level) VALUES(?, ?, ?, ?)''', (user_id, guild_id, starting_xp, starting_level,))
        await self.conn.commit()
        await cursor.close()
        return Rank(user_id, guild_id, starting_xp, starting_level)
        
    async def update(self, user_id: int, guild_id: int, *, xp: int=None, level: int=None) -> bool:
        if not xp and not level:
            return False
        
        cursor = await self.conn.cursor()

        if xp and not level:
            await cursor.execute("UPDATE exps SET xp = ? WHERE user_id = ? AND guild_id = ?", (xp, user_id, guild_id,))
            
        if level and not xp:
            await cursor.execute("UPDATE exps SET level = ? WHERE user_id = ? AND guild_id = ?", (level, user_id, guild_id,))
            
        if xp and level:
            await cursor.execute("UPDATE exps SET xp = ? , level = ? WHERE user_id = ? AND guild_id = ?",(xp,level,user_id, guild_id,))
        
        await self.conn.commit()
        await cursor.close()
        return True


class MessageDB(Base):
    conn: aiosqlite.Connection

    def __init__(self) -> None:
        super().__init__("CREATE TABLE IF NOT EXISTS messages(user_id INTEGER, channel_id INTEGER, message_id INTEGER, guild_id INTEGER, dm_id INTEGER, dm_channel_id INTEGER)")


    async def read_user_message(self, user_id: int, message_id: int) -> None | Record:
        cursor = await self.conn.cursor()
        record = await (await cursor.execute("SELECT * FROM messages WHERE user_id = ? AND message_id = ?", (user_id, message_id,))).fetchone()
        if not record: return None
        return Record(record[2], record[0], record[3], record[1], record[4], record[5])

    async def read_message(self, message_id: int) -> None | List[Record]:
        cursor = await self.conn.cursor()
        records = await (await cursor.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,))).fetchall()
        if not records: return None
        return [Record(record[2], record[0], record[3], record[1], record[4], record[5]) for record in records]

    async def read_user(self, user_id: int) -> None | List[Record]:
        cursor = await self.conn.cursor()
        record = await (await cursor.execute("SELECT * FROM messages WHERE user_id = ?", (user_id,))).fetchall()
        if not record: return None
        return [Record(record[2], record[0], record[3], record[1], record[4], record[5]) for record in record]

    async def create(self, user_id: int, channel_id: int, message_id: int, guild_id: int, dm_id: int, dm_channel_id: int) -> bool | Record:
        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO messages(user_id, channel_id, message_id, guild_id, dm_id, dm_channel_id) VALUES(?, ?, ?, ?, ?, ?)", (user_id, channel_id, message_id, guild_id, dm_id, dm_channel_id,))
        await self.conn.commit()
        return Record(message_id, user_id, guild_id, channel_id, dm_id, dm_channel_id)
    
    async def remove(self, user_id: int, message_id: int) -> bool | Record:
        _check = await self.read_user_message(user_id, message_id)
        if _check is None:
            return False
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM messages WHERE user_id = ? AND message_id = ?", (_check.user_id, _check.message_id,))
        await self.conn.commit()
        return Record(_check.message_id, _check.user_id, _check.guild_id, _check.channel_id, _check.dm_id, _check.dm_channel_id)
    
    async def remove_user(self, user_id: int) -> bool:
        _check = await self.read_user(user_id)
        if _check is None:
            return False
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        await self.conn.commit()
        return True
    
    async def remove_message(self, message_id: int) -> bool:
        _check = await self.read_message(message_id)
        if _check is None:
            return False
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))
        await self.conn.commit()
        return True

class DatabaseManager:
    ranks = Experience()
    messages = MessageDB()

    async def setup(self) -> None:
        await self.ranks.setup()
        await self.messages.setup()