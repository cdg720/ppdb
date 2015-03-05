import gzip, sys

class Paraphrase:
	def __init__(self, para):
		self.sent, self.lhs, self.old_span, self.new_span, self.source, self.source_span, self.target = para

	def __str__(self):
		return 'PARAPHRASE:\t' + self.sent + '\nLHS:     \t' + self.lhs + '\nOLD SPAN:\t' + str(self.old_span) + '\nNEW SPAN:\t' + str(self.new_span) + '\nSOURCE:  \t' + self.source + '\nSOURCE SPAN:\t' + str(self.source_span) + '\nTARGET:   \t' + self.target

class Paraphrases:
	def __init__(self, info, paras):
		self.id, self.tree, self.sent = info
		self.items = [Paraphrase(para) for para in paras]

	def __str__(self):
		s = 'ID:      \t' + str(self.id) + '\nTREE:    \t' + self.tree + '\nSENTENCE:\t' + self.sent + '\n'
		s += '\n'.join([str(paraphrase) for paraphrase in self.items])
		return s

class Corpus:
	def __init__(self, file):
		f = gzip.open(sys.argv[1])
		count = [0, 3, 0]
		total = 0
		sets = []
		
		for line in f:
			line = line[:-1]
			if count[0] == 0:
				if count[1] == 3: # start of a set of paraphrases
					x = [int(line)]
					y = []
					z = []
				elif count[1] == 2: # orig tree
					x.append(line) 
				elif count[1] == 1: # orig sent
					x.append(line)
				else: # # of parapharses
					count[0] = int(line)
					total += count[0] + 1
					count[2] = 7
				count[1] -= 1
			else:
				if count[2] == 5 or count[2] == 4: # old/new span
					t = line.split(',')
					z.append((int(t[0]), int(t[1])))
				elif count[2] == 2:
					t = line.split()
					tmp = []
					for tt in t:
						tmp.append(tuple([int(ttt) for ttt in tt.split(',')]))
					z.append(tmp)
				else:
					z.append(line)
				count[2] -= 1
				if count[2] == 0:
					y.append(z)
					z = []
					count[0] -= 1
					if count[0] == 0: # end of a set
						sets.append(Paraphrases(x, y))
						count[1] = 3
					else:
						count[2] = 7
		self.sets = sets

# def main():
# 	corpus = Corpus(sys.argv[1])
# 	for paraphrases in corpus.sets:
# 		print paraphrases.sent
# 		for paraphrase in paraphrases.items:
# 			print paraphrase.sent


# main()
