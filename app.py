from fastapi import FastAPI
from pydantic import BaseModel
from Games import recommend_games, add_game_auto, generate_game_info, save_games, games

app = FastAPI()

class RequestData(BaseModel):
    user_input: str

class GameData(BaseModel):
    name: str

@app.post("/recommend")
def recommend(data: RequestData):
    return recommend_games(data.user_input)


# ✅ 新增：添加游戏接口
@app.post("/add_game")
def add_game(data: GameData):

    # AI补全信息
    new_game = generate_game_info(data.name)

    # 加入库
    games.append(new_game)
    save_games()

    return {
        "status": "success",
        "game": new_game
    }