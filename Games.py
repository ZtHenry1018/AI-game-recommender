from openai import OpenAI
import json
import re
import os

print("DEBUG KEY:", os.getenv("OPENAI_API_KEY"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://robust-courage-production-12e0.up.railway.app/",  # 可以随便填
        "X-Title": "AI Game Recommender"
    }
)

def get_completion(prompt):

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        timeout=60,
        temperature=0.3
    )

    return response.choices[0].message.content

try:
    with open("games.json", "r", encoding="utf-8") as f:
        games = json.load(f)
except:
    games = []

def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

    print("⚠️ JSON解析失败：", text)
    return {}


def save_games():
    import os

    print("💾 正在保存...")
    print("当前路径：", os.getcwd())
    print("当前games数量：", len(games))
    print("当前games内容：", games)

    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    print("✅ 保存完成")

def generate_game_info(game_name):

    prompt = f"""
你是一个游戏数据库助手。

请根据游戏名称补全信息：

游戏名：
{game_name}

输出JSON：

{{
  "name": "",
  "genre": "",
  "playtime": "",
  "features": "",
  "audience": "",
}}

要求：

- genre 用英文（RPG / Action / Sports 等）
- playtime 用小时（如30h+ / 50h+ / 无限）
- features 用数组（如"开放世界", "剧情"）
- audience 简单描述（竞技玩家 / 休闲玩家 / 硬核玩家）

只输出JSON，不要解释。
"""

    result = get_completion(prompt)

    return safe_json_parse(result)

def normalize_name(name):
    return name.lower().replace(" ", "").replace("-", "")

def is_duplicate_fuzzy(game_name, games):

    new_name = normalize_name(game_name)

    for game in games:
        existing_name = normalize_name(game["name"])

        if new_name in existing_name or existing_name in new_name:
            return True

    return False

def add_game_auto():

    game_name = input("\n请输入游戏名：")

    # ⭐先检测重复
    if is_duplicate_fuzzy(game_name, games):
        print("⚠️ 该游戏已存在，不能重复添加")
        return

    print("🤖 AI正在补全信息...")

    new_game = generate_game_info(game_name)

    print("\n生成结果：")
    print(new_game)

    confirm = input("是否保存？(y/n)：")

    if confirm != "y":
        print("取消添加")
        return

    games.append(new_game)
    save_games()

    print(f"✅ 已添加：{game_name}")

def input_guard(user_input):

    prompt = f"""
判断以下用户输入是否属于“游戏推荐相关请求”。

如果是：
返回 JSON：
{{"valid": true}}

如果不是：
返回 JSON：
{{"valid": false, "reason": "原因"}}

用户输入：
{user_input}

只输出JSON，不要解释。
"""

    result = get_completion(prompt)

    return json.loads(result)

def analyze_request(user_input):

    prompt = f"""
分析用户的游戏需求：

用户输入：
{user_input}

输出JSON：

{{
  "genre": ["", ""],
  "playtime": ["", ""],
  "features": ["", ""],
  "audience": ["", ""]
}}

要求：
- 每个字段可以有多个关键词
- genre用常见英文表达（类似：RPG / Action / Sports / Puzzle）
- playtime用小时表达（类似：15h+ / 30h+ / 无限）
- features总体用常见表达（类似：开放世界 / 剧情 / 竞技 / 射击）
- audience用某种玩家表达（类似：硬核玩家 / 休闲玩家 / 竞技玩家）
- 没有就空数组

只输出JSON
"""

    result = get_completion(prompt)

    return safe_json_parse(result)

def match_any(keywords, text):

    if not keywords:
        return False

    # 如果 target 是字符串 → 转成 list
    if isinstance(text, str):
        text = [text]

    for k in keywords:
        for t in text:
            if k.lower() in t.lower():
                return True

    return False

def retrieve_games(games, filters):

    results = []

    for game in games:

        score = 0

        if match_any(filters.get("genre", []), game["genre"]):
            score += 1

        if match_any(filters.get("playtime", []), game["playtime"]):
            score += 1

        if match_any(filters.get("features", []), game["features"]):
            score += 1

        if match_any(filters.get("audience", []), game["audience"]):
            score += 1

        # ⭐关键：只要命中一个就留下
        if score >= 1:
            game_copy = game.copy()
            game_copy["match_score"] = score
            results.append(game_copy)

    return results

def evaluate_games(candidate_games, user_input):

    prompt = f"""
你是一名资深游戏玩家。

用户需求：
{user_input}

候选游戏：
{candidate_games}

请对每个游戏进行评估：

1 是否推荐（true/false）
2 推荐评分（1-10）
3 推荐理由（简短）

输出JSON：

[
  {{
    "name": "",
    "recommend": true,
    "score": "",
    "reason": "..."
  }}
]

只输出JSON。
"""

    result = get_completion(prompt)

    return safe_json_parse(result)

def get_top_games(evaluated_games):

    # 1 只保留推荐的
    valid = [g for g in evaluated_games if g.get("recommend")]

    # 2 按评分排序
    valid.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 3 取前3个
    return valid[:3]

def recommend_games(user_input):

    # Step 0 输入检测
    guard = input_guard(user_input)

    if not guard["valid"]:
        return {
            "status": "invalid",
            "reason": guard["reason"]
        }

    # Step 1 解析
    filters = analyze_request(user_input)

    # Step 2 检索
    candidate_games = retrieve_games(games, filters)

    if not candidate_games:
        return {
            "status": "no_result",
            "message": "没有匹配游戏"
        }

    # Step 3 AI评估
    evaluated = evaluate_games(candidate_games, user_input)

    # Step 4 排序
    top_games = get_top_games(evaluated)

    return {
        "status": "success",
        "games": top_games
    }

if __name__ == "__main__":
    while True:
        user_input = input("\n请输入你的游戏需求（输入add添加游戏入库/输入 exit 退出）：")
        if user_input.lower() == "exit":
            print("已退出")
            break

        if user_input == "add":
            add_game_auto()
            continue

        result = recommend_games(user_input)

    # 👇 根据状态输出
        if result["status"] == "invalid":
            print("❌ 输入不合法：", result["reason"])

        elif result["status"] == "no_result":
            print("❌ 没有匹配游戏")

        elif result["status"] == "success":
            print("\n🎮 最终推荐（Top3）：\n")

            for g in result["games"]:
                print(f"{g['name']}（评分：{g['score']}）")
                print(f"理由：{g['reason']}")
                print("-" * 30)


    


   
    