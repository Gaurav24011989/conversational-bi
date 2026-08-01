from fastapi import APIRouter

from app.config import settings
from app.i18n import LOCALE_INFO, get_supported_locales
from app.schemas import LocaleInfo, LocalesResponse

router = APIRouter(prefix="/locales", tags=["locales"])


@router.get("", response_model=LocalesResponse)
async def list_locales() -> LocalesResponse:
    supported = get_supported_locales()
    return LocalesResponse(
        default_locale=settings.default_locale,
        supported_locales=[
            LocaleInfo(
                code=code,
                name=LOCALE_INFO.get(code, {}).get("name", code),
                native_name=LOCALE_INFO.get(code, {}).get("native_name", code),
            )
            for code in supported
        ],
    )
