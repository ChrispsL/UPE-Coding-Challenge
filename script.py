import urllib3
import json
import random
from collections import Counter
import time
# contents = urllib2.urlopen("http://upe.42069.fun/2PFte").read();
http = urllib3.PoolManager()

game = None

def initGame():
	res = None
	try:
		res = http.request('GET', "http://upe.42069.fun/2PFte", retries=10)
	except urllib3.connection.ConnectionError:
		print("Could not get data")
		return
	# print(res)
	res = json.loads(res.data)
	global game
	game = res;

def patternWord(word):
	output = ""
	count = 1
	letters = [0] * 26
	for letter in word:
		if not letter.isalpha():
			continue
		index = ord(letter.lower()) - ord('a')
		if letters[index] != 0:
			output += chr(ord('0')+letters[index])
		else:
			letters[index] = count
			count += 1
			output += chr(ord('0')+letters[index])
	return output

class Dictionary:
	def __init__(self):
		self.loadWords()

	def loadWords(self):
		biasCounts = Counter(line.strip() for line in open('lyrics.txt'))
		self.biasList = sorted(biasCounts, key=lambda word: (-biasCounts[word], word))
		self.wordsList = set(line.strip() for line in open('wordlist.txt'))
		self.biasLengths = {}
		for word in self.biasList:
			length = len(word)
			if not length in self.biasLengths:
				self.biasLengths[length] = [word.lower()]
			else:
				self.biasLengths[length].append(word.lower())
		self.wordLengths = {}
		for word in self.wordsList:
			length = len(word)
			if not length in self.wordLengths:
				self.wordLengths[length] = [word.lower()]
			else:
				self.wordLengths[length].append(word.lower())
		# self.wordPatterns = {}
		# for word in self.wordsList:
		# 	pattern = patternWord(word)
		# 	if not pattern in self.wordPatterns:
		# 		self.wordPatterns[pattern] = [word.lower()]
		# 	else:
		# 		self.wordPatterns[pattern].append(word.lower())

	def addWordLen(self, word):
		length = len(word)
		if not length in self.biasLengths:
			self.biasLengths[length] = [word.lower()]
		else:
			self.biasLengths[length].append(word.lower())

	def delete(self, letter):
		for key, listWords in self.biasLengths.items():
			# print(listWords)
			temp = [word for word in listWords if letter not in word]
			listWords = temp
			# print(listWords)
		for key, listWords in self.wordLengths.items():
			temp = [word for word in listWords if letter not in word]
			listWords = temp

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
			20: ['i', 'e']
		}

	def reloadLetters(self):
		self.unused = (
		# Alphabet order in frequence of English text
		# ['e', 't', 'a', 'o', 'i', 'n', 's', 'h', 'r', 'd', 'l', 'c', 'u', 'm', 'w', 'f', 'g', 'y', 'p', 'b', 'v', 'k', 'j', 'x', 'q', 'z'])
		# Alphabet order in frequence of Dictionary (can we compile our own from scraped lyrics?)
		['e', 's', 'i', 'a', 'r', 'n', 't', 'o', 'l', 'c', 'd', 'u', 'p', 'm', 'g', 'h', 'b', 'y', 'f', 'v', 'k', 'w', 'z', 'x', 'q', 'j'])

	def chooseLetter(self, word):
		score = 100	# we want to minimize score (index that it appears in our freq tables)
		letter =  None
		for char in word:
			if (not char.isalpha()) or (char not in self.unused):	# if we already used that letter, obviously can't use
				# print("%c not in array" % char)
				continue
			else:
				if(char in self.frequency[len(char)]):
					lenFrequency = self.frequency[len(word)].index(char)
					if(lenFrequency < score):
						letter = char
						score = lenFrequency
				else:
					if(self.unused.index(char) < score):
						letter = char
						score = self.unused.index(char)
		if (letter != None):	# Likely all letters in this word has been chosen
			self.unused.remove(letter)
		if(letter == None):
			letter = self.unused.pop(0)	# last resort just go down the list of frequent letters
		return letter

def matches(word1, word2):
	for charPair in list(zip(word1, word2)):
		if (charPair[0] == '_'):
			if (not charPair[1].isalpha()):
				return False
			else:
				continue
		elif(charPair[0] != charPair[1]):
			return False
	return True

def findMatches(toGuess, sameLength):
	ret = []
	for candidate in sameLength:
		if matches(toGuess, candidate):
			ret.append(candidate.replace(',','').replace(':','').replace('.','').replace('(','').replace(')','').replace('{',''))
	return ret

def guessLetter(state, dictionary): #REMOVE COMMAS (and apostrophes?)
	words = state.split()
	#print(words)
	mostBlanks = "a"
	numBlanks = 0

	# # run matching algorithm on every word with at least 1 blank,
	# # choosing the one with the smallest pool of possibilities (higher chance of right word)
	# candidatesArr = []
	# for word in words:
	# 	if '_' in word:
	# 		candidates = findMatches(mostBlanks, dictionary.biasLengths[len(mostBlanks)])
	# 		if len(candidates)==0: #preference the bias first, only defaulting on dictionary if no matches are found
	# 			candidates = findMatches(mostBlanks, dictionary.wordLengths[len(mostBlanks)])
	# 		candidatesArr.append(candidates)
	# return min(candidatesArr, key=len)

	# toGuess = "_"
	# #left to right, word that still needs to be decoded
	# for word in words:
	# 	if '_' in word:
	# 		toGuess = word
	# 		continue

	#Find word with most blanks in it
	for word in words:
		countBlanks = 0
		for letter in word:
			if letter == '_':
				countBlanks += 1
		if countBlanks > numBlanks:
			mostBlanks = word
			numBlanks = countBlanks

	# # Find longest word that has at least 1 unknown
	# while "_" not in mostBlanks:
	# 	mostBlanks = max(words, key=len)
	# 	words.remove(mostBlanks)

	# print(toGuess)
	# candidates = findMatches(toGuess, dictionary.wordLengths[len(toGuess)])
	#print(mostBlanks)
	candidates = findMatches(mostBlanks, dictionary.biasLengths[len(mostBlanks)])
	if len(candidates)==0: #preference the bias first, only defaulting on dictionary if no matches are found
		candidates = findMatches(mostBlanks, dictionary.wordLengths[len(mostBlanks)])
	#print(candidates)
	return candidates


###


initGame()
myDict = Dictionary()
letterBank = LetterBank()

entered = "y"

while entered != "x":
	lives = 3
	words = guessLetter(game['state'], myDict)
	letter = None
	if(len(words)!=0):		#if it returned something, aka not empty
		for word in words:
			letter = letterBank.chooseLetter(word)
			if(letter != None):
				break
	print(letter)
	try:
		r = http.request("POST", "http://upe.42069.fun/2PFte",
		headers={"Content-Type": "application/json"}, body=json.dumps({"guess": letter}))
	except urllib3.connection.ConnectionError:
		print("No response from post request. Used %c" % letter)
		exit
	#game = game.read()
	game = json.loads(r.data)
	print(game)
	# print(game)
	#print(randWord)
	#print(words)
	# print(letter)
	if(game['remaining_guesses'] < lives):
		lives -= 1
		if(lives == 0):
			lives = 3
		else:
			myDict.delete(letter)

	if('lyrics' in game): #if we lose, SCRAPE THOSE LYRICS
		print(game)
		with open("lyrics.txt", "a+") as lyricsFile:
			for line in game['lyrics'].split():
				# contents = lyricsFile.read()
				# print(contents)
		#line = line.replace(',','').replace(':','').replace('.','').replace('(','').replace(')','').replace('{','')
		# do we want to strip these? These could be very easy catches that makes certain guesses work instantly
				# if line in contents:
				# 	print("\'%s\' in file\n" % line)
				# else:
				# 	lyricsFile.write("%s\n" % line)
				lyricsFile.write("%s\n" % line)
				myDict.addWordLen(line)
		initGame()
		letterBank.reloadLetters()

	# entered = input("Press Enter...")
	time.sleep(1)