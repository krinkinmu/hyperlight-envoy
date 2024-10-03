#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import sys

from itertools import product


_MESSAGE_SIZE = 'message_size'
_SETUP = 'setup'
_EXPERIMENT = 'experiment'
_CONFIG = 'config'
_LATENCY = 'latency'

def setups():
    return ['existing_connection']

def message_sizes():
    return [128, 256, 512, 1024, 2048, 4096]

def column(setup: str, message_size: int):
    return '_'.join([setup, str(message_size), 'bytes'])

def relevant_columns():
    return [
        column(setup, size)
        for setup, size in product(setups(), message_sizes())
    ]

def parse_csv(path):
    df = pd.read_csv(path, dtype=np.int32)[relevant_columns()]
    df = df.melt(var_name=_CONFIG, value_name=_LATENCY)
    for setup in setups():
        for message_size in message_sizes():
            config = column(setup, message_size)
            df.loc[df[_CONFIG]==config, _SETUP] = setup
            df.loc[df[_CONFIG]==config, _MESSAGE_SIZE] = message_size
    df[_MESSAGE_SIZE] = df[_MESSAGE_SIZE].astype(np.int32)
    return df

def main(args: argparse.Namespace):
    # This just parses command line arguments to extract the names of
    # the experiments and file path to the raw results of the experiment
    file_path = {}
    for exp in args.experiments:
        name, path = [word.strip() for word in exp.split('=', maxsplit=1)]
        file_path[name] = path

    # This actually reads the data and generates a single relation from
    # individual data files for each experiment
    dfs = []
    for name, path in file_path.items():
        df = parse_csv(path)
        df[_EXPERIMENT] = name
        dfs.append(df)
    df = pd.concat(dfs, axis=0)

    # And now we actually summarize the results calculating mean, 25th and
    # 75th %-iles for latency measuremnts
    df = df.groupby(
        by=[_EXPERIMENT, _SETUP, _MESSAGE_SIZE, _CONFIG],
        as_index=False,
    ).agg(
        Mean=(_LATENCY, np.mean),
        Std=(_LATENCY, np.std),
    )

    # We show the result as text, given that once it was summraized it
    # shouldn't have a lot of data
    print(df)

    # The picture worth 1000-words through, so we also generate a simple
    # plot visualizing the data and save it as a picture
    df = df.pivot(
        index=_MESSAGE_SIZE,
        columns=[_SETUP, _EXPERIMENT],
        values=['Mean', 'Std'],
    )
    for setup in setups():
        ax = df[('Mean', setup)].plot.bar(rot=0, yerr=df[('Std', setup)])
        ax.set_title('Latency in ns')
        ax.legend(bbox_to_anchor=(1.0, 1.0))
        ax.figure.savefig(setup + '.png', bbox_inches='tight')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='Summarize Envoy latency results.',
    )
    parser.add_argument(
        'experiments', metavar='E', type=str, nargs='+',
        help="Name of the experiment and path to the file with the results.",
    )
    args = parser.parse_args()
    main(args)
