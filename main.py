import qrcode
from PIL import Image
import sys
import copy

def genpixmap(pixsize):
    """Generate pixel value map."""
    v=256.0/(pixsize*pixsize+1)
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
    controlwidth=11 
    pixsize=2
    border=5
    version=10
    dummyqr = qrcode.make(code,
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

