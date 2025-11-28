import os
from Actions import DnSAction, AODOAction, GPUAction, DAction

def run_OCT(self):
        self.PreMosaic_OCT()
        self.Mosaic_OCT()
    
    
def Makedir(self,savepath = 'self.ui.DIR'):
    self.stempath = savepath.toPlainText()
    if not os.path.exists(self.stempath + '/aip'):
        os.mkdir(self.stempath + '/aip')
    if not os.path.exists(self.stempath + '/surf'):
        os.mkdir(self.stempath + '/surf')
    if not os.path.exists(self.stempath + '/fitting'): 
        os.mkdir(self.stempath + '/fitting')
        
    
def PreMosaic_OCT(self):
        pass
    
def Mosaic_OCT(self):
        pass