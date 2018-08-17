from qrcode import constants, exceptions, util
from qrcode.image.base import BaseImage
import six
import qrcode
from PIL import Image
import sys
import copy

def showmodules(modules):
    for n in modules:
        t=""
        for m in n:
            #t += m
            if m:
                t+="O"
            else:
                t+="."
        print(t)
                
class imgqrcode(qrcode.QRCode):
    def make_image(self, image_factory=None, **kwargs):
        """
        Make an image from the QR Code data.

        If the data has not been compiled yet, make it first.
        """
        qrcode.main._check_box_size(self.box_size)
        if self.data_cache is None:
            self.make()

        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)
        else:
            image_factory = self.image_factory
            if image_factory is None:
                # Use PIL by default
                from qrcode.image.pil import PilImage
                image_factory = PilImage

        im = image_factory(
            self.border, self.modules_count, self.box_size, **kwargs)
        #print("XXX")
        #showmodules(self.modules)
        self.adjustlevel(self.keepdata_cache)
        for r in range(self.modules_count):
            for c in range(self.modules_count):
                if self.modules[r][c]:
                    im.drawrect(r, c)
        return im

    def makeImpl(self, test, mask_pattern):
        qrcode.main._check_version(self.version)
        self.modules_count = self.version * 4 + 17
        self.modules = [None] * self.modules_count

        for row in range(self.modules_count):

            self.modules[row] = [None] * self.modules_count

            for col in range(self.modules_count):
                self.modules[row][col] = None   # (col + row) % 3

        self.setup_position_probe_pattern(0, 0)
        self.setup_position_probe_pattern(self.modules_count - 7, 0)
        self.setup_position_probe_pattern(0, self.modules_count - 7)
        self.setup_position_adjust_pattern()
        self.setup_timing_pattern()
        self.keepmodules = copy.deepcopy(self.modules)
        self.setup_type_info(test, mask_pattern)

        if self.version >= 7:
            self.setup_type_number(test)

        if self.data_cache is None:
            self.data_cache = util.create_data(
                self.version, self.error_correction, self.data_list)
        self.keepdata_cache = copy.deepcopy(self.data_cache)
        self.map_data(self.data_cache, mask_pattern)

    def adjustlevel(self, data):
        """Make from map_data"""
        inc = -1
        row = self.modules_count - 1
        bitIndex = 7
        byteIndex = 0
        self.maptest = []
        for col in range(self.modules_count):
            self.maptest.append([".",] * self.modules_count)

        #mask_func = util.mask_func(mask_pattern)

        data_len = len(data)
        boxlist=[]
        bl = [0,0,[]]
        sumvalue = 0

        #print(self.ssize)
        self.changescore=0
        for col in six.moves.xrange(self.modules_count - 1, 0, -2):

            if col <= 6:
                col -= 1

            col_range = (col, col-1)

            while True:

                for c in col_range:

                    if self.keepmodules[row][c] is None:

                        #dark = False

                        #if byteIndex < data_len:
                        #    dark = (((data[byteIndex] >> bitIndex) & 1) == 1)

                        #if mask_func(row, c):
                        #    dark = not dark

                        #if byteIndex == 130:
                        #    xp = True
                        #else:
                        #    xp = False
                        if self.modules[row][c]:
                            sumvalue += 1
                        bl[2].append((row,c,bitIndex))
                        if bitIndex == 0:
                            self.maptest[row][c] = "%d" % sumvalue
                            
                            ty = (row - self.controlwidth)/self.tonesize
                            tx = (c - self.controlwidth)/self.tonesize
                            #print(row,c,ty,tx)
                            if tx >= 0 and tx < self.ssize and ty >= 0 and ty < self.ssize:
                                bl[0] = sumvalue
                                bl[1] = self.picm.getpixel((tx,ty))
                                #print(bl)
                                boxlist.append(bl)
                                if bl[0] > bl[1]+self.allow: #change to False
                                    self.changescore += 1
                                    vcount = bl[0] - bl[1]
                                    for n in bl[2]:
                                        if self.modules[n[0]][n[1]] == True:
                                            self.modules[n[0]][n[1]] = False
                                            vcount -= 1
                                            if vcount <= 0:
                                                break
                                elif bl[0] < bl[1]-self.allow: #change to True
                                    self.changescore += 1
                                    vcount = bl[1] - bl[0]
                                    for n in bl[2]:
                                        if self.modules[n[0]][n[1]] == False:
                                            self.modules[n[0]][n[1]] = True
                                            vcount -= 1
                                            if vcount <= 0:
                                                break

                            bl = [0,0,[]]
                            sumvalue = 0
                        
                        bitIndex -= 1

                        if bitIndex == -1:
                            byteIndex += 1
                            bitIndex = 7

                row += inc

                if row < 0 or self.modules_count <= row:
                    row -= inc
                    inc = -inc
                    break
        print(len(boxlist))
        print(self.modules_count)
        print("Score: %d" % self.changescore)

    def targetimage(self,image,controlwidth=11,tonesize=2):
        self.controlwidth = controlwidth
        self.tonesize = tonesize
        self.codesize=self.modules_count
        mp=genpixmap(8)
        pic = Image.open(image)
        picb = pic.convert("L")
        #ssize = int((codesize-controlwidth*2)/self.tonesize)
        pics = picb.resize((self.ssize,self.ssize))
        self.picm = pics.point(mp)
        #self.ssize = ssize

def genpixmap(targetlevel):
    """Generate pixel value map."""
    v=256.0/(targetlevel+1)
    m=[]
    j=0
    for i in range(256):
       m.append(int(i/v))
    return m

def qrmap(qr,picm,controlwidth,pixsize):
    """Apply picm to qr"""
    samecount=0
    nearcount=0
    for y in range(picm.size[1]):
        for x in range(picm.size[0]):
            s=0
            orgy = controlwidth + y * pixsize
            for dy in range(orgy,orgy+pixsize):
                orgx = controlwidth + x * pixsize
                for dx in range(orgx,orgx+pixsize):
                    if qr.getpixel((dx,dy)) == 255:
                        s += 1
            if picm.getpixel((x,y))==s:
                samecount += 1
            else:
                changepixels = s - picm.getpixel((x,y))
                if abs(picm.getpixel((x,y))-s) == 1:
                    nearcount += 1
                orgy = controlwidth + y * pixsize
                for dy in range(orgy,orgy+pixsize):
                    orgx = controlwidth + x * pixsize
                    for dx in range(orgx,orgx+pixsize):
                        if changepixels > 0 and qr.getpixel((dx,dy)) == 255:
                            qr.putpixel((dx,dy),0)
                            changepixels -= 1
                        if changepixels < 0 and qr.getpixel((dx,dy)) == 0:
                            qr.putpixel((dx,dy),255)
                            changepixels += 1
    #qr.show()
    return samecount,nearcount,qr

def make(code,image):
    border=5
    version=15
    qr = imgqrcode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=2,
        border=5,
        mask_pattern=2)
    qr.controlwidth=25
    qr.tonesize=2
    #qr.makeImpl(False,2)
    #qr.makeImpl(False,2)
    qr.add_data(code)
    qr.modules_count = qr.version * 4 + 17
    qr.codesize=qr.modules_count
    qr.ssize = int((qr.codesize-qr.controlwidth*2)/qr.tonesize)
    qr.allow=2
    #print("QQQ",qr.codesize,qr.ssize)
    qr.targetimage(image)
    #qr.adjustlevel(qr.keepdata_cache)
    #for n in qr.modules:
    #    t=""
    #    for m in n:
    #        #t += m
    #        if m:
    #            t+="O"
    #        else:
    #            t+="."
    #    print(t)
    #            
    #for n in qr.maptest:
    #    t=""
    #    for m in n:
    #        t += m
    #        #if m:
    #        #    #t+="O"
    #        #else:
    #        #    #t+="."
    #    print(t)
                
    #qr.data_cache=copy.deepcopy(qr.keepdata_cache)
    #print(qr.data_cache)
    img = qr.make_image()
    #print(qr.keepmodules)
    #qr.targetimage(image,controlwidth=11)
    #showmodules(qr.keepmodules)
    img.show()

def xmake(code,image):
    controlwidth=11 
    pixsize=2
    border=5
    version=10
    dummyqr = imgqrcode.make(code,
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=0)
    codesize=dummyqr.size
    mp=genpixmap(pixsize)
    pic = Image.open(image)
    picb = pic.convert("L")
    ssize = int((codesize[0]-controlwidth*2)/2)
    pics = picb.resize((ssize,ssize))
    picm = pics.point(mp)

    vmax = 0
    vmaxqr=None
    for msk in range(0,1):
        qr = qrcode.make(code,
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=1,
            border=0,
            mask_pattern=msk)
        qr.show()
        v=qrmap(qr,picm,controlwidth,pixsize)
        if v[0] > vmax:
            vmax = v[0]
            vmaxqr = v[2]
    #add border
    qrb = Image.new("L",(vmaxqr.size[0]+border*2,vmaxqr.size[1]+border*2),255)
    qrb.paste(vmaxqr,(border,border))
    qrb.show()

if __name__ == '__main__':
    make(sys.argv[1],sys.argv[2])
    #qr = qrcode.make(sys.argv[1])
    #qr.show()

