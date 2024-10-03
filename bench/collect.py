#!/usr/bin/env python3

import argparse
import csv
import os
import socket
import sys
import time

from collections.abc import Callable


class ReusableSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def shutdown(self, how):
        pass

    def actually_shutdown(self, how):
        super().shutdown(how)

    def close(self):
        pass

    def actually_close(self):
        super().close()


def tx(s, message, buffer):
    s.sendall(message)
    received = 0
    while received < len(message):
        received += s.recv_into(buffer)

def measure(message_size: int, iterations: int, new_socket: Callable[[], socket.socket]):
    results = [0] * iterations
    message = bytes(os.urandom(message_size))
    buffer = bytearray(message_size)
    for i in range(iterations):
        start_time = time.perf_counter_ns()
        with new_socket() as s:
            tx(s, message, buffer)
            s.shutdown(socket.SHUT_RDWR)
        end_time = time.perf_counter_ns()
        elapsed_time = end_time - start_time
        results[i] = elapsed_time
    return results

def format(writer, results, rows):
    columns = list(results.keys())
    writer.writerow(columns)
    for i in range(rows):
        row = [results[c][i] for c in columns]
        writer.writerow(row)

def run(args: argparse.Namespace):
    addr = (args.host, args.port)
    reusable = ReusableSocket()
    reusable.connect(addr)

    def new_socket():
        s = socket.socket()
        s.connect(addr)
        return s

    def reusable_socket():
        return reusable

    results = {}
    results['new_connection_128_bytes'] = measure(128, args.count, new_socket)
    results['new_connection_256_bytes'] = measure(256, args.count, new_socket)
    results['new_connection_512_bytes'] = measure(512, args.count, new_socket)
    results['new_connection_1024_bytes'] = measure(1024, args.count, new_socket)
    results['new_connection_2048_bytes'] = measure(2048, args.count, new_socket)
    results['new_connection_4096_bytes'] = measure(4096, args.count, new_socket)
    results['existing_connection_128_bytes'] = measure(128, args.count, reusable_socket)
    results['existing_connection_256_bytes'] = measure(256, args.count, reusable_socket)
    results['existing_connection_512_bytes'] = measure(512, args.count, reusable_socket)
    results['existing_connection_1024_bytes'] = measure(1024, args.count, reusable_socket)
    results['existing_connection_2048_bytes'] = measure(2048, args.count, reusable_socket)
    results['existing_connection_4096_bytes'] = measure(4096, args.count, reusable_socket)

    reusable.actually_shutdown(socket.SHUT_RDWR)
    reusable.actually_close()

    with open(args.output, 'w+') as f:
        writer = csv.writer(f)
        format(writer, results, args.count)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=(
            'Connect to the given address and port and sends variety '
            'of TCP requests measuring latency of each of the requests.'
        ),
    )
    parser.add_argument('-o', '--output', required=True, help=(
        'path to the file where the results will be stored, file will '
        'be created if it does not exist.'))
    parser.add_argument('-t', '--host', required=False, default='127.0.0.1',
        help=(
            'name or ip address of the host to connect to, if not provided, '
            'localhost will be used.'))
    parser.add_argument('-p', '--port', type=int, default=5678, required=False,
        help='port to connect to on the host, by default port 5678 is used.')
    parser.add_argument('-c', '--count', type=int, default=1000, required=False,
        help=(
            'the number of times each measurment will be repeated, default '
            'value is 1000.'))

    args = parser.parse_args()
    run(args)

