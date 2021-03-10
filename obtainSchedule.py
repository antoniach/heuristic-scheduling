import sys

def getData(outfiles, heuristics):
	n = len(outfiles)
	files = []
	for i in range(n):
		file = open(outfiles[i],'r')
		files.append(file.readlines())

	instances = []
	optsols = []

	data = [[h,[]] for h in heuristics]
	usednodes = [set() for heur in heuristics]
	
	for i in range(n):

		newinstance = False
		newheurdata = False
		ninstances = 0
		for j in range(len(files[i])):
			line = files[i][j]
			line = line.strip()

			# new instance found
			if( line.startswith('@01') ):
				name = line.split('/')[-1].split()[0].strip()
				instances += [name]
				newinstance = True
				ninstances += 1

			# store optimal solution of instance
			if line.startswith('Primal Bound       :') and newinstance:
				solution = float(line.split(':')[1].split()[0])
				optsols += [solution]

			# start of heuristic call information
			elif line.startswith('Diving Heuristic  :   NodeID    Found    Best      Depth    ExecTime') and newinstance:
				newheurdata = True
				newinstance = False

			# track heuristic call information
			elif newheurdata:

				# end of tracking
				if len(line) == 0:
					newheurdata = False    
					continue

				# store whether solution was found
				nsols = int(line.split('|')[2].strip())
				solved = True if nsols > 0 else False
				#nsols = int(line.split('|')[2].strip())
				#nincb = int(line.split('|')[3].strip())

				# if solution was found, store it
				if nsols != 0:
					bestsol = float(line.split('|')[4].strip())
				else:
					bestsol = '-'

				# store name of heuristic
				heurname = line.split('|')[0].strip()

				# store diving depth for diving heuristics and nodes in subscip for LNS heuristics
				if heurname in {'rens', 'crossover', 'rins', 'localbranching', 'mutation', 'trustregion', 'dins'}:
					niter = max(int(line.split('|')[9].strip()),1)
				else:
					niter = int(line.split('|')[5].strip())

				# store "name of node" -> nodenumber + number of instance + seed
				instancename = line.split('|')[1].strip() + '-' + str(ninstances) + '-' + str(i)
				
				# store amount of time for which heuristic was ran
				time = float(line.split('|')[6].strip())
				if time == 0.0:
					time = 0.0000001
				
				nodedepth = int(line.split('|')[7].strip())

				nodeidx = line.split('|')[1].strip()

				#if heuristic exists, add to data
				try:
					idx = heuristics.index(heurname)
				except ValueError:
					continue

				# store information in data array if node was never seen before for this heuristic.
				# Otherwise, replace existing entry if node got solved
				if instancename in usednodes[idx]:
					if solved == True:
						copy = [(x,i) for i,x in enumerate(data[idx][1]) if x[0] == instancename]
						data[idx][1][copy[0][1]] = [instancename, solved, niter, time, nodedepth, bestsol] 
				data[idx][1] += [[instancename, solved, niter, time, nodedepth, bestsol]]


	# return data points and dictonary of optimal solutions to instances
	return(data)

# only consider nodes which were solved by at least one heuristic
def filterData(data):

	# get all nodes that were solved by at least one heuristic
	solved = set()
	for i in range(len(data)):
		heursolved = {x[0] for x in data[i][1] if x[1] == True}
		solved = solved.union(heursolved)

	# filter out instances that were not solved by any heuristic
	for i in range(len(data)):
		
		data[i][1] = [x for x in data[i][1] if x[0] in solved]

		included = {x[0] for x in data[i][1]}
		notincluded = solved - included

		data[i][1] += [[node, False, 0, '-', '-', '-'] for node in notincluded]

	return data


def computeBestIterLimitTuple(heuristic, itercosts, heurdata, miniter, maxiter, translation, unsolved):

	scores = []
	for j in range(miniter, maxiter):
				
		solved = [x for x in heurdata if x[1] == True and x[2] <= j]
		solvednodes = {x[0] for x in solved}

		prob = len(solved)/len(heurdata)
		scores += [(prob/((j-translation)*itercosts), j, solvednodes)]

	if len(scores) == 0:
		return (heuristic, 0, 0, set())

	best = max(scores,key=lambda item:item[0])

	if len(unsolved.intersection(best[2])) > 0:
		prob = len(best[2])/len(heurdata)
	else:
		prob = 0.0

	return (heuristic, prob/((best[1]-translation)*itercosts), best[1], best[2])

# get average time/node for every heuristic
def getCostPerNode(data):
	heuristics = []
	avecosts = []
	for i in range(len(data)):

		heuristics += [data[i][0]]
		cost = 0.0
		ninstances = 0

		for heurcall in data[i][1]:

			if heurcall[3] != '-':
				ninstances += 1
				cost += heurcall[3] / heurcall[2]

		if ninstances == 0:
			cost = 0.1
		else:
			cost /= ninstances 
		avecosts += [cost]

	return dict(zip(heuristics, avecosts))


# get optimal schedule using diving depth or nodes in subscip as a measure
def computeSchedule(data):
	
	unsolved = {x[0] for x in data[0][1]}
	best = ('',1,1)
	heuristics = [x[0] for x in data]

	schedule = []
	usedheur = set()
	diving = True

	# get average time/node for every heuristic
	costs = getCostPerNode(data)
	
	while len(unsolved) > 0 and best[1] != 0:
		
		heurscores = []
		# go though all heuristics
		for i in range(len(heuristics)):

			# if the heuristic is already in the schedule, skip it 
			if data[i][0] in usedheur:
				continue

			heurdata = [x for x in data[i][1] if x[0] in unsolved]

			if len(heurdata) == 0:
				continue

			# get minimal and maximal number of iterations
			miniter = max(min(data[i][1],key=lambda item:item[2])[2],1)
			maxiter = max(data[i][1],key=lambda item:item[2])[2] + 1

			# find iteration limit w.r.t. score and add corresponding tuple to heurscores
			heurscores += [computeBestIterLimitTuple(data[i][0], costs[data[i][0]], heurdata, miniter, maxiter, 0, unsolved)]

		# running the heuristic that was added last to the scheudle is also an option		
		if len(schedule) > 0:

			# get last heuristic added to the schedule
			heuridx = heuristics.index(schedule[-1][0])

			# get data for that heuristic
			heurdata = [x for x in data[heuridx][1] if x[0] in unsolved]

			if len(heurdata) != 0:

				# get iteration limit with which the heuristic was added to the schedule
				iterlimit = schedule[-1][1]

				# get shifted iteration limits
				miniter = iterlimit + 1
				maxiter = max(data[heuridx][1],key=lambda item:item[2])[2] + 1

				# find iteration limit w.r.t. score and add corresponding tuple to heurscores
				heurscores += [computeBestIterLimitTuple(data[heuridx][0], costs[data[heuridx][0]], heurdata, miniter, maxiter, iterlimit, unsolved)]

		if len(heurscores) == 0:
			break

		# get tuple with best score
		best = max(heurscores,key=lambda item:item[1])	
		
		# use every heuristic only once
		usedheur = usedheur.union({best[0]})

		# if we decided to run last heuristic for longer, update iteration limit of last entry of schedule
		if len(schedule) > 0 and schedule[-1][0] == best[0]:
			schedule[-1][1] = best[2]
		# if heuristic is new, add [heuristic, limit] to schedule
		else:
			schedule += [[best[0], best[2]]]
		
		# remove nodes that are solved now
		unsolved = unsolved - best[3]

	return schedule

def createSettingsfile(heuristics, schedule):

	notincluded = heuristics
	
	settings = ''
	for i in range(len(schedule)):
		entry = schedule[i]

		# correct name of 'distributiondiving' (in the logs, it's written without the 'g')
		if entry[0] == 'distributiondivin':
			entry[0] = 'distributiondiving'
			
		# depending on the type of heuristic, 'iterations' mean something different
		# (diving -> maximal diving depth, LNS -> max number of nodes in sub-MIP)
		if entry[0][-4] == 'ving':
			itertype = '/maxdivedepth'
		else:
			itertype = '/maxnodes'

		# create right settings for heuristics in schedule
		settings += 'heuristics/' + entry[0] + '/freq = 1 \n'
		settings += 'heuristics/' + entry[0] + '/freqofs = 0 \n'
		settings += 'heuristics/' + entry[0] + '/priority = ' + str( -10 * (i + 1)) + '\n'
		settings += 'heuristics/' + entry[0] + itertype + ' = ' + str(entry[1]) + '\n \n'

		if entry[0] == 'distributiondiving':
			entry[0] = 'distributiondivin'

		# remove the heuristics that are in the schedule from the 'not included' list
		notincluded.remove(entry[0])

	# do not execute heuristics that are not in the schedule
	for heur in notincluded:
		settings += 'heuristics/' + heur + '/freq = -1 \n'

	# get a complete schedule settings file
	settingsfile = open('schedule.set', "a+")
	settingsfile.write(settings)
	settingsfile.close()


# compute greedy schedule using the data
def getScheduleSetting(outfiles, whichheuristics):

	if whichheuristics == 'diving':
		heuristics = ['actconsdiving','coefdiving','conflictdiving','distributiondivin','farkasdiving',
		'fracdiving','guideddiving','linesearchdiving','pscostdiving','veclendiving']
	elif whichheuristics == 'LNS':
		heuristics = ['rens', 'crossover', 'rins', 'localbranching', 'mutation', 'trustregion', 'dins']
	else:
		heuristics = ['actconsdiving','coefdiving','conflictdiving','distributiondivin','farkasdiving',
		'fracdiving','guideddiving','linesearchdiving','pscostdiving','veclendiving','rens', 'crossover',
		'rins', 'localbranching', 'mutation', 'trustregion', 'dins']	

	# get data from log-files
	data = getData(outfiles, heuristics)

	# filter out nodes for which not all heuristics ran and for which no heuristic found a solution
	data = filterData(data)

	# compute greedy schedule
	schedule = computeSchedule(data)

	# create settingsfile out of schedule
	createSettingsfile(heuristics, schedule)

if __name__ == "__main__":
	print(sys.argv)
	outfile = sys.argv[1]
	whichheuristics = sys.argv[2]

	getScheduleSetting([outfile],whichheuristics)
	
	




