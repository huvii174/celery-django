from dateutil.rrule import rrulestr


def get_list_run_date(rrule_str, run_count, start_date, end_date):
    """
    Calculate the next run times based on the input rrule string, start date, and run count.

    :param rrule_str: The recurrence rule string (RFC 2445 format).
    :param run_count: The number of next occurrences to find.
    :param start_date: The start datetime for the recurrence rule.
    :param end_date: The end datetime for the recurrence rule.
    :return: A list of next run datetimes.
    """
    rule = rrulestr(rrule_str, dtstart=start_date)
    list_run_dates = []

    current_time = start_date
    for _ in range(run_count):
        next_run = rule.after(current_time)
        if next_run is None or next_run > end_date:
            break
        list_run_dates.append(next_run)
        current_time = next_run

    return list_run_dates


def get_next_run(list_run_dates, last_run):
    """
    Get the next run datetime based on the input rrule string, list of run datetimes, and the last run datetime.
    :param list_run_dates: A list of next run datetimes.
    :param last_run: The last run datetime.
    :return: The next run datetime.
    """
    if last_run not in list_run_dates:
        raise ValueError("last_run is not in list_run_dates")

    last_run_index = list_run_dates.index(last_run)
    if last_run_index + 1 < len(list_run_dates):
        return list_run_dates[last_run_index + 1]

    return None