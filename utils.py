import time


def memoize(ttl):
    cache = {}

    def time_wrapper(func):
        def wrapper(*args):
            if args in cache and cache[args][1] >= time.time():
                return cache[args][0]
            else:
                result = func(*args)
                cache[args] = (result, time.time() + ttl)
                return result
        return wrapper
    return time_wrapper
