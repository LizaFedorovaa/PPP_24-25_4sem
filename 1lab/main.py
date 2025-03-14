import os
import json
import socket
import threading
import wave
import tempfile
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

client_logger = logging.getLogger("client")
client_logger.setLevel(logging.INFO)
client_handler = logging.FileHandler("client.log")
client_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
client_logger.addHandler(client_handler)

def save_audio_metadata(directory):
    """Сохраняет метаданные аудиофайлов в JSON."""
    audio_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".wav"):
            with wave.open(os.path.join(directory, filename), 'rb') as audio_file:
                frames = audio_file.getnframes()
                rate = audio_file.getframerate()
                duration = frames / float(rate)
                audio_files.append({
                    "filename": filename,
                    "duration": duration,
                    "format": "wav"
                })
    with open("audio_metadata.json", "w") as f:
        json.dump(audio_files, f)
    logging.info("Метаданные аудиофайлов сохранены в audio_metadata.json")

def handle_client(conn, addr):
    """Обрабатывает запросы клиента."""
    logging.info(f"Подключен клиент: {addr}")
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        if data == "list":
            logging.info(f"Клиент {addr} запросил список аудиофайлов")
            with open("audio_metadata.json", "r") as f:
                conn.send(json.dumps(json.load(f)).encode())
        else:
            filename, start, end = data.split(",")
            start = int(float(start)) * 1000  
            end = int(float(end)) * 1000
            logging.info(f"Клиент {addr} запросил отрезок аудио из файла {filename} с {start} до {end} мс")

            with wave.open(os.path.join("audio_files", filename), 'rb') as audio_file:
                frames = audio_file.getnframes()
                rate = audio_file.getframerate()
                start_frame = int(start * rate / 1000)
                end_frame = int(end * rate / 1000)

                # Перемещаем указатель на начальный кадр
                audio_file.setpos(start_frame)
                # Читаем отрезок аудио
                segment_data = audio_file.readframes(end_frame - start_frame)

                # Создаем временный файл
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_filename = temp_file.name  
                    with wave.open(temp_filename, 'wb') as segment_file:
                        segment_file.setparams(audio_file.getparams())  
                        segment_file.writeframes(segment_data)  

                    with open(temp_filename, "rb") as f:
                        conn.send(f.read())
                    logging.info(f"Отправлен отрезок аудио клиенту {addr}")

                os.remove(temp_filename)
                logging.info(f"Временный файл {temp_filename} удален")

    conn.close()
    logging.info(f"Клиент {addr} отключен")

def start_server():
    directory = "audio_files"
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Создана директория {directory}")
    save_audio_metadata(directory)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 12345))
    server.listen()
    logging.info("Сервер запущен и ожидает подключений...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def list_audio_files():
    """Запрашивает список аудиофайлов у сервера."""
    client_logger.info("Запрос списка аудиофайлов у сервера")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    client.send("list".encode())
    response = client.recv(1024).decode()
    client_logger.info("Получен список аудиофайлов от сервера")
    print(response)
    client.close()

def request_audio_segment(filename, start, end):
    """Запрашивает отрезок аудио у сервера."""
    client_logger.info(f"Запрос отрезка аудио из файла {filename} с {start} до {end} секунд")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    client.send(f"{filename},{start},{end}".encode())

    # Получаем отрезок аудио и сохраняем его
    with open(f"segment_{filename}", "wb") as f:
        while True:
            data = client.recv(1024)
            if not data:
                break
            f.write(data)
    client_logger.info(f"Отрезок аудио сохранен в segment_{filename}")
    client.close()

def start_client():
    list_audio_files()
    filename = input("Введите имя файла: ")
    start = input("Введите начальное время (в секундах): ")
    end = input("Введите конечное время (в секундах): ")
    request_audio_segment(filename, start, end)

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    start_client()
