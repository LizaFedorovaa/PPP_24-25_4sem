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


def handle_client(conn, addr, shutdown_event):
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
        elif data == "shutdown":
            logging.info(f"Клиент {addr} запросил завершение работы сервера")
            conn.send("Сервер завершает работу...".encode())
            conn.close()
            shutdown_event.set()  # Устанавливаем флаг завершения
            return  # Завершаем обработку клиента
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
                        while True:
                            chunk = f.read(1024)
                            if not chunk:
                                break
                            conn.send(chunk)

                    # Отправляем маркер завершения передачи
                    conn.send(b"END")
                    logging.info(f"Отправлен отрезок аудио клиенту {addr}")

                os.remove(temp_filename)
                logging.info(f"Временный файл {temp_filename} удален")

    conn.close()
    logging.info(f"Клиент {addr} отключен")

def start_server(shutdown_event):
    """Запускает сервер."""
    directory = "audio_files"
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Создана директория {directory}")
    save_audio_metadata(directory)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 12345))
    server.listen()
    logging.info("Сервер запущен и ожидает подключений...")

    while not shutdown_event.is_set():
        try:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, shutdown_event))
            client_thread.start()
        except socket.error:
            break

    server.close()
    logging.info("Сервер завершил работу.")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)

def list_audio_files():
    """Запрашивает список аудиофайлов у сервера."""
    logging.info("Запрос списка аудиофайлов у сервера")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    client.send("list".encode())
    response = client.recv(1024).decode()
    logging.info("Получен список аудиофайлов от сервера")
    print("Список аудиофайлов:")
    print(response)
    client.close()


def request_audio_segment():
    """Запрашивает отрезок аудио у сервера."""
    filename = input("Введите имя файла: ")
    start = input("Введите начальное время (в секундах): ")
    end = input("Введите конечное время (в секундах): ")
    logging.info(f"Запрос отрезка аудио из файла {filename} с {start} до {end} секунд")

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 12345))
        client.send(f"{filename},{start},{end}".encode())

        with open(f"segment_{filename}", "wb") as f:
            while True:
                data = client.recv(1024)
                if not data or data == b"END":  # Проверяем маркер завершения
                    break
                f.write(data)

        logging.info(f"Отрезок аудио сохранен в segment_{filename}")
        print("Отрезок аудио успешно сохранён.")
    except Exception as e:
        logging.error(f"Ошибка при запросе отрезка аудио: {e}")
        print(f"Произошла ошибка: {e}")
    finally:
        client.close()

    print("\nВозвращаемся в меню...")

def shutdown_server():
    """Отправляет команду на завершение работы сервера."""
    logging.info("Отправка команды на завершение работы сервера")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    client.send("shutdown".encode())
    response = client.recv(1024).decode()
    logging.info(response)
    client.close()

def start_client():
    """Запускает клиентскую часть."""
    while True:
        print("\nМеню:")
        print("1. Получить список аудиофайлов")
        print("2. Запросить отрезок аудио")
        print("3. Завершить работу сервера")
        print("4. Выйти")
        choice = input("Выберите действие (1-4): ")

        if choice == "1":
            list_audio_files()
        elif choice == "2":
            request_audio_segment()
        elif choice == "3":
            shutdown_server()
        elif choice == "4":
            logging.info("Клиент завершает работу.")
            print("Клиент завершает работу.")
            break
        else:
            print("Неверный выбор. Пожалуйста, выберите действие от 1 до 4.")

if __name__ == "__main__":
    import threading

    shutdown_event = threading.Event()

    server_thread = threading.Thread(target=start_server, args=(shutdown_event,))
    server_thread.start()

    start_client()

    server_thread.join()