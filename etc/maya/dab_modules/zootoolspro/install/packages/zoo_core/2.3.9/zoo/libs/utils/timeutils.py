from datetime import datetime, timedelta


def formatFrameToTime(start, current, frameRate):
    total = current - start
    seconds = float(total) / float(frameRate)
    minutes = int(seconds / 60.0)
    seconds -= minutes * 60

    return ":".join(["00", str(minutes).zfill(2),
                     str(round(seconds, 1)).zfill(2),
                     str(int(current)).zfill(2)])


def formatModifiedDateTime(dateTime):
    """Format a data/time into a nice human-friendly string.

    :param dateTime: The datetime instance to be formatted
    :type dateTime: :class:`datatime`

    :returns A string representing the datetime in a nice format
    :rtype: str

    .. code-block:: python

        from datetime import datetime
        now = datetime.now()
        format_modified_date_time_str(now)
        # result: 'Today, 9:23am'

    """
    date = dateTime.date()
    timeDiff = datetime.now().date() - date
    if timeDiff < timedelta(days=1):
        date_str = "Today"
    elif timeDiff < timedelta(days=2):
        date_str = "Yesterday"
    else:
        date_str = "{:d}{} {}".format(date.day,
                                      daySuffix(date.day),
                                      date.strftime("%b %Y"))

    # format the modified time into a 12-hour am/pm format
    dataTime = dateTime.time()
    hour = dataTime.hour
    suffix = "am" if hour < 12 else "pm"
    hour = hour if hour == 12 else hour % 12  # 0-11am, 12pm, 1-11pm
    date_str += (", {:d}:{:02d}{}".format(hour, dataTime.minute, suffix))
    return date_str


def daySuffix(day):
    """Figure out the suffix to use for the specified day of the month (e.g. 1st, 3rd,
    15th, 32nd, etc.)

    :param day: The day of the month
    :type day: int
    :returns: A string containing the shorthand suffix for the day of the month
    :rtype: str
    """
    return ["th", "st", "nd", "rd"][day % 10 if not 11 <= day <= 13 and day % 10 < 4 else 0]
