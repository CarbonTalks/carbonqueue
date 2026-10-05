def main() -> None:
    import logging

    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run("cq_backend.app:app", host="127.0.0.1", port=8000)
