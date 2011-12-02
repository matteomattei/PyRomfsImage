.. installation:

===============
Getting Started
===============

Preferred::

 sudo pip install PyRomfsImage

Alternatively::

 sudo easy_install PyRomfsImage 

.. toctree::
   :maxdepth: 2

Application structure
+++++++++++++++++++++

This is a single module library in pure Python with no dependencies.

Typical use cases
+++++++++++++++++
The following code is an example on how to use the library::

 # Python imports
 import sys
 # PyRomfsImage import
 import PyRomfsImage

 filename = sys.argv[1]
 r = PyRomfsImage.Romfs()
 r.open(filename)
 n = r.getRoot()
 for i in n.findAll():
     print(i)
 r.close()

