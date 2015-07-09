#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 $Id: filebrowser.py 159 2008-09-29 19:42:04Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/filebrowser.py $
"""

# Python
import os

import gtk
from kiwi.ui.objectlist import ObjectTree, Column
import kiwi

class TreeNode(object):
    skip=False
    empty=False
    dummy=False
    loaded=True
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.pathname)
    
    def __init__(self, pathname, dummy=False):
        assert isinstance(pathname, basestring), pathname
        self.dummy=dummy
        self.pathname=pathname
        self.name=os.path.basename(pathname)
        if self.name.startswith('.'):
            self.skip=True
            return
        if not os.path.isdir(pathname):
            self.skip=True
            return
        
COL_MODEL=0
class Tree(ObjectTree):
    root_node=None
    def __init__(self, *args, **kwargs):
        self.TreeNode=kwargs.pop('TreeNode', TreeNode)
        ObjectTree.__init__(self, *args, **kwargs)
        self.append_path(None, '/')
        self.connect('row-expanded', self.on_expand)

        # callback for double click and enter key.
        #self.connect('row-activated', self.on_activated)
        
    def on_expand(self, tree, node):
        model=self.get_model()
        to_remove=[]
        def remove_iter(iter, remove_this=True):
            # Depth First remove children: The leaves need to
            # be removed first.
            child_iter=model.iter_children(iter)
            while child_iter:
                remove_iter(child_iter)
                child_iter=model.iter_next(child_iter)
            if remove_this:
                sub_node=model[iter][COL_MODEL]
                to_remove.append(sub_node)
        remove_iter(self._iters[id(node)], False)
        
        try:
            files=os.listdir(node.pathname)
        except OSError, exc:
            print node.pathname, exc
            files=[]
        for file in sorted(files):
            file=os.path.join(node.pathname, file)
            self.append_path(node, file)
        for node in to_remove:
            self.remove(node)
        node.loaded=True
        
    def expand_path(self, path):
        path=os.path.abspath(path)
        path_list=[]
        head=path
        while True:
            head, tail = os.path.split(head)
            if not tail:
                break
            path_list.append(tail)
        path_list.reverse()
        node=self.root_node
        for filename in path_list:
            node=self._expand_node_path(node, filename)
            self.expand(node, open_all=False)
            iter=self._iters[id(node)]
            self._treeview.get_selection().select_iter(iter)

            
    def _expand_node_path(self, node, filename):
        model=self.get_model()
        if not node.loaded:
            self.expand(node, open_all=False)
        child_iter=model.iter_children(self._iters[id(node)])
        while child_iter:
            sub_node=model[child_iter][COL_MODEL]
            if sub_node.name==filename:
                return sub_node
            child_iter=model.iter_next(child_iter)
        raise ValueError('%s not in %s' % (filename, node))
        
    def append_path(self, parent, pathname):
        assert (not parent) or isinstance(parent, self.TreeNode), parent
        assert isinstance(pathname, basestring), pathname
        node=self.TreeNode(pathname)
        if not self.parent:
            self.root_node=node
        if node.skip:
            return False
        self.append(parent, node)
        if node.empty:
            return True
        dummy=self.TreeNode(os.path.join(pathname, '...'), dummy=True)
        self.append(node, dummy)
        node.loaded=False
        return True
    
    def iter_values(self):
        return [self._model.get_value(iter, COL_MODEL) for iter in self._iters.values()]

        
if __name__=='__main__':
    window = gtk.Window()
    window.connect('delete-event', gtk.main_quit)
    tree=Tree([Column('name')])
    tree.expand_path(os.environ['HOME'])
    window.add(tree)
    window.set_size_request(400, 600)
    window.show_all()
    gtk.main()

    
