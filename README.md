## Instructions:

1. Setup env with `poetry` or with `requirements.txt`

2. Run the REST API server

```bash
uvicorn main:app --reload
```

3. Run chainlit app

```bash
chainlit run chainlit_app.py --port 3003
```

4. Visit the chainlit app at [`http://localhost:3003`](http://localhost:3003)
