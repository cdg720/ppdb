from transformation import *
import sys
from bllipparser import Tree


ppdb = PPDB(sys.argv[1])
#print ppdb.pp_table
tran = Transformation(ppdb)
trees = [Tree(line) for line in open(sys.argv[2])]

count = 0
for i, tree in enumerate(trees):
	matches = tran.transform(tree)

	if matches:
		count += 1
		print i
		print tree
		print ' '.join(tree.tokens())
		print len(matches)
		for match in matches:
			print ' '.join(match[0])
			print match[3][0] # LHS
			print ','.join([str(x) for x in match[1]]) # old span
			print ','.join([str(x) for x in match[2]]) # new span
			print ' '.join([x[0] for x in match[4]]) # SOURCE
			print ' '.join([','.join([str(xx) for xx in y]) for y in [z[1] for z in match[4]]])
			print ' '.join(match[5]) # TARGET			
			#print ' '.join([[','.join(xx) for xx] in x for x in match[4]]) # SOURCE span

		#print ''.join(['=' for x in xrange(150)])
