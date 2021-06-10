# from click import get_current_context
# from . import ignore
#
# """
# functions in this module should only be invoked from the main thread
# get_current_context is not thread safe
# """
#
# IGNORE_PATTERN_LIST_KEY = f'{__name__}.IGNORE_PATTERN_LIST_KEY'
#
#
# def set_ignore_patterns(value):
#     ctx = get_current_context()
#     ctx.meta[IGNORE_PATTERN_LIST_KEY] = value
#
#
# def get_ignore_patterns():
#     return get_current_context().meta.get(IGNORE_PATTERN_LIST_KEY, ignore.default_ignore_list())
