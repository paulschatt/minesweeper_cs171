import random
from AI import AI
from Action import Action
import time


class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		self.rowDimension = rowDimension
		self.colDimension = colDimension
		self.totalMines = totalMines
		self.board = [['X' for i in range(rowDimension)] for j in range(colDimension)]
		self.remaining_mines = [[float('inf') for i in range(rowDimension)] for j in range(colDimension)]
		self.adjacentFlaggedTiles = [[0 for i in range(rowDimension)] for j in range(colDimension)]
		self.probabilities = [[float('inf') for i in range (rowDimension)] for j in range(colDimension)]
		self.lastX = startX
		self.lastY = startY
		self.coveredFields = rowDimension*colDimension
		self.safeFields = set()
		self.fieldsToFlag = set()
		
	def getAction(self, number: int) -> "Action Object":
		self.coveredFields -= 1
		if number >= 0:
			self.board[self.lastX][self.lastY] = number
			self.remaining_mines[self.lastX][self.lastY] = number - self.numAdjacentFlaggedFields(self.lastX, self.lastY)
		else:
			self.board[self.lastX][self.lastY] = '?'
			self.reduceAdjacentMineCounts(self.lastX, self.lastY)
		#If the last move has zero adjacent mines all of its neighbors are safe to uncover
		if(number == 0):
			self.addSafeFields(self.lastX, self.lastY)
		if not self.safeFields:
			self.findSafeFieldsToUncover()
			self.findPatternOneOne()
		if not self.fieldsToFlag:
			self.findFieldsToFlag()
			self.findPatternOneTwo()
			self.findPatternOneTwoGeneralized()
		while(self.safeFields):
			x, y = self.safeFields.pop()  
			if self.board[x][y] == 'X':  
				self.lastX, self.lastY = x, y
				return Action(AI.Action.UNCOVER, x, y)
		while(self.fieldsToFlag):
			x,y = self.fieldsToFlag.pop()
			if self.board[x][y] == 'X':  
				self.lastX, self.lastY = x, y
				self.totalMines -= 1
				return Action(AI.Action.FLAG, x, y)
		
		if(self.numOfTotalUncoveredFields() == 0):
			return Action(AI.Action.LEAVE)
		self.calcProbabilities()
		x, y = self.findBestFieldToUncoverProbabilistic()
		self.lastX, self.lastY = x, y
		if self.probabilities[x][y] < 0.6:
			if self.board[x][y] == 'X':
				return Action(AI.Action.UNCOVER, x, y)
		if self.totalMines/self.coveredFields <= 0.5:
			x, y = self.randomUncoverCoordinateAssignment()
			self.lastX, self.lastY = x, y
			return Action(AI.Action.UNCOVER, x, y)
		else:
			x, y = self.randomFlagCoordinateAssignment()
			self.lastX, self.lastY = x, y
			self.totalMines -= 1
			return Action(AI.Action.FLAG, x, y)
	#Around a field which has a count of 0, all fields are safe to uncover
	def addSafeFields(self, x, y):
		for i, j in self.adjacentFields(x, y):
			self.safeFields.add((i, j))


	def addFlagFields(self, x, y):
		for i, j in self.adjacentFields(x, y):
			self.fieldsToFlag.add((i, j))

	#Return at most 8 adjacent uncovered fields for a given coordinate	
	def adjacentFields(self, x, y):
		for j in range(y-1, y+2):
			for i in range(x-1, x+2):
				if 0 <= i < self.colDimension and 0 <= j < self.rowDimension and self.board[i][j] == 'X':
					yield i, j

	def allNeighbors(self, x, y):
		for j in range(y-1, y+2):
			for i in range(x-1, x+2):
				if 0 <= i < self.colDimension and 0 <= j < self.rowDimension:
					yield i,j
	def adjacentUncoveredFields(self,x,y):
		for j in range(y-1, y+2):
			for i in range(x-1, x+2):
				if 0 <= i < self.colDimension and 0 <= j < self.rowDimension and self.board[i][j] != 'X' and self.board[i][j] != '?':
					yield i, j
	#Number of adjacent flagged fields for a given coordinate
	def numAdjacentFlaggedFields(self, x, y):
		counter = 0
		for j in range(y-1, y+2):
			for i in range(x-1, x+2):
				if 0 <= i < self.colDimension and 0 <= j < self.rowDimension and self.board[i][j] == '?':
					counter += 1
		return counter

	#Number of adjacent covered fields for a given coordinate
	def numAdjacentCoveredFields(self, x, y):
		counter = 0
		for j in range(y-1, y+2):
			for i in range(x-1, x+2):
				if 0 <= i < self.colDimension and 0 <= j < self.rowDimension and self.board[i][j] == 'X':
					counter += 1
		return counter

	#Return a random field to uncover
	def randomUncoverCoordinateAssignment(self):
		while True:
			x = random.randrange(self.colDimension)
			y = random.randrange(self.rowDimension)
			if self.board[x][y] == 'X':
				return x, y
	#Return a random field to flag
	def randomFlagCoordinateAssignment(self):
		while True:
			x = random.randrange(self.colDimension)
			y = random.randrange(self.rowDimension)
			if self.board[x][y] == 'X' and self.noFlagContradictions(x, y):
				return x, y
			
	#If a field has n adjacent mines and all n adjacent mines have already been uncovered, it is safe to uncover the other adjacent fields
	def findSafeFieldsToUncover(self):
		for i in range(len(self.board)):
			for j in range(len(self.board[i])):
				if(self.board[i][j] == 'X'):
					neighbors = list(set(self.allNeighbors(i, j)))
					if(self.remaining_mines[i][j] == 0):
						self.addSafeFields(i, j)
	
	def findFieldsToFlag(self):
		for i in range(len(self.board)):
			for j in range(len(self.board[i])):
				if isinstance(self.board[i][j], int):
					num_mines = self.remaining_mines[i][j]
					covered_neighbors = list(self.adjacentFields(i, j))
					if len(covered_neighbors) == num_mines:
						# All covered neighbors are mines
						self.fieldsToFlag.update(covered_neighbors)
					elif num_mines == 0:
						# All covered neighbors are safe
						self.safeFields.update(covered_neighbors)
					
						
				
	def numOfTotalUncoveredFields(self):
		counter = 0
		for i in range(len(self.board)):
			for j in range(len(self.board[i])):
				if self.board[i][j] == 'X':
					counter += 1
		return counter
	#returns the probability that a field contains a mine
	def calcProbabilities(self):
		self.probabilities = [[float('inf') for i in range (self.rowDimension)] for j in range(self.colDimension)]
		for i in range(len(self.board)):
			for j in range(len(self.board[i])):
				if self.board[i][j] == 'X':
					if self.noFlagContradictions(i, j):
						neighbors = list(self.adjacentUncoveredFields(i, j))
						#self.probabilities[i][j] =  max([self.remaining_mines[x][y]/self.numAdjacentCoveredFields(x, y) for x, y in neighbors])
						for x, y in neighbors:
							if self.probabilities[i][j] == float('inf'):
								self.probabilities[i][j] = self.remaining_mines[x][y]/self.numAdjacentCoveredFields(x, y)
							else:
								self.probabilities[i][j] = max(self.probabilities[i][j], self.remaining_mines[x][y]/self.numAdjacentCoveredFields(x, y))
					else:
						self.probabilities[i][j] == 0
	def findBestFieldToUncoverProbabilistic(self):
		minProbability = 1
		x, y = -1, -1
		for i in range(len(self.probabilities)):
			for j in range(len(self.probabilities[i])):
				if self.board[i][j] == 'X':  # Covered tile
					if self.probabilities[i][j] == 0:
						return i, j  # Prioritize safe tile
					elif self.probabilities[i][j] < minProbability:
						x, y = i, j
		# Prioritize corners/edges among equally probable options
		return x, y

	def isEdgeOrCorner(self, x, y):
		return (x == 0 or x == self.colDimension - 1 or y == 0 or y == self.rowDimension - 1)
	
	def remaining_mines(self, i, j):
		if isinstance(self.board[i][j], int):
			return self.remaining_mines[i][j]
		return float('inf')
	#Check if setting a flag somewhere would result in contradiction
	def noFlagContradictions(self, i, j):
		for x, y in self.adjacentFields(i, j):
			if self.numAdjacentFlaggedFields(x, y) - 1 == self.board[x][y]:
				return False
		return True



	

	def findPatternOneOne(self):
		for x in range(len(self.board)):
			for y in range(1, len(self.board[x])):
				if(self.remaining_mines[x][y] == self.remaining_mines[x][y-1] == 1):
					adj1 = set(self.adjacentFields(x, y))
					adj2 = set(self.adjacentFields(x, y-1))
					if adj1 <= adj2:
						self.safeFields.update(adj2 - adj1)
					elif adj1 >= adj2:
						self.safeFields.update(adj1 - adj2)
		for x in range(1, len(self.board)):
			for y in range(len(self.board[x])):
				if(self.remaining_mines[x][y] == self.remaining_mines[x-1][y] == 1):
					adj1 = set(self.adjacentFields(x, y))
					adj2 = set(self.adjacentFields(x-1, y))
					if adj1 <= adj2:
						self.safeFields.update(adj2 - adj1)
					elif adj1 >= adj2:
						self.safeFields.update(adj1 - adj2)

	def findPatternOneTwo(self):
		for x in range(len(self.board)):
			for y in range(1, len(self.board[x])):
				if(self.remaining_mines[x][y] == 1 and self.remaining_mines[x][y-1] == 2):
					adj1 = set(self.adjacentFields(x, y-1))			
					adj2 = set(self.adjacentFields(x, y))
					if(len(adj1- adj2) == 1):
						diff = adj1 -adj2
						self.fieldsToFlag.update(diff)
				elif(self.remaining_mines[x][y-1] == 1 and self.remaining_mines[x][y] == 2):
					adj1 = set(self.adjacentFields(x, y))			
					adj2 = set(self.adjacentFields(x, y-1))
					if(len(adj1- adj2) == 1):
						diff = adj1 -adj2
						self.fieldsToFlag.update(diff)
		for x in range(1,len(self.board)):
			for y in range(len(self.board[x])):
				if(self.remaining_mines[x][y] == 1 and self.remaining_mines[x-1][y] == 2):
					adj1 = set(self.adjacentFields(x-1, y))			
					adj2 = set(self.adjacentFields(x, y))
					if(len(adj1- adj2) == 1):
						diff = adj1 -adj2
						self.fieldsToFlag.update(diff)
				elif(self.remaining_mines[x-1][y] == 1 and self.remaining_mines[x][y] == 2):
					adj1 = set(self.adjacentFields(x, y))			
					adj2 = set(self.adjacentFields(x-1, y))
					if(len(adj1- adj2) == 1):
						diff = adj1 -adj2
						self.fieldsToFlag.update(diff)
						
	def findPatternOneTwoGeneralized(self):
		for x in range(len(self.board)):
			for y in range(len(self.board[x]) - 1):
				if(self.remaining_mines[x][y] == (self.remaining_mines[x][y+1] - 1) and self.remaining_mines[x][y] != float('inf')):
					if(len(set(self.adjacentFields(x, y + 1)) -set(self.adjacentFields(x, y))) <= 1):
							extra_fields = set(self.adjacentFields(x, y + 1)) - set(self.adjacentFields(x, y))
							self.fieldsToFlag.update(extra_fields)
				elif(self.remaining_mines[x][y] - 1 == (self.remaining_mines[x][y+1]) and self.remaining_mines[x][y] != float('inf')):
					if(len(set(self.adjacentFields(x, y)) -set(self.adjacentFields(x, y + 1))) <= 1):
							extra_fields = set(self.adjacentFields(x, y)) - set(self.adjacentFields(x, y +1))
							self.fieldsToFlag.update(extra_fields)
		for x in range(len(self.board) - 1):
			for y in range(len(self.board[x])):
				if(self.remaining_mines[x][y] == (self.remaining_mines[x+1][y] - 1) and self.remaining_mines[x][y] != float('inf')):
					if(len(set(self.adjacentFields(x+1, y)) -set(self.adjacentFields(x, y))) <= 1):
							extra_fields = set(self.adjacentFields(x + 1, y)) - set(self.adjacentFields(x, y))
							self.fieldsToFlag.update(extra_fields)
				elif(self.remaining_mines[x][y] - 1 == (self.remaining_mines[x+1][y]) and self.remaining_mines[x][y] != float('inf')):
					if(len(set(self.adjacentFields(x, y)) -set(self.adjacentFields(x+1,y))) <= 1):
							extra_fields = set(self.adjacentFields(x, y)) - set(self.adjacentFields(x + 1, y))
							self.fieldsToFlag.update(extra_fields)
	def isSafe(self, x, y):
		return isinstance(self.board[x][y], int)
	
	


	def reduceAdjacentMineCounts(self, x, y):
		for j in range(y-1, y+2):
			for i in range(x-1, x+2):
				if 0 <= i < self.colDimension and 0 <= j < self.rowDimension and isinstance(self.remaining_mines[i][j], int):
					self.remaining_mines[i][j] -= 1