# -*- mode:python;tab-width:2;indent-tabs-mode:t;show-trailing-whitespace:t;rm-trailing-spaces:t -*-
import os,sys,inspect
newpath = os.path.dirname(inspect.getfile(inspect.currentframe())) # script directory
if not newpath in sys.path: sys.path.append(newpath)
import string,re,gzip,itertools
from pymol import cmd
import LA as la
from sym_util import *
from pymol_util import *

def homogenizechains(sel1,sel2):
   cmd.remove("hydro")
   cmd.remove("resn HOH")
#   cmd.remove("(HET and not resn MSE+CSW)")
   a = cmd.get_model("%s and name ca"%(sel1))
   b = cmd.get_model("%s and name ca"%(sel2))
   sa = "".join([name1[x.resn] for x in a.atom if x.resn in name1])
   sb = "".join([name1[x.resn] for x in b.atom if x.resn in name1])
   if sa==sb: return True
   ra = [myint(x.resi) for x in a.atom]
   rb = [myint(x.resi) for x in b.atom]
#   if max(ra) - min(ra) + 1 != len(ra): print "missing residue numbers",max(ra),min(ra),len(ra)
#   if max(rb) - min(rb) + 1 != len(rb): print "missing residue numbers",rb
   mla,mua,mlb,mub = lcs(sa,sb)
   bla,bua,blb,bub = lcs(sa[  :mla],sb[  :mlb])
   ala,aua,alb,aub = lcs(sa[mua+1:],sb[mub+1:])
   ra = ra[mla:(mua+1)]
   rb = rb[mlb:(mub+1)]
   if len(ra[bla:(bua+1)]) > 10:
      ra = ra[bla:(bua+1)] + ra[mla:(mua+1)] + ra[ala:(aua+1)]
      rb = rb[blb:(bub+1)] + rb[mlb:(mub+1)] + rb[alb:(aub+1)]
   if len(ra[ala:(aua+1)]) > 10:
      ra += ra[ala:(aua+1)]
      rb += rb[alb:(aub+1)]
   for c,i in getres("%s"%(sel1)):
      if not i in ra: cmd.remove("%s and resi %i"%(sel1,i))
   for c,i in getres("%s"%(sel2)):
      if not i in rb: cmd.remove("%s and resi %i"%(sel2,i))
   return False

def pickandfixchains(N,sel="all"):
   # find chains
   # homogenize all pairs until fixed
   cc = []
   for c in getchain(sel):
      cc.append((-cmd.select("%s and chain %s and name CA"%(sel,c)),c))
   cc.sort()
   chains = [x[1] for x in cc[:N]]
   done = False
   count = 0
   while not done:
      if count > 10: break
      count += 1
      done = True;
      random.shuffle(chains)
      for i in range(1,len(chains)):
         done = done and homogenizechains(sel,chains[0],chains[i])
   print chains
   if N is 2: alignc2(sel,"name ca",chains=chains)
   if N is 3: alignc3(sel,"name ca",chains=chains)
   if N is 4: alignc4(sel,"name ca",chains=chains)
   if N is 5: alignc5(sel,"name ca",chains=chains)
   chains.sort()
   return chains[0]


def processhomomers():
   o = open("log",'w')
   for n in (2,3,4,5):
      files = glob.glob("c%ipdb/*.pdb.gz"%n)
      random.shuffle(files)
      for f in files:
         o.write(f+"\n")
         o.flush()
         cmd.delete("all")
         try:
            cmd.load(f)
            c = pickandfixchains(n)
            cmd.save("c%ia/"%n+f[3:-3],"chain %s"%c)
         except:
            print "fail on",f
   o.close()


def iscontig(sel):
	m = cmd.get_model(sel+" and name N+CA+C").atom
	for i in range(1,len(m)):
		if ( la.Vec(m[i-1].coord) - la.Vec(m[i].coord) ).length() > 1.8:  return False
		return True

def procCdat(N=3,lfile=None,biod="/data/biounit",outd=None):
	if lfile is None: lfile=os.path.expanduser("~/Dropbox/project/sym_comp/meta/C%i.dat"%N)
	if outd  is None:  outd=os.path.expanduser(".//C%i"%N)
	print outd
	Nnobio=0; Nok=0;  Nbig=0; Nnsym=0; Nnomxatm=0; Nhomogen=0
	for fn in open(lfile).readlines():
		try:
				fn = fn.split()[0].strip()
				pdb = fn[3:7]
				bnum = int(fn[-1:])
				if os.path.exists(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb") or os.path.exists(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb.gz"):
					Nok += 1
					continue
				fname = biod+"/"+fn
				if not os.path.exists(fname): fname += ".gz"
				if not os.path.exists(fname):
					Nnobio += 1
					print "no file",fname
					continue
				cmd.delete("all")
				cmd.load(fname,'m')
				cmd.remove("resn HOH")
				cmd.remove('not alt a+""')
				#hf = cmd.select("(HET and not resn MSE+CSW)",state=1) / cmd.select("ALL",state=1)
				#if hf > 0.1: continue
				#cmd.remove("(HET and not resn MSE+CSW)")
				if cmd.select('all',state=N) != 0:
					for i in range(1,N+1):
						cmd.create("sub%i"%i,"m",i,1)
				else:
					cc = chaincount("m")
					if len(cc) < N:
						Nnsym += 1
						print "ERROR:",fname," symmetry error"
						continue
					for i in range(1,N+1):
						cmd.create("sub%i"%i,"m and chain %s"%(cc[-i][1]),1,1)
				for i in range(1,N+1):
					if iscontig("sub%i"%i):
						cmd.create("mxatm","sub%i"%i)
						break
				if cmd.select("mxatm") < 50:
					Nnomxatm += 1
					print "ERROR: mxatm < 50"
				 	continue
				if cmd.select("name CA and mxatm") > 500:
					Nbig += 1
					print "ERROR:",fname," more than 500 res"
					continue
				chains = ["sub%i"%i for i in range(1,N+1)]
				done = False
				count = 0
				while not done and count < 50:
					done = True
					random.shuffle(chains)
					for i in range(len(chains)):
						for j in range(i+1,len(chains)):
							done = done and homogenizechains(chains[i],chains[j])
					count += 1
				if count >= 50:
					Nhomogen += 1
					print "ERROR: error homogenizing"
					continue
				if cmd.select("sub1") < 50:
					Nnomxatm += 1
					print "ERROR: less than 50 atoms"
					continue
				cm = com("sub*")
				for i in range(1,N+1):
					trans("sub%i"%i,-cm)
				a = [cmd.get_model("sub%i and name CA"%i).atom for i in range(1,N+1)]
				axis = la.Vec(0,0,0)
				for i in range(len(a[0])):
					axis1 = la.Vec(0,0,0)
					for j in range(N): axis1 += la.Vec(a[j][i].coord)
					if axis1.length() > 0.0001 and axis.dot(axis1) < 0: axis1 *= -1
					axis += axis1
				axis.normalize()
				for i in range(1,N+1):
					alignaxis("sub%i"%i,la.Vec(0,0,1),axis,la.Vec(0,0,0))
				#cmd.create("final1","mxatm")
				#cmd.create("final2","mxatm")
				#cmd.create("final3","mxatm")
				#cmd.align("final1","sub1")
				#cmd.align("final2","sub2")
				#cmd.align("final3","sub3")
				#return
				if not os.path.exists(outd): os.mkdir(outd)
				cmd.align("mxatm","sub1")
				cmd.save(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb","mxatm")
				Nok += 1
				print "SUCCESS on",N,fname
		except (pymol.CmdException,Exception) as e:
			print "EXCEPTION!!!!!!",e
			print fname
			pass
  print "DONE"
	print Nok, Nbig, Nnsym, Nnobio, Nnomxatm, Nhomogen

def procD2dat(lfile=None,biod="/data/biounit",outd=None):
	N = 4
	if lfile is None: lfile=os.path.expanduser('~/Dropbox/project/sym_comp/meta/D2.dat')
	if outd  is None:  outd=os.path.expanduser("./D2")
	print outd
	Nnobio=0; Nok=0; Ncontact=0; Nbig=0; Nnsym=0; Nnomxatm=0; Nhomogen=0
	for fn in open(lfile).readlines():
	 try:
		fn = fn.strip()
		fn = fn.split()[0]
		pdb = fn[-9:-5]
		print fn,pdb
		bnum = int(fn[-1:])
		if os.path.exists(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb") or os.path.exists(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb.gz"):
			Nok += 1
			continue
		fname = biod+"/"+fn
		if not os.path.exists(fname):
		  fname += ".gz"
		if not os.path.exists(fname):
		  Nnobio += 1
			print "can't find",fname
		  continue
		#print pdb,bnum,fname
		cmd.delete("all")
		cmd.load(fname,'m')
		cmd.remove("resn HOH")
		cmd.remove('not alt a+""')
		#hf = cmd.select("(HET and not resn MSE+CSW)",state=1) / cmd.select("ALL",state=1)
		#if hf > 0.1: continue
		#cmd.remove("(HET and not resn MSE+CSW)")
		if   cmd.select('all',state=4) != 0:
			for i in range(1,N+1):
				cmd.create("sub%i"%i,"m",i,1)
		elif cmd.select('all',state=2) != 0:
			cc = chaincount('m')
			if len(cc) < 2:
				Nnsym += 1
				continue
			cmd.create("sub1","m and chain %s"%(cc[0][1]),1,1)
			cmd.create("sub2","m and chain %s"%(cc[1][1]),1,1)
			cmd.create("sub3","m and chain %s"%(cc[0][1]),2,1)
			cmd.create("sub4","m and chain %s"%(cc[1][1]),2,1)
		else:
			cc = chaincount("m")
			if len(cc) < N:
				sym = cmd.get_symmetry("m")
				if   sym[6] == "I 2 2 2":
					trans('m',la.Vec(0,-sym[1],0))
					print pdb
				#elif sym[6] == "P 21 21 2" and len(cc)==2:
				#   trans('m',la.Vec(-sym[0]/2.0,-sym[1]/2.0,0))
				#   cmd.create("sub1","m and chain %s and not (HET and not resn MSE+CSW)"%(cc[0][1]),1,1)
				#   cmd.create("sub2","m and chain %s and not (HET and not resn MSE+CSW)"%(cc[1][1]),1,1)
				#   cmd.create("sub3","m and chain %s and not (HET and not resn MSE+CSW)"%(cc[0][1]),1,1)
				#   cmd.create("sub4","m and chain %s and not (HET and not resn MSE+CSW)"%(cc[1][1]),1,1)
				#   rot("sub3",la.Vec(0,0,1),180,la.Vec(0,0,0))
				#   rot("sub4",la.Vec(0,0,1),180,la.Vec(0,0,0))
				elif sym[6] in ('C 1 2 1','P 21 21 21','P 62 2 2','P 64 2 2','P 65 2 2','P 63 2 2','P 61 2 2','C 2 2 21'):
					Nnsym += 1
					#if pid != "1y2k_2": return
					continue
				else:
					Nnsym += 1
					continue#return
				cmd.save(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb","m")
				Nok += 1
				continue
			else:
				for i in range(1,N+1):
					cmd.create("sub%i"%i,"m and chain %s"%(cc[-i][1]),1,1)
		for i in range(1,N+1):
			if iscontig("sub%i"%i):
				cmd.create("mxatm","sub%i"%i)
				break
		if cmd.select("name CA and mxatm") > 250:
			Nbig += 1
			continue
		if cmd.select("mxatm") < 50:
			Nnomxatm += 1
			continue
		chains = ["sub%i"%i for i in range(1,N+1)]
		done = False
		count = 0
		while not done and count < 50:
			done = True
			random.shuffle(chains)
			for i in range(len(chains)):
				for j in range(i+1,len(chains)):
					done = done and homogenizechains(chains[i],chains[j])
			count += 1
		if count >= 50:
			Nhomogen += 1
			continue
		if cmd.select("sub1") < 50:
			Nnomxatm += 1
			continue
		cm = com("sub*")
		for i in range(1,N+1):
			trans("sub%i"%i,-cm)
		a = [cmd.get_model("sub%i and name CA"%i).atom for i in range(1,N+1)]
		a1 = la.Vec(0,0,0)
		for i in range(len(a[0])):
			axis1 = la.Vec(a[0][i].coord) + la.Vec(a[1][i].coord)
			if axis1.length() > 0.0001 and a1.dot(axis1) < 0: axis1 *= -1
			a1 += axis1
		a1.normalize()
		for i in range(1,N+1):
			alignaxis("sub%i"%i,la.Vec(1,0,0),a1,la.Vec(0,0,0))
		a = [cmd.get_model("sub%i and name CA"%i).atom for i in range(1,N+1)]
		a1 = la.Vec(0,0,0)
		for i in range(len(a[0])):
			axis1 = la.Vec(a[0][i].coord) + la.Vec(a[2][i].coord)
			if axis1.length() > 0.0001 and a1.dot(axis1) < 0: axis1 *= -1
			a1 += axis1
		a1.normalize()
		for i in range(1,N+1):
			alignaxis("sub%i"%i,la.Vec(0,1,0),a1,la.Vec(0,0,0))
		cmd.align("mxatm","sub1")
		cmd.create("final2","mxatm")
		cmd.create("final3","mxatm")
		cmd.create("final4","mxatm")
		rot('final2',la.Vec(1,0,0),180,la.Vec(0,0,0))
		rot('final3',la.Vec(0,1,0),180,la.Vec(0,0,0))
		rot('final4',la.Vec(0,0,1),180,la.Vec(0,0,0))
		n1 = cmd.select('mxatm within 4 of final2')
		n2 = cmd.select('mxatm within 4 of final3')
		n3 = cmd.select('mxatm within 4 of final4')
		if n1 < 10 and n2 < 10 and n3 < 10:
			Ncontact += 1
			continue
		if not os.path.exists(outd): os.mkdir(outd)
		cmd.save(outd+"/"+pdb+"_"+str(bnum)+"_sub1.pdb","mxatm")
		Nok += 1
		#return
	 except:
					 print "exception!"
	print Nok, Nbig, Nnsym, Ncontact, Nnobio, Nnomxatm, Nhomogen



if __name__ == '__main__':
	# pymol environment
	moddir='/home/sheffler/pymol/modules'
	sys.path.insert(0, moddir)
	os.environ['PYMOL_PATH'] = "/home/sheffler/pymol"
 	import pymol
	pymol.pymol_argv = ['pymol','-qc'] + sys.argv[1:]
	pymol.finish_launching()
	cmd = pymol.cmd
	for i in range(2,9): procCdat(i)
