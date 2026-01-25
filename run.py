import logging
import uvicorn

def run_server():
    logging.info("Iniciando o servidor do Agente...")
    # Aqui ele aponta para o arquivo app.py dentro de src/api
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s, %(message)s",
    )
    
    run_server()