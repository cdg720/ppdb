import gzip, sys
from collections import OrderedDict


from bllipparser import Tree, RerankingParser
from preprocess import Corpus

class Parser:
	def __init__(self):
		parser = '/pro/dpg/dc65/models/dk-wsj'
		reranker = '/pro/dpg/dc65/models/WSJ/reranker/'
		self.rrp = RerankingParser()
		self.rrp.load_parser_model(parser + '/parser')
		self.rrp.load_reranker_model(reranker + 'features.gz', reranker + '/weights.gz')
		#self.rrp.set_parser_options(nbest=50)

	def parse2(self, gold_tree, paraphrase, debug=False):
		self.gold_tree = Tree(gold_tree)
		# if len(self.gold_tree.tokens()) > 15:
		# 	return
		self.paraphrase = paraphrase
		#print paraphrase
		#print
		self.build_constraints()
		# print paraphrase
		# print self.constraints
		# print
		try:
			parsed = self.rrp.parse_constrained(paraphrase.sent.split(), self.constraints)
			if parsed:
				return parsed[0].ptb_parse, True
			else:
				return 'FAILED: ' + paraphrase.sent, False
		except:
			#print self.constraints
			return 'ERROR: ' + paraphrase.sent, False

	# build constraints
	def build_constraints(self, debug=False):
		old_words = self.paraphrase.sent.split()
		old_span = self.paraphrase.old_span
		source = self.paraphrase.source.split()
		source_span = self.paraphrase.source_span

		self.spans_to_preserve = []
		#if old_span[0] != 0:
		#	spans_to_preserve.append((0, old_span[0]))
		for span, src in zip(source_span, source):
			if src.startswith('[') and src.endswith(']'):
				self.spans_to_preserve.append({'span':span, 'label':src[1:-3]})
		#if old_span[1] != len(old_words)+1:
		#	spans_to_preserve.append((old_span[1], len(old_words)+1))

		# print spans_to_preserve
		# print
		# if True:
		# 	return
		
		new_span = self.paraphrase.new_span
		target = self.paraphrase.target.split()
		target_span = []
		span_map = []

		self.top_label_on = {}
		index = new_span[0]
		for new_word in target:
			# non-terminal or pre-terminal mapping
			if new_word.startswith('[') and new_word.endswith(']'):
				tmp = source_span[source.index(new_word)]
				target_span.append((index, index + tmp[1] - tmp[0]))
				span_map.append((source_span[source.index(new_word)], (index, index + tmp[1] - tmp[0]), new_word[1:-3]))
				self.top_label_on[(index, index + tmp[1] - tmp[0])] = {}
				self.top_label_on[(index, index + tmp[1] - tmp[0])][new_word[1:-3]] = False
				index += tmp[1] - tmp[0]
			else: # word mapping
				index += 1

		# print self.top_label_on
		# print span_map
		# print self.paraphrase

		self.constraints = OrderedDict()
		for subtree in self.gold_tree.all_subtrees():
			count = 0
			span = subtree.span()
			label = subtree.label()
			# LEFT 
			if span[1] <= old_span[0]: 
				count += 1
				self.message = ['LEFT', span, old_span[0], label]
				self.update_constraints2(span, label, debug=debug)
			# RIGHT
			if span[0] >= old_span[1]: 
				count += 1
				self.message = ['RIGHT', span, old_span[1], label]				
				diff = len(source) - len(target)
				new_span = (span[0] - diff, span[1] - diff)
				self.update_constraints2(new_span, label, debug=debug)

			# INSIDE
			count2 = 0
			for ss_ts in span_map: # (source_span, target_span)
				if ss_ts[0][0] <= span[0] and span[1] <= ss_ts[0][1]:
					count2 += 1
					self.message = ['INSIDE', span, ss_ts[0], label, span_map]
					diff = ss_ts[0][0] - ss_ts[1][0] # source[0] - target[0]
					new_span = (span[0] - diff, span[1] - diff)
					self.update_constraints2(new_span, label, ss_ts[2], debug=debug)

			# OUTSIDE
			if span[0] <= old_span[0] and span[1] >= old_span[1]:
				count += 1
				diff = len(source) - len(target)
				new_span = (span[0], span[1] - diff)
				self.message = ['OUTSIDE', span, new_span, label]
				self.update_constraints2(new_span, label, debug=debug)
			
			if count > 1 or (count > 0 and count2 > 0):
				print 'OH NO!'
					

		# print self.constraints
		#return self.constraints
		#print

	def update_constraints2(self, span, label, top_label=None, debug=False):
		if span in self.top_label_on and top_label:
			if top_label == label:
				# print span, label
				self.top_label_on[span][label] = True
			elif not self.top_label_on[span][top_label]:
				return

		if span not in self.constraints:
			self.constraints[span] = []
		# if label not in self.constraints[span]:
		# 	self.constraints[span] = []
		self.constraints[span].append(label)

	# def parse(self, original_tree, paraphrase, debug=False):
	# 	if debug:
	# 		print original_tree
	# 		print paraphrase
	# 		print

	# 	self.gold_tree = Tree(original_tree)
	# 	#self.paraphrase
			
	# 	words = paraphrase.sent.split()
	# 	nbest = self.rrp.parse(words)
	# 	for i, cand in enumerate(nbest):
	# 		if self.satisfied(cand.ptb_parse, paraphrase, debug):
	# 			return (cand.ptb_parse, i)
	# 	# for i, tree in enumerate(nbest):
	# 	# 	print i, tree.ptb_parse
	# 	return None

	# # there is a bug. find it!
	# #@staticmethod
	# def satisfied(self, parse, paraphrase, debug=False):
	# 	self.candidate = parse
	# 	self.paraphrase = paraphrase
	# 	left, right = paraphrase.new_span
	# 	old_span = paraphrase.old_span
	# 	source = paraphrase.source.split()
	# 	source_span = paraphrase.source_span
	# 	# print source
	# 	# print source_span
	# 	span_map = []
	# 	target_span = []
	# 	index = left
	# 	for word in paraphrase.target.split():
	# 		if word.startswith('[') and word.endswith(']'):
	# 			tmp = source_span[source.index(word)]
	# 			target_span.append((index, index + tmp[1] - tmp[0]))
	# 			span_map.append((source_span[source.index(word)], (index, index + tmp[1] - tmp[0])))
				
	# 			index += tmp[1] - tmp[0]
	# 		else:
	# 			target_span.append((index, index + 1))
	# 			index += 1
	# 	#print span_map
	# 	self.constraints = OrderedDict()
	# 	for subtree in self.gold_tree.all_subtrees():
	# 		span = subtree.span()
	# 		label = subtree.label()
	# 		''' here too '''
	# 		if span[1] <= left:
	# 			self.message = ['LEFT', span, left, label]
	# 			self.update_constraints(span, label, debug=debug)
	# 		''' this seems wrong '''
	# 		if span[0] >= right:
	# 			self.message = ['RIGHT', span, right, label]				
	# 			diff = target_span[-1][1] - source_span[-1][1]
	# 			new_span = (span[0] + diff, span[1] + diff)
	# 			self.update_constraints(new_span, label, debug=debug)				
	# 		for ss_ts in span_map:
	# 			if ss_ts[0][0] <= span[0] and span[1] <= ss_ts[0][1]:
	# 				self.message = ['MID', span, ss_ts[0], label, span_map]
	# 				diff = ss_ts[1][0] - ss_ts[0][0]
	# 				new_span = (span[0] + diff, span[1] + diff)
	# 				self.update_constraints(new_span, label, debug=debug)
	# 	# print paraphrase
	# 	# for key in sorted(constraints):
	# 	# 	print key, constraints[key]

	# 	# if debug:
	# 	# 	print parse
	# 	# 	print constraints
	# 	# 	print
		
	# 	for subtree in parse.all_subtrees():
	# 		span = subtree.span()
	# 		label = subtree.label()
	# 		if span in self.constraints and label not in self.constraints[span]:
	# 			return False
	# 	return True
	
	# def update_constraints(self, span, label, debug=False):
	# 	if span in self.constraints:
	# 		#if label in constraints[span] and debug: # copy should not exist
	# 		if label in self.constraints[span]: # copy should not exist
	# 			print self.message
	# 			print self.gold_tree
	# 			print self.candidate
	# 			print self.paraphrase
	# 			print self.constraints
	# 			print label, span, self.constraints[span]
	# 			print 'oh fuck'
	# 			print
	# 	else:
	# 		self.constraints[span] = set()
	# 	self.constraints[span].add(label)

def break_data():
	corpus = Corpus(sys.argv[1])
	count = 0
	count2 = 0
	for paraphrases in corpus.sets:
		if count % 100 == 0:
			out = gzip.open('/home/dc65/research/paraparsing/ppdb/data2/' + str(count / 100 + 1) + '.gz', 'wb')
		out.write(str(paraphrases.id) + '\n')
		out.write(paraphrases.tree + '\n')
		out.write(paraphrases.sent + '\n')
		out.write(str(len(paraphrases.items)) + '\n')
		for paraphrase in paraphrases.items:
			count2 += 1
			out.write(paraphrase.sent + '\n')
			out.write(paraphrase.lhs + '\n')
			out.write(','.join([str(x) for x in paraphrase.old_span]) + '\n')
			out.write(','.join([str(x) for x in paraphrase.new_span]) + '\n')
			out.write(paraphrase.source + '\n')
			tmp = [','.join([str(x[0]), str(x[1])]) for x in paraphrase.source_span]
			out.write(' '.join([x for x in tmp]) + '\n')
			out.write(paraphrase.target + '\n')
		count += 1
	print count2

break_data()

def main():
	p = Parser()
	corpus = Corpus(sys.argv[1])
	for paraphrases in corpus.sets:
		tmp = []
		for paraphrase in paraphrases.items:
			#p.parse2(paraphrases.tree, paraphrase)
			parse, good = p.parse2(paraphrases.tree, paraphrase)
			if good:
				tmp.append(parse)
		if tmp:
			# print paraphrases.tree
			print paraphrases.id, len(tmp)
			for t in tmp:
				print t
			# print

#main()
