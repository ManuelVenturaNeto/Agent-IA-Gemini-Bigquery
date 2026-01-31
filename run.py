import logging
import uvicorn

def run_server():
    logging.info("Starting Agent Server...")
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s, %(message)s",
        filename="./pipeline_logs.log",
    )
    
    run_server()