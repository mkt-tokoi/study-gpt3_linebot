import openai

from app.conf_and_cert import OPENAI_API_KEY
from app.linebot_handlers import webhook_handler, linebot_api
from linebot.models import MessageEvent
from linebot.models import (BoxComponent, BubbleContainer, FlexSendMessage,
                            ImageComponent, TextComponent, TextSendMessage, URIAction)

openai.api_key = OPENAI_API_KEY

conversations = {}
@webhook_handler.add(MessageEvent)
def handle_message(event: MessageEvent):

    line_user_id = event.source.user_id
    user_msg = event.message.text

    if(user_msg in {"reset", "リセット"}):
        reset_conversation(line_user_id)
        response = TextSendMessage(text='(会話をリセットしました)')
    else:
        # 会話を更新（ユーザ発言）
        add_user_msg_to_conversation(line_user_id, user_msg )
        conversation = get_conversation(line_user_id)
        conversation = conversation + "\n" + f"AI: "

        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=conversation,
            max_tokens=1000,
            temperature=0.9, # ランダムさ。創造的にするには0.9、答えがある場合は0推奨。top_pと同時変更は非推奨（デフォルト:1）
            stop='.')
        r_text = response['choices'][0]['text']
        token_usage = response['usage']['total_tokens']
        token_remain = 4000 - token_usage

        # 会話を更新（AI発言）
        add_ai_msg_to_conversation(line_user_id, r_text)
        if token_remain < 1000:
            response = TextSendMessage(text=r_text + f"\n(残トークン: {token_remain} です。'リセット'と入力すると会話をリセットできます)")
        else:
            response = TextSendMessage(text=r_text)

    # 応答する
    linebot_api.reply_message(event.reply_token, response)


def reset_conversation(line_user_id):
    if line_user_id in conversations:
        del conversations[line_user_id]

def check_conversation(line_user_id):
    if line_user_id not in conversations:
        conversations[line_user_id] = f""


def get_conversation(line_user_id):
    check_conversation(line_user_id)
    return conversations[line_user_id]


def add_ai_msg_to_conversation(line_user_id, ai_msg):
    user_name = get_user_name(line_user_id)
    check_conversation(line_user_id)
    conversations[line_user_id] = conversations[line_user_id] + "/n" + f"AI: " + ai_msg


def add_user_msg_to_conversation(line_user_id, usr_msg):
    user_name = get_user_name(line_user_id)
    check_conversation(line_user_id)
    conversations[line_user_id] = conversations[line_user_id] + "/n" + f"{user_name}: " + usr_msg


def get_user_name(line_user_id):
    try:
        profile = linebot_api.get_profile(line_user_id)
        return profile.display_name
    except:
        return f"{line_user_id[:3]}さん"
