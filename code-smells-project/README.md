# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado por `python app.py` no primeiro boot (o schema é criado pelo entry point; importar `app.py` não toca o banco; com WSGI use `app:create_app()` após rodar `init_db()`), já com produtos e usuários de exemplo.
