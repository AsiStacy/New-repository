import requests
import datetime
import json
import telebot
import unicodedata

API_TOKEN = "your_token"
API_KEY = "your_key"

bot = telebot.TeleBot(API_TOKEN)
dep_t = list()
dep_p = list()
arr_t = list()
t_subtype = list()
n = 0
i = 0


with open('api.rasp.json', encoding='utf-8') as f:
    data = json.load(f)


def make_your_time():
    your_datetime = datetime.datetime.now()
    your_datetime = str(your_datetime)
    your_time = your_datetime[11:16]
    return your_time


def make_your_date():
    your_datetime = datetime.datetime.now()
    your_datetime = str(your_datetime)
    your_date = your_datetime[:10]
    return your_date


def Country_find(your_country):
    for country in data['countries']:
        if your_country in country["title"]:
            return country


def Region_find(your_country, your_region):
    for region in Country_find(your_country)["regions"]:
        if your_region in region["title"]:
            return region


def station_code_find(your_country, your_region, your_station_name):
    for city in Region_find(your_country, your_region)["settlements"]:
        for station in city["stations"]:
            if station["title"] == your_station_name:
                return station["codes"]["yandex_code"]


def make_url(your_country, your_region, your_name_from, your_name_to):
    url = f"https://api.rasp.yandex.net/v3.0/search/?apikey={API_KEY}&from={station_code_find(your_country, your_region, your_name_from)}&to={station_code_find(your_country, your_region, your_name_to)}&date={make_your_date()}&limit=200"
    return url


def make_departure_time(ans_data):
    departure_time = list()
    for segment in ans_data["segments"]:
        dep_time = segment["departure"]
        dep_time = dep_time[11:16]
        departure_time += [dep_time]
    return departure_time


def make_arrival_time(ans_data):
    arrival_time = list()
    for segment in ans_data["segments"]:
        arr_time = segment["arrival"]
        arr_time = arr_time[11:16]
        arrival_time += [arr_time]
    return arrival_time


def make_departure_platform(ans_data):
    dep_platforms = list()
    for segment in ans_data["segments"]:
        dep_plat = segment["departure_platform"]
        dep_plat = unicodedata.normalize("NFKC", dep_plat)
        dep_platforms += [dep_plat]
    return dep_platforms


def make_transport_subtype(ans_data):
    trans_sub = list()
    for segment in ans_data["segments"]:
        tran = segment["thread"]["transport_subtype"]["title"]
        trans_sub += [tran]
    return trans_sub


def compare_date(date1, date2):
    if int(date1[:4]) > int(date2[:4]):
        return False
    else:
        if int(date1[5:7]) > int(date2[5:7]):
            return False
        else:
            if int(date1[8:]) > int(date2[8:]):
                return False
            else:
                return True


def compare_time(time1, time2):
    if int(time1[:2]) > int(time2[:2]):
        return False
    elif int(time1[3:]) > int(time2[3:]):
        return False
    else:
        return True


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, 'Привет! Для того, чтобы узнать расписание, напиши название интересующей тебя страны, '
                          'региона, станции отправления и прибытия через запятую.\n\n'
                          'Ты можешь указать время и дату, если тебе интересно расписание не на настоящий момент.\n'
                          'Пожалуйста укажи сначала время в формате hh:mm, а затем дату в формате YYYY-MM-DD.\n\n'
                          'Например: Россия, Москва, Одинцово, Славянский Бульвар, 13:00, 2022-12-30')


@bot.message_handler(commands=['more'])
def send_next(message):
    global i, n
    m = 0
    i += 5
    for j in range(i, i + 5):
        try:
            bot.send_message(message.chat.id, f'Время отправления: {dep_t[j]}\n'
                                              f'Платформа отправления: {dep_p[j]}\n'
                                              f'Тип поезда: {t_subtype[j]}\n'
                                              f'Время прибытия: {arr_t[j]}')
        except IndexError:
            m = 1
    if m == 1:
        bot.send_message(message.chat.id, 'К сожалению, на указанные день и время рейсов больше нет :( \n'
                                          'Попробуйте выбрать другую дату.')
    else:
        bot.send_message(message.from_user.id, 'Отправьте команду "/more" для просмотра следующих рейсов.')


@bot.message_handler(func=lambda message: True)
def send_message(message):
    global dep_t, dep_p, arr_t, t_subtype, n, i
    mes_list = message.text.split(', ')
    if len(mes_list) == 4:
        time = make_your_time()
        date = make_your_date()
        mes_list += [time] + [date]
    elif len(mes_list) == 5:
        date = make_your_date()
        mes_list += [date]
    elif len(mes_list) == 6:
        pass
    country = mes_list[0]
    region = mes_list[1]
    code_from = mes_list[2]
    code_to = mes_list[3]
    time = mes_list[4]
    date = mes_list[5]
    response = requests.get(make_url(country, region, code_from, code_to))
    answer_data = response.json()
    dep_t = make_departure_time(answer_data)
    dep_p = make_departure_platform(answer_data)
    arr_t = make_arrival_time(answer_data)
    t_subtype = make_transport_subtype(answer_data)
    i = 0
    k = 0
    n = 5
    while not compare_time(time, dep_t[i]):
        i += 1
        if i >= len(dep_t):
            bot.send_message(message.chat.id, 'К сожалению, на указанные день и время рейсов больше нет :( \n'
                                              'Попробуйте выбрать другую дату.')
            break
    for j in range(i, i + 5):
        try:
            bot.send_message(message.chat.id, f'Время отправления: {dep_t[j]}\n'
                                              f'Платформа отправления: {dep_p[j]}\n'
                                              f'Тип поезда: {t_subtype[j]}\n'
                                              f'Время прибытия: {arr_t[j]}')
        except IndexError:
            k = 1
    if k == 1:
        bot.send_message(message.chat.id, 'К сожалению, на указанные день и время рейсов больше нет :( \n'
                                          'Попробуйте выбрать другую дату.')
    else:
        bot.send_message(message.from_user.id, 'Отправьте команду "/more" для просмотра следующих рейсов.')


bot.infinity_polling()
