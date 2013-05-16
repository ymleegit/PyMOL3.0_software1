# -*- mode:python;tab-width:2;indent-tabs-mode:t;show-trailing-whitespace:t;rm-trailing-spaces:t -*-
import sys,os
newpath = os.path.dirname(inspect.getfile(inspect.currentframe())) # script directory
if not newpath in sys.path: sys.path.append(newpath)
from pymol_util import *
from xyzMath import *

nsymmetrizecx = 0


def showmotifs(sel=None):
	sels = [sel]
	if not sel:	sels = cmd.get_object_list()
	for sel in sels:
		cmd.hide("ev",sel)
		cmd.remove(sel+" and hydro")
		cmd.unbond(        sel + " and resn BPY", sel + " and not resn BPY")
		util.cbc()
		cmd.show("lines" , sel + " and (not name n+c+o) and (chain ~)")
		cmd.show("car"   , sel + " and not (chain ~)")
		cmd.color("white", sel + " and (chain ~)")
		cmd.zoom (         sel + " and (chain ~)")
		cmd.color("blue" , sel + " and name n")
		cmd.color("red"  , sel + " and name o" )
		cmd.show( "sti"  , sel + " and chain X+Y")
		cmd.show( "sti"  , "(("+sel+") and (name CA+CB) and (not chain ~)) within 4 of ((" +sel+") and (resn BPY))" )
		cmd.show("lines" , sel + " and chain Z" )
		cmd.dss(           sel + " and chain A+B+C+D+E+F")
		cmd.color("red"  , sel + " and chain Z")
		cmd.show( "sph"  , sel + " and chain Z and name C22+C25+C30")
		cmd.set("sphere_scale","0.3")

