#!/usr/bin/python
# -*- coding: utf8 -*-
""" Author: Ly Tuan Anh
    github nick: ongxabeou
    mail: lytuananh2003@gmail.com
    Date created: 2017/12/22
"""
import datetime
import hashlib
import sys

# để có thể chạy được cho cả python 2 và 3
# import traceback
# from functools import wraps

IS_PY2 = sys.version_info < (3, 0)

if IS_PY2:
    from Queue import Queue
else:
    from queue import Queue

from threading import Thread


def function_to_thread(thread_pool, is_cache=False):
    """ chuyển hàm được gọi trở thành Thread để chạy ngầm """

    def wrapper(f):
        return ThreadFunction(f, thread_pool, is_cache)

    return wrapper


class ThreadFunction(object):
    def __init__(self, a_function, thread_pool, is_cache):
        self.function = a_function
        self.thread_pool = thread_pool
        self.is_cache = is_cache

    def __call__(self, *args, **kwargs):
        self.thread_pool.add_task(self.function, self.is_cache, *args, **kwargs)


class ThreadPool:
    """ Pool của Thread tiêu thụ nhiệm vụ từ một hàng đợi """

    def __init__(self, num_workers, logger=None):
        self._tasks = Queue(num_workers)
        self._results = {}
        for _ in range(num_workers):
            self.Worker(self._tasks, logger, self._results)

    def add_task(self, func, is_cache, *args, **kargs):
        """ Thêm một tác vụ vào hàng đợi """
        self._tasks.put((func, args, kargs, is_cache))
        return self.Worker.get_function_id(func, args, kargs)

    def map(self, func, is_cache, args_list):
        """ Thêm một danh sách các nhiệm vụ vào hàng đợi """
        ids = []
        for args in args_list:
            ids.append(self.add_task(func, is_cache, *args))
        return ids

    def wait_all_tasks_done(self):
        """ Chờ hoàn thành tất cả các nhiệm vụ trong hàng đợi """
        self._tasks.join()
        res = self._results
        self._results = {}
        return res

    class Worker(Thread):
        """ Thread thực hiện nhiệm vụ từ một hàng đợi nhiệm vụ nhất định """

        def __init__(self, tasks, logger, results):
            Thread.__init__(self)
            self.results = results
            self.tasks = tasks
            self.logger = logger
            self.daemon = True
            self.start()

        def run(self):
            """ hàm thực hiện nhiệm vụ,
                nếu nhiệm vụ đã từng thực hiện rồi thi không thực hiện nữa
                nếu chưa thì thực hiện nhiệm vụ và ghi kết quả vào result
                quá trình thực hiện nếu lỗi được ghi log nếu logger != None
            """
            while True:
                func, args, kargs, is_cache = self.tasks.get()
                try:
                    id = self.get_function_id(func, args, kargs)
                    if id in self.results and is_cache:
                        return self.results[id]
                    else:
                        result = func(*args, **kargs)
                        if is_cache:
                            self.results[id] = result
                except SystemExit:
                    pass
                except:
                    # Một trường hợp ngoại lệ đã xảy ra trong thread này
                    if self.logger is None:
                        raise
                    else:
                        line = '=================================================================='
                        if args is ():
                            self.logger.exception('Exception in thread %s\n%s :: %s' %
                                                  (line, str(datetime.datetime.now()), func.__name__))
                        else:
                            self.logger.exception('Exception in thread %s\n%s :: %s with param %r' %
                                                  (line, str(datetime.datetime.now()), func.__name__, args))
                finally:
                    # Đánh dấu công việc này là xong, dù có ngoại lệ xảy ra hay không
                    self.tasks.task_done()

        @staticmethod
        def get_function_id(func, args, kargs=None):
            identify = "{function} {agrs} ".format(
                function=func.__name__,
                agrs="args %r kargs %r" % (args, kargs))
            return hashlib.md5(identify.encode('utf-8')).hexdigest()


# ------------------Test------------------------
if __name__ == "__main__":
    from random import randrange
    from time import sleep

    # Khởi chạy một ThreadPool với 8 công nhân(Worker)
    # giao cho 8 công nhân đó 16 nhiệm vụ, các công nhân
    # nhận nhiệm vụ theo cơ chế hàng đợi(FIFO). chương trình
    # sẽ đợi cho đến khi tất cả các nhiệm vụ được hoàn thành.
    pool = ThreadPool(num_workers=8)


    # Chức năng được thực hiện trong một chủ đề
    def wait_delay(id_w, time):
        print("(%d)id sleeping for (%d)sec" % (id_w, time))
        sleep(1)
        return time * 100


    @function_to_thread(pool)
    def wait_delay2(time):
        print("wait_delay2 sleeping for (%d)sec" % time)
        sleep(1)


    @function_to_thread(pool)
    def func_error2(time):
        print("func_error2 sleeping for (%d)sec" % time)
        sleep(1)
        raise Exception("error2 in thread")


    def func_error():
        raise Exception("error in thread")


    # gọi hàm đã chuyển thành thread trương chình không
    # chờ xử lý xong mà vẫn sẽ đi tiếp
    wait_delay2(10)
    # gọi hàm có lỗi
    func_error2(10)

    # Tạo sự chậm trễ ngẫu nhiên cho 15 nhiệm vụ.
    # một nhiệm vụ bao gồm mã và thời gian hoàn thành.
    delays = [(i + 1, randrange(3, 7)) for i in range(15)]

    # Thêm các công việc với số lượng lớn vào thread.
    # Hoặc bạn có thể sử dụng `pool.add_task` để thêm
    # các công việc đơn lẻ.
    func_ids = pool.map(wait_delay, True, delays)
    # thêm một nhiệm vụ đơn lẻ
    func_id = pool.add_task(wait_delay, True, 16, 8)

    pool.add_task(func_error, True)
    # đợi cho đến khi tất cả nhiệm vụ được hoàn thành
    results = pool.wait_all_tasks_done()
    # kiểm tra kết quả
    for id in func_ids:
        print('function %s result %r' % (id, results[id]))
    print('function %s result %r' % (func_id, results[func_id]))

    sleep(1)
