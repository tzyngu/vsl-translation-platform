from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from core.models import PredictionHistory, TranslationHistory
from ..schemas import TranslateRequest
from ..security import COOKIE_NAME, current_user, decode_access_token
from ..services.llm_translator import translate_labels
from ..services.model_registry import active_model_for_user
from ..services.realtime_predictor import RealtimeSession


router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("/translate")
def translate(payload: TranslateRequest, user=Depends(current_user)):
    result = translate_labels(payload.labels)
    TranslationHistory.objects.create(
        user=user, labels=payload.labels, sentence=result["sentence"], provider=result["provider"]
    )
    return result


@router.websocket("/ws")
async def realtime(websocket: WebSocket):
    token = websocket.query_params.get("token") or websocket.cookies.get(COOKIE_NAME)
    if not token:
        await websocket.close(code=4401)
        return
    try:
        user_id = decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    model_version = await sync_to_async(active_model_for_user)(user_id)
    await websocket.accept()
    session = RealtimeSession(model_version.model_path, model_version.labels_path)
    try:
        while True:
            payload = await websocket.receive_json()
            result = session.process_base64_jpeg(payload["frame"])
            if result.get("accepted_word"):
                await sync_to_async(PredictionHistory.objects.create)(
                    user_id=user_id, label=result["accepted_word"], confidence=result["prediction"]["confidence"]
                )
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
    finally:
        session.close()
