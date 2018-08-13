from qrcode import constants, exceptions, util
from qrcode.image.base import BaseImage
import six
import qrcode
from PIL import Image
import sys
import copy

class imgqrcode(qrcode.QRCode):
    def makeImpl(self, test, mask_pattern):
        #qrcode._check_version(self.version)
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
        sumvalue=0

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
                        if bitIndex == 0:
                            self.maptest[row][c] = "%d" % sumvalue
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

    def targetimage(self,image,controlwidth=11):
        codesize=self.modules_count
        mp=genpixmap(8)
        pic = Image.open(image)
        picb = pic.convert("L")
        ssize = int((codesize-controlwidth*2)/2)
        pics = picb.resize((ssize,ssize))
        self.picm = pics.point(mp)

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
    version=10
    qr = imgqrcode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=0,
        mask_pattern=2)
    qr.makeImpl(False,2)
    qr.add_data(code)
    qr.targetimage(image,controlwidth=11)
    qr.adjustlevel(qr.keepdata_cache)
    for n in qr.maptest:
        t=""
        for m in n:
            t += m
            #if m:
            #    #t+="O"
            #else:
            #    #t+="."
        print(t)
                
    img = qr.make_image()
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

