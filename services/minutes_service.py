import os
import openai
import time
import psutil
from logger import app_logger

def get_memory_usage():
    """現在のプロセスのメモリ使用量をMB単位で取得する"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

# プロンプトを分割して管理しやすくする
SYSTEM_PROMPT = """プロの議事録作成者として、以下の会議内容から詳細かつ構造化された議事録を**日本語で**作成してください。"""

INSTRUCTIONS = [
    "1. 各議題項目とサブトピックについて、できるだけ詳細に記述してください。議論の内容、提案、提起された懸念事項を深く説明してください。",
    "2. 専門用語や概念が言及された場合、簡単な説明や定義を追加してください。",
    "3. プロジェクトやイニシアチブの進捗状況、現在の段階、次のステップについて、より具体的な情報を提供してください。",
    "4. 重要な手順や方法論が議論された場合、各ステップを詳細に説明し、潜在的な問題点や注意事項を含めてください。",
    "5. 目標や期限については、より具体的な詳細と、それらを達成するための具体的なアクションアイテムを提供してください。",
    "6. 将来の計画や提案についてより詳細な説明を含め、それらが組織や目標にどのように貢献するかを分析してください。",
    "7. チームの協力やコミュニケーションに関する具体的な方針や推奨事項がある場合、それらを詳細に記録してください。",
    "8. 決定事項、アクションアイテム、期限が明確に定義されている場合、責任者や完了条件を含めてこれらを強調してください。",
    "9. 議論された課題や問題点を詳細に記録し、提案された解決策も含めてください。",
    "10. 次回の会議の準備事項や、会議間に完了すべきタスクを具体的に記載してください。",
    "11. 財務事項が議論された場合、具体的な数字、予算配分、財務目標を正確に記録してください。",
    "12. 法的または規制上の問題が議論された場合、その内容と潜在的な影響を慎重に文書化してください。",
    "13. 新しいアイデアやイノベーションが議論された場合、その詳細と潜在的な影響を記録してください。",
    "14. 参加者の役割や貢献が明確な場合、機密情報に注意しながら、名前を挙げて記録してください。",
    "15. 議事録の最後に、重要なポイントの非常に詳細なサマリーを追加し、重要な決定事項とアクションアイテムを箇条書きで明確にリストアップしてください。"
]

FORMATTING_INSTRUCTIONS = """
さらに、議事録をマークダウン形式で作成する際は、以下の点に注意してください：

- 適切な見出しレベル（#, ##, ### など）を使用して、文書を明確に構造化してください。
- リストには適切なマークダウン構文（- または 1. など）を使用してください。
- 重要な部分は適切に強調してください（**太字** または *斜体* を使用）。
- 必要に応じて適切な引用構文（>）を使用してください。
- 必要に応じて水平線（---）を使用してセクションを区切ってください。

議事録の冒頭には、基本的な会議情報（日付、時間、場所、参加者、議題など）を含めてください。
"""

def generate_minutes(text):
    """入力されたテキストから OpenAI API を使用してマークダウン形式の議事録を生成する関数"""
    start_time = time.time()
    start_memory = get_memory_usage()
    app_logger.info("開始: OpenAI APIを使用した議事録生成")

    try:
        # API キーを環境変数から取得
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません。")

        # OpenAI API の設定
        openai.api_key = api_key

        # プロンプトの構築
        prompt = f"{SYSTEM_PROMPT}\n\n"
        prompt += "\n".join(INSTRUCTIONS) + "\n\n"
        prompt += FORMATTING_INSTRUCTIONS + "\n\n"
        prompt += f"以下の会議内容に基づいて、上記の指示に従って包括的で詳細な議事録をマークダウン形式で作成してください。議事録は会議で使用された言語で作成してください。\n\n{text}"

        app_logger.debug("OpenAI APIにリクエストを送信")
        
        # ストリーミングレスポンスの処理
        response = openai.ChatCompletion.create(
            model="gpt-4",  # または適切なモデルを指定
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        full_response = ""
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                content = chunk['choices'][0].get('delta', {}).get('content', '')
                if content:
                    full_response += content

        end_time = time.time()
        end_memory = get_memory_usage()
        processing_time = end_time - start_time
        memory_change = end_memory - start_memory

        app_logger.info(f"完了: OpenAI APIを使用した議事録生成. 処理時間: {processing_time:.2f}秒")
        app_logger.info(f"メモリ使用量変化: {memory_change:.2f}MB")

        return full_response

    except Exception as e:
        app_logger.error(f"OpenAI APIを使用した議事録生成中にエラーが発生しました: {str(e)}", exc_info=True)
        return "議事録の生成中にエラーが発生しました。"

# スクリプトが直接実行された場合のサンプル使用例
if __name__ == "__main__":
    # サンプルの会議テキスト（実際の使用時はこれを実際の会議内容に置き換えてください）
    meeting_text = """
    ここに実際の会議の議事録やメモを入力してください。
    """
    # 議事録を生成
    minutes = generate_minutes(meeting_text)
    # 生成された議事録を表示
    print(minutes)