# Copyright (c) 2020 Tulir Asokan
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import List, Callable, Awaitable
from abc import ABC

from mautrix.types import RoomID, UserID
from mautrix.crypto import StateStore

from ..portal import BasePortal
from .mx_user_profile import UserProfile

GetPortalFunc = Callable[[RoomID], Awaitable[BasePortal]]


class BaseCryptoStateStore(StateStore, ABC):
    get_portal: GetPortalFunc

    def __init__(self, get_portal: GetPortalFunc):
        self.get_portal = get_portal

    async def is_encrypted(self, room_id: RoomID) -> bool:
        portal = await self.get_portal(room_id)
        return portal.encrypted if portal else False


class SQLCryptoStateStore(BaseCryptoStateStore):
    @staticmethod
    async def find_shared_rooms(user_id: UserID) -> List[RoomID]:
        return [profile.user_id for profile in UserProfile.find_rooms_with_user(user_id)]


try:
    from mautrix.util.async_db import Database


    class PgCryptoStateStore(BaseCryptoStateStore):
        db: Database

        def __init__(self, db: Database, get_portal: GetPortalFunc) -> None:
            super().__init__(get_portal)
            self.db = db

        async def find_shared_rooms(self, user_id: UserID) -> List[RoomID]:
            rows = await self.db.fetch("SELECT room_id FROM mx_user_profile "
                                       "LEFT JOIN portal ON portal.mxid=mx_user_profile.room_id "
                                       "WHERE user_id=$1 AND portal.encrypted=true", user_id)
            return [row["room_id"] for row in rows]
except ImportError:
    Database = None
    PgStateStore = None
