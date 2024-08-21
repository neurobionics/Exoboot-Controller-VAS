import numpy as np
from numpy import random
from Robobidders import *
import matplotlib.pyplot as plt
import csv

# generating random walking duration
randDuration = random.choice(range(40,60,2))

###### Check if user has already done suggested subtrial and robo-model trial
flag_new_suggestion = True
while flag_new_suggestion == True:
	# generating random subtrial (WNE or EPO) & random robo-model
	subtrials = ['Walking No Exo (WNE)', 'Exo Powered On (EPO)']
	
	k = 0.4395073979128712
	b = 0.05735650555767768 # regular 'b' from Leo's trials
	robo_models = [roboModel(k,b,2)]

	numOfShuffles = random.randint(2, 10)
	for i in range(numOfShuffles): # shuffled # of times & selected at random
		np.random.shuffle(subtrials)
		np.random.shuffle(robo_models)
		
	currentRobomodel = robo_models[0]
	currentSubtrial = subtrials[0]

	# REmove subtrial stuff
	print("Random Subtrial: ", currentSubtrial)
	print("Random Robomodel (0.028 is 0.5b case): ", currentRobomodel.name())

	# Ask user if suggested trial is new
	print("Are the suggested trials new? (Answer Y/N): ")
	user_suggestion_decision = input()
	if user_suggestion_decision == 'Y':
		flag_new_suggestion = False
#######

# Print current trial
print("Current trial is: ",randDuration, "minutes,", currentSubtrial, ",", currentRobomodel.name())

## Ask user for name of csv file 
print("Filename to save as (format:Data_Subject_WNE/EPO_2r0.5b/3r1b).csv => ") 
filename = input()

headers = ['Time(mins)','Subject Bid Amount', 'Won?', 
		   'Winning Payout Amnt', 'Total Subject Winnings']

# Initializations
bid_matrix = [] # store bids for each round
win_bools = [] # store if user won or not
winning_payout = [] # store winning payout amount
time_elapsed = 0
total_winnings = 0
subject_win_counter = 0

timeStep = 2 # modify step size during debugging (i.e. randDuration/2)
walk_start_time = 0
timecount = np.arange(walk_start_time,randDuration,timeStep) 
# Loop to get bids every 2 mins
for t in timecount:
	print("Trial #:", t)
	print('Enter Bid to continue walking for next 2 mins: ')
	subject_bid = input()

	# check whether input is appropriate float value 
	while True:
		try:
			subject_bid = float(subject_bid)
			break
		except:
			print("You have to type a float value")
			subject_bid = input()
	
	# get current subject & robo bids
	current_bids = [subject_bid]
	robotbids = currentRobomodel.get_bids()
	current_bids.extend(currentRobomodel.get_bids())
	print(current_bids) # prints full list of bids (1 human & # of robo-competitors)

	# verify that bids not all same
	number_of_unique_values = len(set(current_bids))
	if number_of_unique_values == 1:
		print("ALL BIDS ARE THE SAME")

	# Find minimum value of bid list & it's index, then display
	lowest_bid = min(current_bids)
	print("Winning Bid is:", lowest_bid)
	lowestBid_idx = current_bids.index(lowest_bid)

	# Get the 2nd lowest bid (payout)
	current_payout = sorted(current_bids)[1] 
	print("Winning Payout is:", current_payout)

	time_elapsed += timeStep # incrementing time elapsed by 2 mins
	user_win_flag = False

	# Determine whether user or Robobidder won
	if lowestBid_idx == 0:
		print("Human subject won!")
		
		total_winnings += current_payout # total human subject $ payout
		
		# increment subject win counter
		subject_win_counter += 1
		user_win_flag = True
	else:
		# make winning robot walk - cus it's not tired 
		print("Human lost")
		# Since human 1st idx, do 'lowest idx-1' to get lowest robot idx
		currentRobomodel.robobidderlist[lowestBid_idx-1].walk_old(time_elapsed, walk_start_time)

	# append each list of collected values  (bid matrix is list of lists)
	bid_matrix.append(current_bids)
	# Uncomment the lists below if you need the full time history
	#win_bools.append(user_win_flag)
	#winning_payout.append(current_payout)

	# Open file in write mode & create the csv writer
	with open(filename, 'a') as csvfile:
		csvwriter = csv.writer(csvfile)
		if (t == 0): # write headers & time stamp to csv file only once
			csvwriter.writerow(headers) 
			#csvwriter.writerow(timecount)
	
		# Filling data: time stamp, user bid amnt, human won/no, winning bid, human payout/winnings amnt
		csvwriter.writerow([t, subject_bid, user_win_flag, current_payout, total_winnings])
	

# Convert to bid matrix to np array to manipulate
arr_bid_matrix = np.array(bid_matrix)
print("Here is the full bid matrix: ")
print(arr_bid_matrix)

# plot bids of subject & all robots over time
fig, ax = plt.subplots()
ax.plot(timecount,arr_bid_matrix[:,0],'ro',label='Human Subject') # plotting human bids from 1st col
ax.plot(timecount,arr_bid_matrix[:,1],'bo',label='Robot 1')
ax.plot(timecount,arr_bid_matrix[:,2],'go',label='Robot 2')

# check # of columns of bid matrix to get # of robobidders
if arr_bid_matrix.shape[1] == 4:
	ax.plot(timecount,arr_bid_matrix[:,3],'o',label='Robot 3')

ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Bid ($/min)')
ax.legend()

plt.show()

