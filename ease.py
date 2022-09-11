"""イージング
よく使うもののみ
"""
__author__ = "Choi Gyun 2022"

import math


def linear(current, start, delta, total):
    current /= total
    return delta * current + start


def in_quad(current, start, delta, total):
    current /= total
    return delta * current * current + start


def out_quad(current, start, delta, total):
    current /= total
    return -delta * current * (current - 2) + start


def inout_quad(current, start, delta, total):
    current /= total
    if current / 2 < 1:
        return delta / 2 * current * current + start
    current -= 1
    return -delta / 2 * (current * (current - 2) - 1) + start


def in_quart(current, start, delta, total):
    current /= total
    return delta * current * current * current * current + start


def out_quart(current, start, delta, total):
    current = current / total - 1
    return -delta * (current * current * current * current - 1) + start


def inout_quart(current, start, delta, total):
    current /= total / 2
    if current < 1:
        return delta / 2 * current * current * current * current + start
    current -= 2
    return -delta / 2 * (current * current * current * current - 2) + start


def in_elastic(current, start, delta, total):
    s = 1.70158
    p = 0
    a = delta

    if (current == 0):
        return start

    current /= total
    if current == 1:
        return start + delta

    if p == 0:
        p = current * 0.3

    if a < abs(delta):
        a = delta
        s = p / 4
    else:
        s = p / (2 * math.pi) * math.asin(delta / a)

    current -= 1
    return -(a * math.pow(2, 10 * current) * math.sin((current * total - s) * (2 * math.pi) / p)) + start


def out_elastic(current, start, delta, total):
    s = 1.70158
    p = 0
    a = delta

    if current == 0:
        return start

    current /= total
    if current == 1:
        return start + delta

    if p == 0:
        p = total * 0.3

    if a < abs(delta):
        a = delta
        s = p / 4
    else:
        s = p / (2 * math.pi) * math.asin(delta / a)

    return a * math.pow(2, -10 * current) * math.sin((current * total - s) * (2 * math.pi) / p) + delta + start


def inout_elastic(current, start, delta, total):
    s = 1.70158
    p = 0
    a = delta

    if current == 0:
        return start

    current /= total / 2
    if current == 2:
        return start + delta

    if p == 0:
        p = total * (0.3 * 1.5)

    if a < abs(delta):
        a = delta
        s = p / 4
    else:
        s = p / (2 * math.pi) * math.asin(delta / a)

    if current < 1:
        current -= 1
        return -0.5 * (a * math.pow(2, 10 * current) * math.sin((current * total - s) * (2 * math.pi) / p)) + start

    current -= 1
    return a * math.pow(2, -10 * current) * math.sin((current * total - s) * (2 * math.pi) / p) * 0.5 + delta + start
