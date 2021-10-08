from packaging import version

from ascmhl.utils import datetime_now_filename_string
import datetime
import os, time


def test_time():
    datetime_now_filename = datetime_now_filename_string()
    datetime_now_filename_reference = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d_%H%M%S")

    print("datetime_now_filename:           " + datetime_now_filename)
    print("datetime_now_filename_reference: " + datetime_now_filename_reference)

    # seems always to be working, as tests run in UTC ?
    assert datetime_now_filename == datetime_now_filename_reference
