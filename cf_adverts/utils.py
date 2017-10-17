import os
import uuid
from easy_thumbnails.files import get_thumbnailer


def generate_random_str(length=10):
    """
    Генерация случайной строки заданной длины, по умолчанию 10.
    
    :param length: int Длина генерируемой строка
    :return: 
    """
    return os.urandom(length).hex()[:length]


def uuid_replacer_handler(instance, filename, path=''):
    """
    Замена имени файла на uuid

    :param instance: models.Model subclass
    :param filename: str Имя фалй
    :param path: str Путь для сохранения
    :return: str Результирующий путь к файлу
    """

    ext = filename.split('.')[-1]
    new_filename = os.path.join(
        path,
        str(instance.id),
        '{}.{}'.format(uuid.uuid4(), ext).lower()
    )
    return new_filename


def upload_path_handler(instance, filename):
    """
    Загрузка файла в указанную папку с заменой имени на uuid

    :param instance: object
    :param filename: str Оригинальное имя файла
    :return: str Новый путь файла
    """

    path = instance.FILE_PATH
    return uuid_replacer_handler(instance, filename, path=path)


def get_thumbnail(image_field, width, height, crop=False):
    """
    Обрезание изображения используя минимальную границу. Пример: (300x200) => 150x100
    
    :param image_field: ImageField
    :param width: int Требуемая ширина
    :param height: int Требуемая высоты
    :param crop: crop, default - False
    :return: str
    """

    if image_field.width > image_field.height:
        size = 0, height
    else:
        size = width, 0

    options = {'size': size, 'crop': crop, 'upscale': True}
    return get_thumbnailer(image_field).get_thumbnail(options).url


def format_number(number):
    """
    Форматированный вид числа. Разделение тысяч через пробел.
    
    :param number: number Число для форматирование
    
    :return: str
    """
    return '{:,}'.format(number).replace(',', ' ')
