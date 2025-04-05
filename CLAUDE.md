# OpenLockey Development Guidelines

## Commands
- Run app: `uvicorn app.main:app --reload`
- Run tests: `pytest`
- Run single test: `pytest tests/test_file.py::test_function -v`
- Lint: `flake8 app tests`
- Type check: `mypy app tests`
- Format code: `black app tests && isort app tests`

## Code Style
- Use Black with default settings for formatting
- Organize imports with isort
- Type hints required for all function parameters and return values
- Japanese comments are acceptable (コメントは日本語でもOK)
- Class names: PascalCase
- Function/variable names: snake_case
- Constants: UPPERCASE_WITH_UNDERSCORES
- Error handling: Use try/except blocks with specific exceptions

## Architecture
- FastAPI for API routes in app/api/
- SQLAlchemy for database models in app/models/
- Pydantic schemas in app/schemas/
- Core config in app/core/
- Templates use Jinja2 in app/templates/

# OpenLockey 開発ガイドライン

## コマンド
- アプリの実行: `uvicorn app.main:app --reload`
- テスト実行: `pytest`
- 特定のテスト実行: `pytest tests/test_file.py::test_function -v`
- リント: `flake8 app tests`
- 型チェック: `mypy app tests`
- コードフォーマット: `black app tests && isort app tests`

## コードスタイル
- フォーマットには Black のデフォルト設定を使用
- インポートは isort で整理
- すべての関数パラメータと戻り値に型ヒントが必須
- 日本語のコメントは許可（コメントは日本語でもOK）
- クラス名: PascalCase
- 関数/変数名: snake_case
- 定数: UPPERCASE_WITH_UNDERSCORES
- エラー処理: 特定の例外を使用した try/except ブロックを使用

## アーキテクチャ
- API ルートには FastAPI を使用 (app/api/)
- データベースモデルには SQLAlchemy を使用 (app/models/)
- Pydantic スキーマを使用 (app/schemas/)
- コア設定は app/core/ に配置
- テンプレートには Jinja2 を使用 (app/templates/)

