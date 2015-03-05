import gzip, string, sys
from bllipparser import Tree

class PPDB:
	pp_table = {}

	def __init__(self, ppdb):
		f = gzip.open(ppdb)
		for line in f:
			tokens = line.split(' ||| ')
			src = tokens[1].split()
			if PPDB.filter_numbers(src, tokens[2].split()):
				continue
			if tokens[0][1:-1] not in self.pp_table: # LHS
				self.pp_table[tokens[0][1:-1]] = {}
			lhs_map = self.pp_table[tokens[0][1:-1]]

			src_map = lhs_map
			for s in src:
				if s not in src_map:
					src_map[s] = {}
				src_map = src_map[s]
			if 'TARGET' not in src_map:
				src_map['TARGET'] = {}
			tgt_map = src_map['TARGET']
			if tokens[2] not in tgt_map: # LHS, SOURCE, TARGET
				tgt_map[tokens[2]] = []
			tgt_map[tokens[2]].append(tokens[4])

	''' Ignore the same number written in two different styles: 10,000 10000. Maybe need to check the other way too. '''
	@staticmethod
	def filter_numbers(x, y): 
		if len(x) == len(y):
			diff = 0
			for xx, yy in zip(x, y):
				if xx == yy:
					continue
				try:
					float(xx)
					float(yy.replace(',', ''))
					diff += 1
				except Exception as e:
					#print e
					pass
			if diff == 1:
				return True
		return False


# TODO: capitalization
class Transformation:
	def __init__(self, ppdb):
		self.pp_table = ppdb.pp_table

	''' recurse match function '''
	def match(self, table, state, curr, end, nonwords):
		if 'TARGET' in table and curr == end: # match found
			self.matches.append(state) 
			return
		if curr >= end: # no match
			return 

		for i, item in enumerate(self.leaves[curr]):
			if i == 0: # word
				x = item[0].lower()
				if x in table:
					self.match(table[x], state + [(x,item[1])], curr+1, end, nonwords) 
			else: # preterminal or nonterminal
				if nonwords == 2:
					return # no match
				x = '[' + item[0] + ',' + str(nonwords+1) + ']'
				if x in table:
					self.match(table[x], state + [(x,item[1])], item[1][1], end, nonwords+1)

	''' Given a tree and an entry of PPDB, generate its paraphrase. '''
	def paraphrase(self, lhs, src, tgt):
		start, end = lhs[1]
		tokens = self.tree.tokens()
		left = list(tokens[:start])
		right = list(tokens[end:])
		tmp = []
		para = []
		orig = []
		index = start
		for word in src:
			if word[0].startswith('[') and word[0].endswith(']'):
				word, span = word[0][1:-3], word[1]
				for x in self.leaves[index]:
					if word == x[0] and span == x[1]:
						a, b = x[1]
						orig.extend(tokens[a:b])
						tmp.append(tokens[a:b])
						index = b
						break
			else:
				orig.append(tokens[self.leaves[index][0][1][0]])
				#orig.append(word[0])
				index += 1

		for word in tgt:
			if word.startswith('[') and word.endswith(']'):
				if word[-2] == '1':
					para.extend(tmp[0])
				else:
					para.extend(tmp[1])
			else:
				para.append(word)

		# start of a sentence
		if start == 0 and para[0][0].islower():
			para[0] = para[0].capitalize() 

		# capitalized words in the middle of sentence
		if start == 0 and self.tree.tags()[start] != 'NNP' and self.tree.tags()[start] != 'NNPS':
			x = orig[0]
			index = -1
			for i in xrange(1, len(para)):
				if para[i] == x:
					index = i
			if index == -1: # no match
				pass
				# ????
				# if para[0].lower() != x:
				# 	print x, para[0].lower()
				# 	print orig
				# 	print para
				# 	print 'oh no'
			else:
				# print x
				# print orig
				# print para
				para[index] = para[index].lower()
				# print para
				# print

		return left + para + right, (start, end), (start, end + len(tgt) - len(src))

	def valid(self, lhs, src):
		to_be_satisfied = {}
		for s in src:
			if s[0].startswith('[') and s[0].endswith(']'):
				to_be_satisfied[s[1]] = s[0][1:-3]
		for subtree in self.tree.all_subtrees():
			label = subtree.label()
			span = subtree.span()
			if label == lhs[0] and span == lhs[1]:
				tmp = subtree
				for child in subtree.subtrees():
					span2 = child.span()
					if span2 in to_be_satisfied:
						if to_be_satisfied[span2] == child.label():
							del to_be_satisfied[span2]
				break

		# TODO: check if valid() bug-free.
		if to_be_satisfied:
			# print to_be_satisfied
			# print lhs
			# print src
			# print tmp
			# print
			return False
		else:
			return True

	def transform(self, tree):
		''' pre-processing starts. '''
		leaves = [[] for x in xrange(tree.span()[1])]
		for subtree in tree.all_subtrees():
			subtree.label_suffix = ''
			label = subtree.label()
			# bllipparser.Tree assigns S1 to top nodes
			if label != 'S1':
				if subtree.is_preterminal() and label == ',':
					leaves[subtree.span()[0]].append(('COMMA', subtree.span()))
				else:
					leaves[subtree.span()[0]].append((label, subtree.span()))
		tokens = tree.tokens()
		for i in xrange(len(leaves)):
			leaves[i].append((tokens[i], (i, i+1)))
			leaves[i].reverse()
		self.tree = tree
		self.leaves = leaves
		self.matches = []
		#self.int_to_tree = {}
		''' pre-processing ends. '''

		''' Find matches corresponding to entries in PPDB. '''
		# probably i is not needed
		for i, subtree in enumerate(tree.all_subtrees()):
			label = subtree.label()			
			if label != 'S1':
				span = subtree.span()
				# This node spans more than one word.
				if span[1] - span[0] != 1: 
					if label in self.pp_table:
						#self.int_to_tree[i] = subtree
						self.match(self.pp_table[label], [(label, span)], span[0], span[1], 0)

		''' post-processing starts. '''
		check = set()
		check.add(' '.join(tokens).lower())
		new_trees = []
		for match in self.matches:
			tgt = self.pp_table[match[0][0]]
			for m in match[1:]:
				tgt = tgt[m[0]]
			for cand in tgt['TARGET']:
				if not self.valid(match[0], match[1:]):
					continue
				para, old, new = self.paraphrase(match[0], match[1:], cand.split())
				pp = ' '.join(para).lower()
				if pp not in check:
					check.add(pp)
					new_trees.append((para, old, new, match[0], match[1:], cand.split()))
		return new_trees
