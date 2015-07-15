"""Provides methods for obtaining, viewing, splitting oil production data"""
import csv
import cPickle
import gzip
import matplotlib.pyplot as plt
import numpy as np
import os
import random as rnd

# Parameters for reader
DATA_DIRECTORY = "../data"

# Splitting data
IN_MONTHS = 36
OUT_MONTHS = 12
MIN_MONTHS = IN_MONTHS + OUT_MONTHS
STEP_MONTHS = 24

# Preprocessing parameters
REMOVE_ZEROS = True
REMOVE_OUTLIERS = True
SMOOTH_DATA = False
NORMALIZE_DATA = True

OUTLIER_Z = 4
SMOOTH_LEN = 3

# Random seed
SEED = 42


def get_data():
	"""Returns dictionary containing data from files in data directory"""
	# Oil production data is contained in this dictionary
	# Keys are the oil well names
	# Values are lists containing oil production measurements
	data = {}
	
	# Get start directory
	startdir = os.getcwd()
	
	# Get data from files in data directory
	os.chdir(DATA_DIRECTORY)
	for filename in os.listdir(os.getcwd()):
		with open(filename, "rb") as csvfile:
			# Open each data file with csv reader
		    reader = csv.reader(csvfile, dialect="excel")

		    # Ignore the first line because it contains headers
		    reader.next()

		    # Add each row to the corresponding oil well
		    for row in reader:
		    	# Get data from cells and convert appropriately
		    	name = row[3]
		    	oil = float(row[4])

		    	# Add data to the dictionary
		    	if not name in data:
		    		data[name] = []
		        data[name].append(oil)

	# Go back to start directory
	os.chdir(startdir)
	
	# Return data dictionary
	return data


def preprocess_data(data):
	"""Returns preprocessed version of the data"""
	new_data = {}
	x = []
	y = []
	for name in data:
		# Remove zeroed data points (push points together)
		if REMOVE_ZEROS:
			oils = np.array(filter(lambda oil: oil != 0, data[name]))
		else:
			oils = np.array(data[name])
			
		# Skip data set unless standard deviation is non-zero
		if np.std(oils) == 0:
			continue
		
		# Remove outliers
		if REMOVE_OUTLIERS:
			oils = oils[abs(oils - np.mean(oils)) <= OUTLIER_Z*np.std(oils)]
			
		# Smooth data
		if SMOOTH_DATA:
			smooth_window = np.ones(SMOOTH_LEN)/SMOOTH_LEN
			oils = np.convolve(smooth_window, oils, mode="valid")
		
		# Skip data set unless standard deviation is not 0
		if np.std(oils) == 0:
			continue
		
		# Normalize data
		if NORMALIZE_DATA:
			oils = (oils - np.mean(oils))/np.std(oils)
		
		# Add to new data dictionary
		new_data[name] = oils
		
		# Make chunks
		for i in xrange(0, len(oils), STEP_MONTHS):
			in_index = i
			out_index = i + IN_MONTHS
			end_index = i + IN_MONTHS + OUT_MONTHS
			if end_index < len(oils):
				x.append(oils[in_index:out_index])
				y.append(oils[out_index:end_index])
	
	shuffled = list(zip(x, y))
	rnd.shuffle(shuffled)
	x, y = zip(*shuffled)
	return new_data, (np.array(x), np.array(y))


def plot_data(data):
	"""Plots the data using pyplot"""
	for name in data:
		# Create a figure and add a subplot with labels
		fig = plt.figure(1)
		graph = fig.add_subplot(111)
		fig.suptitle(name, fontsize=25)
		plt.xlabel("Year", fontsize=15)
		plt.ylabel("Production", fontsize=15)

		# Plot the data as a red line with round markers
		graph.plot(data[name], "r-o", label="Oil Production")

		# Add legend, resize windows, and display plot
		plt.legend()
		mng = plt.get_current_fig_manager()
		mng.resize(*mng.window.maxsize())
		plt.show()


def plot_chunks(chunks):
	"""Plots the chunks using pyplot"""
	for chunk in zip(chunks[0], chunks[1]):
		# Create a figure and add a subplot with labels
		fig = plt.figure(1)
		graph = fig.add_subplot(111)
		fig.suptitle("Chunk Data", fontsize=25)
		plt.xlabel("Year", fontsize=15)
		plt.ylabel("Production", fontsize=15)
		
		# Plot the predictions as a green line with round markers
		graph.plot(np.append(chunk[0], chunk[1]), "g-o", label="Predicted Output")

		# Plot the data as a red line with round markers
		graph.plot(chunk[0], "r-o", label="Oil Output")

		# Add legend, resize windows, and display plot
		plt.legend()
		mng = plt.get_current_fig_manager()
		mng.resize(*mng.window.maxsize())
		plt.show()
		
		
def generate_data_sets(chunks):
	"""Generate the training, validation, testing sets by splitting the chunks
	using 6:1:1 ratio"""
	train_set = (chunks[0][:6*len(chunks[0])/8,],
				 chunks[1][:6*len(chunks[0])/8,])
	valid_set = (chunks[0][6*len(chunks[0])/8:7*len(chunks[0])/8,],
				 chunks[1][6*len(chunks[0])/8:7*len(chunks[0])/8,])
	test_set = (chunks[0][7*len(chunks[0])/8:,],
				chunks[1][7*len(chunks[0])/8:,])
	return train_set, valid_set, test_set


if __name__ == '__main__':
	rnd.seed(SEED)
	print "Getting data..."
	data = get_data()
	print "Preprocessing data..."
	data, chunks = preprocess_data(data)
	print "Generating data sets..."
	data_sets = generate_data_sets(chunks)
	print "Writing data sets to qri.pkl.gz..."
	with gzip.open("qri.pkl.gz", "wb") as file:
		file.write(cPickle.dumps(data_sets))
	print "Done!"
	# print "Plotting data..."
	# plot_data(data)
	# print "Plotting chunks..."
	# plot_chunks(chunks)
