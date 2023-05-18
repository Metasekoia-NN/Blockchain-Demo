from datetime import datetime, timedelta


def get_current_time():
    return datetime.now()


def get_current_date():
    return datetime.now().date()


def next_day(d):
    return d + timedelta(days=1)


def next_year(d):
    return d + timedelta(days=365)


def time2strtime(t) -> str:
    return t.strftime('%Y-%m-%d %H:%M:%S')


def date2strdate(d) -> str:
    return d.strftime('%Y-%m-%d')


def strtime2time(str_time):
    return datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S')


def strtime2date(str_time):
    return datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S').date()


def strdate2date(str_date):
    return datetime.strptime(str_date, '%Y-%m-%d').date()


def strdate2time(str_date):
    return datetime.strptime(str_date, '%Y-%m-%d')
