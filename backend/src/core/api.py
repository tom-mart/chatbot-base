from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from langchain_chat.api import router as langchain_chat_router
from notifications.api import router as notifications_router
from files.api import router as files_router

api = NinjaExtraAPI()

api.register_controllers(NinjaJWTDefaultController)

api.add_router("/langchain-chat/", langchain_chat_router)
api.add_router("/notifications/", notifications_router)
api.add_router("/files/", files_router)