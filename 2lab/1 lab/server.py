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

def save_audio_metadata(directory):
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

                audio_file.setpos(start_frame)
                segment_data = audio_file.readframes(end_frame - start_frame)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_filename = temp_file.name
                    with wave.open(temp_filename, 'wb') as segment_file:
                        segment_file.setparams(audio_file.getparams())
                        segment_file.writeframes(segment_data)

                    with open(temp_filename, "rb") as f:
                        conn.send(f.read())
                        conn.flush()  # Сбрасываем буфер
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

if __name__ == "__main__":
    start_server()