from ThreadWeaver import WeaverThread
import os



class MosaicManager(WeaverThread):
    def __init__(self):
        super().__init__()
        self.settings = {'OCT':True,
                         'UV':False}
    
    def makedir(self):
        if not os.path.exists(self.ui.DIR.toPlainText()+'/aip'):
            os.mkdir(self.ui.DIR.toPlainText()+'/aip')
        if not os.path.exists(self.ui.DIR.toPlainText()+'/surf'):
            os.mkdir(self.ui.DIR.toPlainText()+'/surf')
        if not os.path.exists(self.ui.DIR.toPlainText()+'/fitting'):
            os.mkdir(self.ui.DIR.toPlainText()+'/fitting') 
            
    def PreMosaic(self):
        pass      