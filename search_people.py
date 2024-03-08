from dataclasses import dataclass
import requests
import json
import asyncio

from openai import OpenAI

# cannot import name 'Iterator' from 'typing_extensions' の場合下記参照
# https://stackoverflow.com/questions/77922817/importerror-cannot-import-name-iterator-from-typing-extensions/77922914#77922914

client = OpenAI(api_key = "YOUR API KEY HERE")

search_service_name = 'recommend-people'
api_version = '2023-10-01-Preview'
SEARCH_SEARVICE_API_KEY = 'YOUR Azure AI Search API KEY HERE'

index_name = 'people-index-2'
# semanticConfiguration = 'semantic-config-vector-20240206-ja-analyzer-1536-2'
QUERY = '生物学の知識を持つ人と繋がりたい'

api_url = f"https://{search_service_name}.search.windows.net/indexes/{index_name}/docs/search?api-version={api_version}"

headers = {
    "Content-Type": "application/json",
    "api-key": SEARCH_SEARVICE_API_KEY
}

@dataclass
class SearchPeople():
    top_k: int = 6

    def search_people(self, query: str):
    # ベクトル検索のみ
        payload = {
            "vectorQueries": [
                {
                    "kind": "text",
                    "text": query,
                    "fields": "strength_vector",
                    "k": self.top_k
                }
            ],
            "select": "name, belongings, will, want, strength",
        }

        response = requests.post(api_url, headers=headers, data=json.dumps(payload))

        # "belongings": belongings,
        # "will": will,
        # "strength": strength,
        # "want": want,

        if response.status_code == 200:

            response_data = response.json()

        return response_data.get('value', [])