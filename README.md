# Learning to Schedule Heuristics in Branch-and-Bound

To reproduce our results, do the following:  

* The source code of our version of SCIP can be found in the directory **scip**. To find out how to install and compile SCIP, please visit https://www.scipopt.org.

* To collect data for diving and LNS heuristic, run SCIP with the setting **datacollection.set** and save the output in an out-file (see https://www.scipopt.org for more information on how to do that).

* To obtain a schedule, execute
	
  `python obtainSchedule.py <path/to/SCIPoutfile.out> <whichheuristics>`

	where `<whichheuristics>` can take values *diving*, *LNS* and *diving+LNS* depending on which heuristics should be added to the schedule.

* The schedule setting will be saved as **schedule.set**.

A collection of GISP instances can be found in the directory **instances**.
	
	
