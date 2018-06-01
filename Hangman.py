import urllib3
import json
import random
from collections import Counter
import time
http = urllib3.PoolManager()

##################		Game Handler Methods		##################
game = None
def initGame():
	res = None
	try:
		res = http.request('GET', "http://upe.42069.fun/2PFte", retries=10)
	except urllib3.connection.ConnectionError:
		print("Could not get data")
		exit
	res = json.loads(res.data)
	
	global game
	game = res;

##################		Dictionary		##################
## The dictionary holds a list of all words previously used
## 		in 2 dictionaries, organized by length of the words
##		e.g. self.biasLengths[5]'s value is a list of all
##		words with length 5
## Also has class methods addWordLen, to insert words into
##		the dictionary during run-time, and delete (unused,
##		prefer to exclude pulling in words from findCandidates
##		rather than removing and reloading a whole dictionary)
class Dictionary:
	def __init__(self):
		self.loadWords()

	def loadWords(self):
		biasCounts = Counter(line.strip() for line in open('bias.txt'))
		biasList = sorted(biasCounts, key=lambda word: (-biasCounts[word], word))	# Create a list of words from bias.txt, ordered by frequency and duplicates removed
		wordsList = set(line.strip() for line in open('wordlist.txt'))
		self.biasLengths = {}
		for word in biasList:
			length = len(word)
			if not length in self.biasLengths:
				self.biasLengths[length] = [word.lower()]
			else:
				self.biasLengths[length].append(word.lower())
		self.wordLengths = {}
		for word in wordsList:
			length = len(word)
			if not length in self.wordLengths:
				self.wordLengths[length] = [word.lower()]
			else:
				self.wordLengths[length].append(word.lower())

	def addWordLen(self, word):
		length = len(word)
		if not length in self.biasLengths:
			self.biasLengths[length] = [word.lower()]
		else:
			self.biasLengths[length].append(word.lower())

	# def delete(self, letter):
	# 	print("delete %c" %letter)
	# 	for key in self.biasLengths:
	# 		self.biasLengths[key] = [word for word in self.biasLengths[key] if letter not in word]
	# 	for key, listWords in self.wordLengths.items():
	# 		temp = [word for word in listWords if letter not in word]
	# 		listWords = temp


##################		Letter Bank		##################
## Handler for managing and choosing letters
## Keeps track of letters we haven't guessed, letters we've
##		guessed, and letters we've guessed wrongly
## The object has a frequency dictionary, according to the
##		length of the word we're trying to guess.
class LetterBank:
	def __init__(self):
		self.reloadLetters()

		# Subset of alphabet in order of frequence with respect to the word's length
		self.frequency = {
			1: ['a', 'i'],
			2: ['a', 'o', 'e', 'i', 'u', 'm', 'b', 'h'],
			3: ['a', 'e', 'o', 'i', 'u', 'y', 'h', 'b', 'c', 'k'],
			4: ['a', 'e', 'o', 'i', 'u', 'y', 's', 'b', 'f'],
			5: ['s', 'e', 'a', 'o', 'i', 'u', 'y', 'h'],
			6: ['e', 'a', 'i', 'o', 'u', 's', 'y'],
			7: ['e', 'i', 'a', 'o', 'u', 's'],
			8: ['e', 'i', 'a', 'o', 'u'],
			9: ['e', 'i', 'a', 'o', 'u'],
			10: ['e', 'i', 'o', 'a', 'u'],
			11: ['e', 'i', 'o', 'a', 'd'],
			12: ['e', 'i', 'o', 'a', 'f'],
			13: ['i', 'e', 'o', 'a'],
			14: ['i', 'e', 'o'],
			15: ['i', 'e', 'a'],
			16: ['i', 'e', 'h'],
			17: ['i', 'e', 'r'],
			18: ['i', 'e', 'a'],
			19: ['i', 'e', 'a'],
			20: ['i', 'e'],
			26: ['e']	# dummy for when alphabet is inputted
		}

		# Array of letters that have been used, for match-improvement
		self.known = []
		# Array of letters that does not exist in the state, for findCandidate-improvement
		self.wrongGuess = []

	def reloadLetters(self):
		self.unused = (
		# Alphabet order in frequence of English text
		# ['e', 't', 'a', 'o', 'i', 'n', 's', 'h', 'r', 'd', 'l', 'c', 'u', 'm', 'w', 'f', 'g', 'y', 'p', 'b', 'v', 'k', 'j', 'x', 'q', 'z'])
		# Alphabet order in frequence of Dictionary (can we compile our own from scraped bias?)
		['e', 's', 'i', 'a', 'r', 'n', 't', 'o', 'l', 'c', 'd', 'u', 'p', 'm', 'g', 'h', 'b', 'y', 'f', 'v', 'k', 'w', 'z', 'x', 'q', 'j'])
		self.known = []
		self.wrongGuess = []

	def chooseLetter(self, word):
		score = 100	# we want to minimize score (index that appears in our freq tables/unused list first)
		letter =  None
		for char in word:
			if (not char.isalpha()) or (char not in self.unused):	# if we already used that letter, obviously can't use
				continue
			else:
				if(len(word) in self.frequency) and (char in self.frequency[len(word)]):
					lenFrequency = self.frequency[len(word)].index(char)
					if(lenFrequency < score):
						letter = char
						score = lenFrequency
				else:
					if(self.unused.index(char) < score):
						letter = char
						score = self.unused.index(char)
		if(letter == None):
			# Last resort just go down the list of frequent letters
			letter = self.unused[0]
		self.unused.remove(letter)
		self.known.append(letter)
		return letter


##################		Guessing Helper Methods		##################

def matches(unknown, candidate, bank):
	for chars in list(zip(unknown, candidate)):	# Iterate over chars[0], letters of unknown, and chars[1], letters of candidate
		if (chars[0] == '_'):				# '_' indicates letter
			if (not chars[1].isalpha()) or (chars[1] in bank.known): # If candidate has a letter we already guessed, and unknown is unknown there, candidate does not fit
				return False
		elif(chars[0] != chars[1]):
			return False
	return True

def findMatches(guess, arrWords, bank):
	ret = []
	# for word in arrWords
	#	for letter in word
	#		if letter not in bank.wrongGuess
	arrWords = [word for word in arrWords for letter in word if (letter not in bank.wrongGuess)]	# Remove all words that has a letter we wrongly guessed already
	for candidate in arrWords:
		if matches(guess, candidate, bank):
			ret.append(candidate.replace(',','').replace(':','').replace('.','').replace('(','').replace(')','').replace('{',''))
	return ret

def guessLetter(state, dictionary, bank):
	words = state.split()

	# run matching algorithm on every word with at least 1 blank,
	# choosing the one with the smallest pool of possibilities (higher chance of right word)
	candidatesArr = []
	for word in words:
		if '_' in word:
			candidates = findMatches(word, dictionary.biasLengths[len(word)], bank)
			if len(candidates)==0: #preference the bias first, only defaulting on dictionary if no matches are found
				candidates = findMatches(word, dictionary.wordLengths[len(word)], bank) #TODO ISSUE: words like "skin," with the comma won't be found in the dictionary
			if len(candidates) != 0: # if no words were found, we don't want to append an empty list
				candidatesArr.append(candidates)
	ret = []
	if(len(candidatesArr) > 0):
		ret = min(candidatesArr, key=len)	# choose smallest list of candidates
	return ret

	# # Find word with most blanks in it
	# toGuess = "a"
	# numBlanks = 0
	# for word in words:
	# 	countBlanks = 0
	# 	for letter in word:
	# 		if letter == '_':
	# 			countBlanks += 1
	# 	if countBlanks > numBlanks:
	# 		toGuess = word
	# 		numBlanks = countBlanks

	# # Find longest word that has at least 1 unknown
	# while "_" not in toGuess:
	# 	toGuess = max(words, key=len)
	# 	words.remove(toGuess)

	# candidates = findMatches(toGuess, dictionary.biasLengths[len(toGuess)])
	# if len(candidates)==0: #preference the bias first, only defaulting on dictionary if no matches are found
	# 	candidates = findMatches(toGuess, dictionary.wordLengths[len(toGuess)])
	# return candidates


###

initGame()
myDict = Dictionary()
letterBank = LetterBank()
entered = "y"
lives = 3

while entered != "x":
	words = guessLetter(game['state'], myDict, letterBank)
	letter = None
	if(len(words)!=0):		# if it returned something, aka not empty, call on letterBank to choose optimal letter
		for word in words:
			letter = letterBank.chooseLetter(word)
			if(letter != None):	# stop at first letter chosen (i.e. words appearing in the list first are preferenced)
				break
	else:
		print("no words")
		letter = letterBank.chooseLetter("")	# choose next most-frequent letter from whole alphabet if no candidates found

	# GUESS
	try:
		r = http.request("POST", "http://upe.42069.fun/2PFte",
		headers={"Content-Type": "application/json"}, body=json.dumps({"guess": letter}))
	except urllib3.connection.ConnectionError:
		print("No response from post request. Used %c" % letter)
		exit
	game = json.loads(r.data)
	print(game)

	# If we wrongly guess (is there a better way to check?), don't consider any words with that letter
	if(game['remaining_guesses'] < lives):
		lives -= 1
		if(lives == 0):
			lives = 3
		else:
			letterBank.wrongGuess.append(letter)

	 # If we lose, SCRAPE THOSE LYRICS ('lyrics' is part of response if we use all our guesses)
	if('lyrics' in game):
		with open("bias.txt", "a+") as biasFile:
			for line in game['lyrics'].split():
				biasFile.write("%s\n" % line)	# TODO: store these in memory then write in intervals/when program exits?
				myDict.addWordLen(line)
		# Start a new game
		initGame()
		letterBank.reloadLetters()

	#entered = input("Press Enter...")
	time.sleep(0.5)