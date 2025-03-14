import socket
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)

def list_audio_files():
    logging.info("Запрос списка аудиофайлов у сервера")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    client.send("list".encode())
    response = client.recv(1024).decode()
    logging.info("Получен список аудиофайлов от сервера")
    print(response)
    client.close()

def request_audio_segment(filename, start, end):
    logging.info(f"Запрос отрезка аудио из файла {filename} с {start} до {end} секунд")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    client.send(f"{filename},{start},{end}".encode())

    with open(f"segment_{filename}", "wb") as f:
        while True:
            data = client.recv(1024)
            if not data:
                break
            f.write(data)
    logging.info(f"Отрезок аудио сохранен в segment_{filename}")
    client.close()

if __name__ == "__main__":
    list_audio_files()
    filename = input("Введите имя файла: ")
    start = input("Введите начальное время (в секундах): ")
    end = input("Введите конечное время (в секундах): ")
    request_audio_segment(filename, start, end)