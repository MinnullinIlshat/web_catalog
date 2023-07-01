from flask import current_app


def get_logs():
    '''возвращает последние n строк логов'''
    with open('logfile.log') as file:
        n = current_app.config.get('LINE_OF_LOGS')
        logs = file.readlines()
        return logs[-n:] if n < len(logs) else logs