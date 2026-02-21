# Gomoku Server

五子棋多人即時對戰後端，使用 FastAPI + WebSocket，透過 Docker 運行。

## 快速啟動

```bash
# 啟動
docker compose up -d

# 確認啟動成功（應回傳 {"status":"ok"}）
curl http://localhost:8000/health

# 看 log
docker compose logs -f

# 停止
docker compose down
```

Server 啟動後會在 `http://localhost:8000` 提供服務。

## 開發流程

改 `.py` 檔案後 uvicorn **自動重啟**，不需手動操作。

只有改了 `requirements.txt` 才需要重建 image：

```bash
docker compose up -d --build
```

### 跑測試

```bash
docker compose exec app pytest tests/ -v
```

### IDE 支援（可選）

建本機 venv 讓 IDE 有 autocomplete，實際程式仍跑在 Docker 內：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 專案結構

```
app/
├── main.py          # FastAPI 入口、CORS、GET /health
├── models.py        # WebSocket 訊息型別（Pydantic models）
├── room.py          # 房間管理（建立/加入/離開/斷線重連/計時器）
├── game.py          # 棋盤邏輯（15×15、落子驗證、勝負判定）
└── ws_handler.py    # WebSocket /ws endpoint、訊息路由
tests/
├── test_game.py     # 遊戲邏輯單元測試
├── test_room.py     # 房間生命週期測試
└── test_ws.py       # WebSocket 整合測試
```

## WebSocket 訊息協議

連線位址：`ws://localhost:8000/ws`

### Client → Server

| type | 說明 | 額外欄位 |
|------|------|----------|
| `create_room` | 建立房間 | — |
| `join_room` | 加入房間 | `room_id` |
| `place_stone` | 落子 | `row`, `col` |
| `leave_room` | 離開房間 | — |
| `reconnect` | 斷線重連 | `room_id`, `player_token` |

### Server → Client

| type | 說明 | 額外欄位 |
|------|------|----------|
| `room_created` | 房間已建立 | `room_id`, `player_token`, `color` |
| `player_joined` | 對手加入 | `color` |
| `game_started` | 遊戲開始 | `your_color` |
| `stone_placed` | 落子廣播 | `row`, `col`, `color`, `next_turn` |
| `game_over` | 遊戲結束 | `winner`, `reason` |
| `state_sync` | 完整狀態同步 | `board`, `current_turn`, `move_count`, `your_color`, `timer_remaining` |
| `turn_timer` | 倒數計時 | `remaining` |
| `opponent_disconnected` | 對手斷線 | — |
| `opponent_reconnected` | 對手重連 | — |
| `error` | 錯誤訊息 | `message` |

## 遊戲規則

- 15×15 棋盤，黑棋先手
- 四方向（橫、直、↘、↗）任一方向連成五子即獲勝
- 每步 30 秒倒數，超時自動判負
- 棋盤下滿 225 手為平手
- 斷線後 60 秒內可用 `player_token` 重連，超時視為棄賽

## 環境變數

參考 `.env.example`：

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174` | 允許的前端來源（逗號分隔） |
