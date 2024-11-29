from packaging import version

from ascmhl.utils import datetime_now_filename_string, datetime_now_isostring
from freezegun import freeze_time
import datetime
import os, time


def test_time():
    datetime_now_filename = datetime_now_filename_string()
    datetime_now_filename_reference = datetime.datetime.strftime(
        datetime.datetime.now(datetime.timezone.utc), "%Y-%m-%d_%H%M%SZ"
    )

    print("datetime_now_filename:           " + datetime_now_filename)
    print("datetime_now_filename_reference: " + datetime_now_filename_reference)

    # seems always to be working, as tests run in UTC ?
    assert datetime_now_filename == datetime_now_filename_reference


@freeze_time("2020-01-15 13:00:00")
def test_freeze_time():
    iso_string = datetime_now_isostring()
    assert iso_string == "2020-01-15T13:00:00+00:00"
