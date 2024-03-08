import ast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from search_people import SearchPeople

client = OpenAI(
    api_key = "YOUR API KEY HERE"
)

messages = []

SEARCH_FALSE = 0
SEARCH_TRUE = 1
SEARCH_SPECIFIC = 2

def get_llm_response(messages):
  response = client.chat.completions.create(
    model = 'gpt-4-turbo-preview',
    messages = messages,
    temperature = 0.0
  )
  content = response.choices[0].message.content
  return content

def is_search_people_message(message):
    prompt = f'''
        メッセージが「人を探す」に関するものかどうかを判定してださい。
        ・人を探すに関するメッセージであれば、{{"is_search_people": {SEARCH_TRUE}}} を返してください
        ・人を探すに関係ないメッセージは、{{"is_search_people": {SEARCH_FALSE}}} を返してください
        ・特定の人に関するメッセージは、{{"is_search_people": {SEARCH_SPECIFIC}}} を返してください
        たとえば、以下のようなメッセージが入力された場合は、{{"is_search_people": {SEARCH_TRUE}}}にしてください
        例：
        「人を探しています」
        「人を探すのを手伝ってください」
        「〇〇が得意なエンジニアいる？」
        「〇〇を専門とする人いる？」
        「〇〇のような人と繋がりたい」

        特定の人に関するメッセージは{{"is_search_people": {SEARCH_SPECIFIC}}}を返してください。
        たとえば、
        「〇〇さんについて詳しく教えて」といった場合や、
        「〇〇くんのやっているプロジェクトについて詳しく教えて！」
        「〇〇さんってPythonできる？」といった場合は{{"is_search_people": {SEARCH_SPECIFIC}}}を返してください。

        メッセージ:
        {message}
    '''
    messages = [{'role': 'user', 'content': prompt}]
    llm_response = get_llm_response(messages)
        
    print('llm_response', llm_response)
    is_search_people_str = "False"
    try:
        dict_data = ast.literal_eval(llm_response)
        print('dict_dat_keys', dict_data.keys())
        is_search_people_str = dict_data["is_search_people"]
    except Exception as e:
        print('Error, could not parse is_search_people: ', e)
    is_search_people = int(is_search_people_str)
    print('isSearchPeole', is_search_people)
    print('isSearchPeole type', type(is_search_people))

    return is_search_people

app = FastAPI()
# TODO: デプロイ時にCORSの範囲を設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 全てのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],  # 全てのHTTPメソッドを許可
    allow_headers=["*"],  # 全てのHTTPヘッダを許可
)

def get_people_summary(people_data):
    prompt = f'''
    {people_data}のそれぞれの人物について軽くまとめてください。
    例：
    ### Aさん
    は〇〇が得意で、〇〇ができるので、あなたが求めている人物かと思うのでぜひ話してみてください。
    またBさんは〇〇に興味があるので、同じ分野に興味を持つあなたと話してみてはどうでしょうか？
    といった感じで、それぞれの人物について軽くまとめた上で、紹介してください。

    条件：
    全体の文字数は300文字以内
    '''
    messages = [{'role': 'user', 'content': prompt}]
    llm_response = get_llm_response(messages)
    llm_response += '''\n ### 詳しくは
    チャットで質問してみてね！'''
    return llm_response

# TODO: 後でPOSTに変更
@app.get("/")
async def root(msg):
    print(msg)
    is_search_people = is_search_people_message(msg)
    llm_response = ''
    if is_search_people == SEARCH_TRUE:
        searchPeople = SearchPeople()
        people_data = searchPeople.search_people(msg)
        people_summary = ''
        str_people_data = ''
        if len(people_data) > 0:
            # str_people_data = ",".join(people_data)
            people_summary = get_people_summary(people_data)
        if len(people_data) == 0:
            str_people_data = "該当する人物が見つかりませんでした。"
        messages.append({'role': 'user', 'content': str_people_data}) # コミュマネに聞けるように
        print('people_data', people_data)
        response_data = {"people_data": people_data, "llm_response": people_summary}
        return response_data
    elif is_search_people == SEARCH_FALSE:
        prompt = msg
        messages.append({'role': 'user', 'content': prompt})
        llm_response = get_llm_response(messages)
        messages.append({'role': 'system', 'content': llm_response})
    elif is_search_people == SEARCH_SPECIFIC:
        searchPeople = SearchPeople()
        people_data = searchPeople.search_people(msg)
        str_human_details = ''
        if len(people_data) > 0:
            # str_human_details = ",".join(people_data)
            prompt = f'''
                参考情報を元に、ユーザーからの質問を元に詳しく教えてください。
                参考情報に、ユーザーが聞きたい人物に関する情報がない場合は、その旨を伝えてください。

                ユーザーからの質問：
                {msg}
                参考情報：
                {people_data}
            '''
            str_human_details = get_llm_response(prompt)
        if len(people_data) == 0:
            str_human_details = "該当する人物が見つかりませんでした。"
        response_data = {"llm_response": people_summary}
        return response_data
    else:
        print('Error, is_search_people is not a valid value')
    print(f'llm_response: {llm_response}')
    return {"llm_response": llm_response}

    # TODO: 探す人をAIのコミュマネが提案
