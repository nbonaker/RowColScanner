import multiprocessing as mp
import time
import numpy as np

from simulations.false_positive.false_positive import simulationUtil


def submission_fun(task_id):
    sim_util = simulationUtil()
    result = sim_util.run_job(task_id, 8, num_clicks=500, trials=20)
    return result


def main():

    pool = mp.Pool(8)
    result = pool.map(submission_fun, range(1, 9, 1))


if __name__ == "__main__":
    main()