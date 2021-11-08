from picamera import PiCamera
import RPi.GPIO as GPIO
import datetime
import requests
import yagmail
import time
import os

# функция, проверяющая наличие/создающая папку shots
def create_shots_folder():
    # если папка существует
    if os.path.exists(os.path.join(os.getcwd(), 'shots')):
        # то ничего не делать
        pass
    # если папки нет
    else:
        # то создать папку shots в текущем каталоге
        os.mkdir('shots')

# функция, управляющая камерой
def take_shots(number_of_shots):
    # инициализация камеры
    camera = PiCamera()
    # задаем разрешение снимка
    camera.resolution = (1024, 768)
    # список, в который добавим пути к снимкам
    shots = []
    # цикл, который number_of_shots-раз сделает снимки с паузой 0.5 сек
    for i in range(number_of_shots):
        # получим текущую дату и время без микросекунд
        time_of_the_crime = datetime.datetime.today().replace(microsecond=0)
        # присвоим снимку имя: текущая дата и время плюс расширение .jpg
        shot_name = str(time_of_the_crime) + '.jpg'
        # получим путь к снимку
        shot_path = os.path.join(os.getcwd(), 'shots', shot_name)
        # сделаем снимок и сохраним его в папку shots под именем shot_name
        camera.capture(shot_path)
        print('Сделал снимок:', shot_name)
        # добавим путь снимка в список снимков shots
        shots.append(shot_path)
        # пауза между снимками в секундах
        pause = 0.5
        time.sleep(pause)

    # отключим камеру
    camera.close()

    return shots

def send_email(sender_email, sender_email_password, recipient_email, number_of_shots):
    # список с путями снимков
    shots = take_shots(number_of_shots)
    # senders_email - Gmail-адрес отправителя
    # senders_email_password - пароль от Gmail
    email = yagmail.SMTP(user=sender_email, password=sender_email_password)
    # subject - тема письма
    # contents - содержимое письма
    # attachments - вложения (снимки)
    email.send(to=recipient_email, subject='Проникновение в помещение', contents='Тревога!', attachments=shots)
    print('Снимки отправлены на почту.\n')


def send_ifttt_notification():
    # ссылка на апплет IFTTT
    link = 'https://maker.ifttt.com/trigger/НАЗВАНИЕ_ПРИЛОЖЕНИЯ/with/key/КЛЮЧ'
    # отправляем post-запрос в IFTTT, чтобы сработал апплет
    requests.post(link)
    print('Уведомление отправлено в приложение IFTTT.')


def setup_GPIO():
    # отключим уведомления об ошибках
    GPIO.setwarnings(False)
    # используем нумерацию выводов BCM
    GPIO.setmode(GPIO.BCM)
    # пин Trig
    TRIGGER = 19
    # пин Echo
    ECHO = 26
    # установим режим работы пина TRIGGER на Выход
    GPIO.setup(TRIGGER, GPIO.OUT)
    # установим режим работы пина ECHO на Вход со стягивающим резистором
    GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    return TRIGGER, ECHO

# пауза после объявления пинов
# без паузы датчик работает некорректно
def pause(value):
    for i in range(value):
        print('Запуск через', value - i, 'сек.')
        time.sleep(1)
    print('Сигнализация включена.\n')


def ultrasonic_detection(TRIGGER, ECHO):
    # подадим импульс, т . е. установим состояние пина на HIGH
    GPIO.output(TRIGGER, GPIO.HIGH)
    # длительность импульса 0.00001 сек
    time.sleep(0.00001)
    # установим состояние пина TRIGGER на LOW
    GPIO.output(TRIGGER, GPIO.LOW)
    # считываем состояние пина ECHO
    # пока ничего не происходит, фиксируем текущее время start
    while GPIO.input(ECHO) == 0:
        start = time.time()
    # если обнаружено движение, зафиксируем время end
    while GPIO.input(ECHO) == 1:
        end = time.time()
    # рассчитаем длительность сигнала
    signal_duration = end - start
    # рассчитаем расстояние до объекта
    distance = round(signal_duration * 17150, 2)
    
    # если объект обнаружен на расстоянии от 3 до 15 см
    if 3 < distance < 15:
        print("Замечено движение на расстоянии", distance, "см. от датчика.")
        # отправим уведомление в приложение IFTTT
        send_ifttt_notification()
        # отправим снимки на почту
        send_email(sender_email='gmail', sender_email_password='gmail_password',
                 recipient_email='email', number_of_shots=3)


def main():
    create_shots_folder()
    TRIGGER, ECHO = setup_GPIO()
    pause(10)
    while True:
        try:
            ultrasonic_detection(TRIGGER, ECHO)
        except KeyboardInterrupt:
            GPIO.cleanup()


if __name__ == "__main__":
    main()
