# AIScriber: 音声文字起こし・議事録生成アプリケーション

AIScriber は、音声ファイルをアップロードし、文字起こしを行い、さらに AI を使用して詳細な議事録を自動生成する Flask ベースの Web アプリケーションです。

## 主な機能

- ドラッグ&ドロップによる音声ファイル（MP3, WAV, MP4）のアップロードと処理
- 音声の文字起こし（Google Speech Recognition API使用）
- 文字起こしテキストからの AI による詳細な議事録自動生成（Anthropic API使用）
- リアルタイムの進捗表示（アップロードと文字起こし）
- 議事録の再生成機能
- 議事録のダウンロード（テキストまたは Markdown 形式）
- 文字起こし結果の表示
- 自動生成される目次機能

## 技術スタック

- バックエンド:
  - Python 3.x
  - Flask
  - Flask-SocketIO
  - SpeechRecognition
  - pydub
  - Anthropic API (Claude-3-Sonnet モデル使用)
- フロントエンド:
  - HTML5
  - CSS (Bootstrap)
  - JavaScript

## プロジェクト構造

```
VOICE_TEXT_GO/
├── __pycache__/
├── services/
│   ├── __pycache__/
│   ├── audio_service.py
│   ├── file_service.py
│   ├── minutes_service.py
│   ├── transcription_service.py
│   └── upload_service.py
├── templates/
│   ├── index.html
│   └── LLMtest.html
├── uploads/
├── .env
├── app.py
├── config.py
├── README.md
├── requirements.txt
└── routes.py
```

## 主要なファイルの説明

### バックエンド

- `app.py`: アプリケーションのエントリーポイント。Flask アプリケーションの初期化と設定を行います。
- `config.py`: アプリケーションの設定ファイル。環境変数や定数を管理します。
- `routes.py`: アプリケーションのルート定義。各エンドポイントの処理を記述します。
- `services/`: 各種サービスの実装を含むディレクトリ
  - `audio_service.py`: 音声ファイルの変換と分割
  - `file_service.py`: ファイル名生成とダウンロード準備
  - `minutes_service.py`: Anthropic APIを使用した議事録生成
  - `transcription_service.py`: 音声認識と文字起こし
  - `upload_service.py`: ファイルアップロードの処理と全体のフロー管理

### フロントエンド

- `templates/index.html`: メインの HTML テンプレート
  - ドラッグ&ドロップによるファイルアップロード機能
  - アップロードと文字起こしの進捗バー
  - 議事録表示エリア（ダウンロードボタン付き）
  - 文字起こし結果表示エリア
  - 自動生成される目次
- `templates/LLMtest.html`: LLMテスト用のHTMLファイル（詳細は要確認）

### その他

- `.env`: 環境変数を格納する設定ファイル
- `README.md`: プロジェクトの説明文書（このファイル）
- `requirements.txt`: プロジェクトの依存パッケージリスト
- `uploads/`: アップロードされたファイルの一時保存ディレクトリ

## セットアップ

1. リポジトリをクローンします：

   ```
   git clone [リポジトリURL]
   cd VOICE_TEXT_GO
   ```

2. 仮想環境を作成し、有効化します：

   ```
   python -m venv venv
   source venv/bin/activate  # Windows の場合: venv\Scripts\activate
   ```

3. 必要なパッケージをインストールします：

   ```
   pip install -r requirements.txt
   ```

4. `.env` ファイルを作成し、必要な環境変数を設定します：

   ```
   SECRET_KEY=your_secret_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

5. アプリケーションを実行します：

   ```
   python app.py
   ```

6. ブラウザで `http://localhost:5000` にアクセスしてアプリケーションを使用します。

## サービス層の詳細

1. **音声サービス (`audio_service.py`)**
   - 音声ファイルのWAV形式への変換
   - 長い音声ファイルの分割処理

2. **ファイルサービス (`file_service.py`)**
   - 議事録の内容からファイル名の生成
   - ダウンロード用ファイルの準備と作成

3. **議事録サービス (`minutes_service.py`)**
   - Anthropic APIを使用した高度な議事録生成
   - 詳細で構造化された議事録のマークダウン形式での作成

4. **文字起こしサービス (`transcription_service.py`)**
   - Google Speech Recognition APIを使用した音声の文字起こし
   - 並行処理による効率的な文字起こし処理

5. **アップロードサービス (`upload_service.py`)**
   - ファイルアップロードの処理と検証
   - 文字起こしと議事録生成の全体フロー管理
   - Socket.IOを使用したリアルタイムの進捗状況更新

## 使用方法

1. アプリケーションにアクセスします。
2. 音声ファイル（MP3, WAV, MP4）をドラッグ&ドロップするか、クリックしてファイルを選択します。
3. "アップロード & 処理開始" ボタンをクリックします。
4. アップロードと文字起こしの進捗がリアルタイムで表示されます。
5. 処理が完了すると、AI によって生成された議事録が表示されます。
6. 議事録はテキストまたは Markdown 形式でダウンロードできます。
7. 文字起こし結果も別途表示されます。
8. 必要に応じて "議事録を再生成" ボタンをクリックして、新しい議事録を生成することができます。

## 注意事項

- このアプリケーションを使用するには、Anthropic APIキーが必要です。
- Google Speech Recognition APIの使用には制限があるため、大量の音声ファイルを処理する場合は注意が必要です。
- アップロードされたファイルは `uploads/` ディレクトリに一時的に保存されますが、処理後に自動的に削除されます。

## 開発者向け情報

- 新しい機能を追加する場合は、適切なサービスファイルに実装し、必要に応じて `upload_service.py` の `process_upload` 関数を更新してください。
- フロントエンドの変更は `templates/index.html` で行います。
- 環境変数の追加や変更が必要な場合は、`config.py` と `.env` ファイルを更新してください。

## ライセンス

[ライセンス情報を記載]

---

このREADMEは現在提供されている情報に基づいて作成されています。プロジェクトの詳細や追加の機能について、さらなる情報が必要な場合は更新します。