import os,sys,inspect
import numpy as np
from scipy import stats
# from matplotlib import pyplot as plt


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
parentdir = os.path.dirname(parentdir)
os.chdir(parentdir)
sys.path.append(parentdir)

from simulated_user import SimulatedUser
from pickle_util import PickleUtil

try:
    my_task_id = int(sys.argv[1])
    num_tasks = int(sys.argv[2])
except IndexError:
    my_task_id = 1
    num_tasks = 12



deltas = [i/10 for i in range(10)]+[i/2+1 for i in range(7)]
print(deltas)
click_dists = [(stats.norm(delta, 0.05), delta) for delta in deltas]

# plt.plot(np.arange(-2,2,0.01), click_dists[7][0].pdf(np.arange(-2,2,0.01)))
# plt.show()

parameters_list = []
parameters_dict = dict()

for dist in click_dists:
    parameters_dict["order"] = "default"
    parameters_dict["words_first"] = True
    parameters_dict["num_words"] = 0
    parameters_dict["click_dist"] = dist[0]
    parameters_dict["attribute"] = dist[1]
    parameters_list += [parameters_dict.copy()]

print(len(parameters_list))
num_jobs = len(parameters_list)
job_indicies = np.array_split(np.arange(1, num_jobs+1), num_tasks)[my_task_id-1]
print(job_indicies)

for job_index in job_indicies:
    parameters = parameters_list[job_index-1]
    user_num = int((job_index*0.999)/num_jobs)
    print(user_num)
    sim = SimulatedUser(parentdir, job_num=user_num)
    sim.parameter_metrics(parameters, num_clicks=500, trials=20, attribute=parameters["attribute"])
