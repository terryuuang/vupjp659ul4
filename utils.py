import re
import os
import time
import threading

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

url_dict = {
    "main_articles": [],
    "supporting_articles": []
}

# openai assistant api 設定
main_assistant_id = 'asst_NeGinXBAF8MXmQZQ4YwUlwPH'
supporting_assistant_id = 'asst_pFPaTVDUMwl5cFc3lzaOCUmV'
api_key = os.getenv('api_key')
organization = os.getenv('organization')


client = OpenAI(
    organization=organization,
    api_key=api_key
)


def analytics_result(data, assistant_id):
    """GPT分析"""
    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=data
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )
        while run.status != "completed":
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        result = client.beta.threads.messages.list(thread.id)
        prompt_tokens = run.usage.prompt_tokens
        completion_tokens = run.usage.completion_tokens

        result_text = result.data[0].content[0].text.value

        return result_text, prompt_tokens, completion_tokens

    except Exception as e:
        print(f"GPT分析錯誤: {str(e)}")
        return f"GPT分析錯誤: {str(e)}", 0, 0


def remove_url_source(text):
    """移除jina.ai分析時產生的URL(會占用太多tokens)"""
    return re.sub(r'^URL Source: .*$', '', text, flags=re.MULTILINE).strip()


def remove_markdowncontent(text):
    """移除jina.ai分析時產生的"Markdown Content:"(防止用tokens)"""
    return re.sub(r'Markdown Content:', '', text)


def fetch_url(url, results):
    """使用jinai爬取網頁內容"""
    full_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(full_url)
        response.raise_for_status()  # 直接拋出非200響應的異常
        soup = BeautifulSoup(response.text, 'html.parser')
        clean_data = remove_url_source(soup.get_text())
        clean_data = remove_markdowncontent(clean_data)
        results.append({
            "data": clean_data,
        })
    except requests.HTTPError:
        results.append({
            "status": "failed",
            "statusCode": response.status_code,
        })
    except requests.RequestException as e:
        results.append({
            "status": "error",
            "message": str(e),
        })


def get_url_response(url_list):
    """使用threading執行fetch_url"""
    results = []
    threads = []

    for url in url_list:
        thread = threading.Thread(target=fetch_url, args=(url, results))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # 讓第二個結果換行
    for i in range(1, len(results)):
        if 'data' in results[i]:
            results[i]['data'] = f"\n➖➖➖➖➖第{i+1}篇➖➖➖➖➖\n\n{results[i]['data']}"

    return results


def get_and_handle_articles(url_list):
    """ 獲取文章、處理內容"""
    content = get_url_response(url_list)

    texts_list = []
    for item in content:
        data = item.get("data", "")
        texts_list.append(data)

    return '\n'.join(texts_list)