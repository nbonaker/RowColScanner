import os,sys,inspect
import numpy as np
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
    my_task_id = 24
    num_tasks = 24


words_first_range = [True, False]
order_range = ["sorted", "default"]
# order_range = ["sorted"]
num_words_range = np.arange(0, 20, 1).tolist()
print(num_words_range)
parameters_list = []
parameters_dict = dict()
for wf in words_first_range:
    for kc in order_range:
        for nw in num_words_range:
            parameters_dict["order"] = kc
            parameters_dict["words_first"] = wf
            parameters_dict["num_words"] = nw
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

    sim.parameter_metrics(parameters, num_clicks=500, trials=30)
