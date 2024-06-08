# Messages

-bot-name = <b>TmMoscow Notify Bot</b>


messages-start =
    👋 { $name }, добро пожаловать в { -bot-name }

messages-commands_set =
    🌎 <b>Команды заданы для { $count ->
        [one] одной локали
        *[other] { $count } локалей
    }:</b> { $locales }

# Commands

commands-start = Запустить бот
