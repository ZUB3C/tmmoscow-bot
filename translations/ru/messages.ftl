# Messages

-bot-name = <b>TmMoscow Notify Bot</b>


messages-start =
    👋 { $name }, добро пожаловать в { -bot-name }

messages-commands_set =
    🌎 <b>Команды заданы для { $count ->
        [one] одной локали
        *[other] { $count } локалей
    }:</b> { $locales }

messages-choose_competition = 🏆 Выберите соревнование (дистанции { $distance_type_title }):

messages-competition_info =
    <a href="{ $url }">{ $title }</a>:
    <b>Дата:</b> { $date }
    <b>Место:</b> { $location }
    <b>Просмотры:</b> { $views }

messages-choose_distance_type = Выберите тип дистанции для поиска недавних соревнований:

messages-choosed_distance_type = Выбран новый тип дистанции: <b> { $new_distance_type_title } </b>

# Commands

commands-start = Запустить бота

# Buttons

buttons-go_back = ⬅ Вернуться назад

buttons-close_menu = 🗑 Закрыть
