
import gzip

class Reader:
   def __init__( self, fname=None ):
	self.fname = fname
	try:
	   if not fname:
		return

	   if fname.endswith('.gz') or fname.endswith('.bgz'):
		self.file = gzip.open( fname, 'rb' )
	   else:
		self.file = open( fname, 'r' )
	except IOError, e:
		pass

   def exists(self):
	try:
		self.file
		return True
	except AttributeError:
		return False

   def notExistExit(self):
	try:
		self.file
	except AttributeError:
		print self.fname +'\tnot exist'
		exit(1)

   def readline( self ):
	return self.file.readline()

   def next( self ):
	line = self.readline()

        if not line:
            raise StopIteration()
        return line
   def __iter__( self ):
	return self

class ReaderStat( Reader ):
   def __init__( self, fname=None ):
	Reader.__init__( self, fname )

	if not self.exists():
		return

	self.head = self.file.readline().strip('\n')
	hdr = self.head.split('\t')
	self.dct = dict((hdr[n],n) for n in xrange(len(hdr)))

	self.idxID = [self.dct['chr'], self.dct['position'], self.dct['variant']];

	line = self.file.readline()
	if line == '': return
	
	self.cLine = line.strip('\n')
	self.cTerms= self.cLine.split('\t')
	self.cID   = ':'.join( [self.cTerms[n] for n in self.idxID] )

   def readLine( self ):
	while self.file:
		self.cLine = self.file.readline().strip('\n');
		if len(self.cLine) < 1 or self.cLine[0] != '#': break

	if self.cLine == '' or not self.file :
		self.cLine = ''
		self.cTerm = []
		self.cId = ''
		return False

	self.cTerms = self.cLine.split('\t')
	self.cID   = ':'.join( [self.cTerms[n] for n in self.idxID] )
	return True
	
   def getFamilyData( self ):
	return self.cTerms[ self.dct['familyData'] ]
   
   def getStat( self ):
	v = [int(self.cTerms[self.dct[x]]) for x in ['all.nParCalled','all.nAltAlls']]
	w = [float(self.cTerms[self.dct[x]])/100. for x in ['all.prcntParCalled','all.altFreq']]

	return v, w

class Writer:
   def __init__( self, fname=None ):
      self.bgzFlag = False

      if not fname:
	self.file = sys.stdout
      else:
	if fname.endswith( '.bgz' ):
		self.bgzFlag = True

		terms = fname.split('.')
		self.filename = '.'.join( terms[0:(len(terms)-1)] )
		self.file = open( self.filename, 'w' )
	elif fname.endswith('.gz'):
		self.file = gzip.open( fname, 'wb' )
	else:
		self.file = open(fname, 'w' )

   def __del__(self):
	if not self.bgzFlag: return

	self.file.close()
	try:
		fname =  self.filename
		os.system( 'bgzip '+ fname +'; mv '+ fname +'.gz '+ fname +'.bgz' )#, self.filename+'.bgz' )
	except IOError, e:
		print e

   def write( self, xstr ):
	self.file.write( xstr )

#is autosomal
def isPseudoAutosomalX( pos ):
	#hg19 pseudo autosomes region: chrX:60001-2699520
	# and chrX:154931044-155260560 are hg19's pseudo autosomal
	flag = not ((pos < 60001) or ((pos >= 2699520) and (pos < 154931044)) or (pos >= 155260560))

	return flag

# p : parents, mother and father, state of ref or alternative
# p : [mother state, father state]
def posStateAuto( p ): #parent state for reference or alternative
	m = [1]*p[0] + [0]*(2-p[0])
	f = [1]*p[1] + [0]*(2-p[1])
	return set( [m[0]+f[0], m[0]+f[1], m[1]+f[0],m[1]+f[1]] )

#male only inherits mother's
def posStateXMale( p ):
	m = [1]*p[0] + [0]*(2-p[0])
	return set( m )

# p[1]: father can not be 2
# female should have fathers
def posStateXFemale( p ):
	m = [1]*p[0] + [0]*(2-p[0])
	f = [1]*p[1] + [0]*(1-p[1])	
	return set( [m[0]+f[0], m[1]+f[0]] )

class dbFamily:
   def __init__( self, fname ):
	infile = Reader( fname )
	self.head = infile.readline().strip('\n')
	hdr = self.head.split('\t')
	self.dct = dict((hdr[n],n) for n in xrange(len(hdr)))

	self.family = dict()
	for line in infile:
		line = line.strip('\n')
		terms = line.split('\t')

		fid = terms[0].split('-')[0]
		fid = fid[5:]

		self.family[fid] = terms[1:]
   def size( self, fn ):
	if fn in self.family:
		return int(self.family[fn][0])

	return 0

   def samples( self, fn ):
	if fn in self.family:
		return self.family[fn][1].split(',')

	return None

   def gender( self, fn ):
	if fn in self.family:
		return self.family[fn][2].split(',')

	return None

   def alpha( self, fn ):
	if fn in self.family:
		return [float(x) for x in self.family[fn][3].split(',')]

	return None

def tooManyFile( xstr ):
	if xstr.endswith('.txt.gz') or xstr.endswith('.txt.bgz'):
		xloc = 3
	else:
		xloc = 2

	terms = xstr.split('.')
	terms[len(terms)-xloc] += '-TOOMANY'

	return '.'.join( terms )
